"""
Response formatter for chat API.
Formats LLM responses with citations and metadata.
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional
from backend.retrieval.context import ContextPacket
from backend.api.models import ChatResponse, SourceDocument

logger = logging.getLogger(__name__)


def extract_citations_from_text(text: str) -> List[str]:
    """
    Extract source_id citations from LLM response text.
    Looks for patterns like [Source src_000_...] or [Source src_001_...]
    
    Args:
        text: LLM response text
        
    Returns:
        List of source_ids found in text
    """
    # Pattern to match [Source src_XXX_...]
    pattern = r'\[Source\s+(src_\d+_\w+)\]'
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    # Also try without brackets
    pattern2 = r'Source\s+(src_\d+_\w+)'
    matches2 = re.findall(pattern2, text, re.IGNORECASE)
    
    # Combine and deduplicate
    all_matches = list(set(matches + matches2))
    
    return all_matches


def parse_llm_json_response(llm_text: str) -> Dict[str, Any]:
    """
    Parse LLM JSON response, extracting clean answer text.
    
    Args:
        llm_text: LLM response text (may be JSON or plain text)
        
    Returns:
        Dict with answer, citations, confidence
    """
    # First, try to find and parse complete JSON object
    # Look for JSON structure that starts with { and contains "answer"
    try:
        # Try to find JSON object boundaries more accurately
        start_idx = llm_text.find('{')
        if start_idx != -1:
            # Try to parse from the first { to the end, or find matching }
            bracket_count = 0
            end_idx = start_idx
            for i, char in enumerate(llm_text[start_idx:], start_idx):
                if char == '{':
                    bracket_count += 1
                elif char == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i + 1
                        break
            
            if end_idx > start_idx:
                json_str = llm_text[start_idx:end_idx]
                parsed = json.loads(json_str)
                answer = parsed.get("answer", "")
                # Ensure answer is a string, not None
                if not answer:
                    answer = llm_text
                return {
                    "answer": str(answer),
                    "citations": parsed.get("citations", []),
                    "confidence": parsed.get("confidence", "medium")
                }
    except (json.JSONDecodeError, ValueError, KeyError):
        pass
    
    # Try extracting just the answer field using regex (handles escaped quotes)
    # Match: "answer": "text here" (handling escaped quotes and newlines)
    answer_pattern = r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"'
    answer_match = re.search(answer_pattern, llm_text, re.DOTALL)
    if answer_match:
        answer = answer_match.group(1)
        # Unescape JSON string escapes
        answer = answer.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
        return {
            "answer": answer,
            "citations": [],
            "confidence": "medium"
        }
    
    # If no JSON found, clean up the text and use it as answer
    answer = llm_text.strip()
    
    # Remove any JSON-looking structure at the beginning or end
    # Remove leading { and anything before "answer"
    answer = re.sub(r'^.*?"answer"\s*:\s*"', '', answer, flags=re.DOTALL)
    # Remove trailing JSON structure
    answer = re.sub(r'"\s*,\s*"citations".*$', '', answer, flags=re.DOTALL)
    answer = re.sub(r'"\s*\}\s*$', '', answer, flags=re.DOTALL)
    answer = re.sub(r'^\{.*?"answer"\s*:\s*"', '', answer, flags=re.DOTALL)
    
    # Clean up any remaining quotes if they're at start/end from JSON parsing
    answer = answer.strip().strip('"').strip()
    
    return {
        "answer": answer,
        "citations": [],
        "confidence": "medium"
    }


def format_chat_response(
    llm_response: str,
    context_packet: ContextPacket,
    query: str,
    confidence: float,
    flags: List[str]
) -> ChatResponse:
    """
    Format LLM response into ChatResponse with citations.
    
    Args:
        llm_response: Raw LLM response text
        context_packet: Context packet with sources
        query: Original user query
        confidence: Confidence score (0-1)
        flags: List of warning flags
        
    Returns:
        ChatResponse object
    """
    # Parse LLM response
    parsed = parse_llm_json_response(llm_response)
    answer_text = parsed["answer"]
    
    # Remove ALL JSON artifacts - be very aggressive about cleaning
    # Remove any remaining JSON structure markers
    answer_text = re.sub(r'^\s*\{.*?"answer"\s*:\s*"', '', answer_text, flags=re.DOTALL)
    answer_text = re.sub(r'"\s*,\s*"citations".*$', '', answer_text, flags=re.DOTALL)
    answer_text = re.sub(r'"\s*\}\s*$', '', answer_text, flags=re.DOTALL)
    
    # Remove citation markers from answer text (clean paragraph format)
    # Remove patterns like [Source src_XXX_...] or [Source src_000_abc123_chunk_2]
    answer_text = re.sub(r'\[\s*Source\s+src_\d+_[^\]]+\]', '', answer_text, flags=re.IGNORECASE)
    answer_text = re.sub(r'\[Source\s+src_[^\]]+\]', '', answer_text, flags=re.IGNORECASE)
    answer_text = re.sub(r'\[Source[^\]]+\]', '', answer_text, flags=re.IGNORECASE)
    
    # Remove any remaining JSON-like artifacts
    answer_text = re.sub(r'\{[^}]*\}', '', answer_text)  # Remove any remaining { }
    answer_text = re.sub(r'"\s*:\s*"[^"]*"', '', answer_text)  # Remove key: "value" patterns
    
    # Clean up multiple spaces, normalize whitespace, and format as paragraph
    answer_text = re.sub(r'\s+', ' ', answer_text)
    answer_text = answer_text.strip()
    
    # Ensure it starts with a capital letter and ends with proper punctuation
    if answer_text and not answer_text[0].isupper():
        answer_text = answer_text[0].upper() + answer_text[1:] if len(answer_text) > 1 else answer_text.upper()
    if answer_text and answer_text[-1] not in '.!?':
        answer_text = answer_text + '.'
    
    # Extract citations from original parsed answer (before cleanup)
    cited_source_ids = extract_citations_from_text(parsed["answer"])
    
    # Build sources list - ALWAYS include top 3 closest matches from context packet
    sources = []
    source_map = {src.source_id: src for src in context_packet.sources}
    used_source_ids = set()
    
    # Sort all sources by score (highest first) to get top matches
    sorted_sources = sorted(context_packet.sources, key=lambda x: x.score, reverse=True)
    
    # First, include any explicitly cited sources (if they're in the top results)
    for source_id in cited_source_ids:
        if source_id in source_map and source_id not in used_source_ids:
            source = source_map[source_id]
            sources.append(SourceDocument(
                text=source.text[:500] + "..." if len(source.text) > 500 else source.text,
                metadata={
                    "source_id": source.source_id,
                    "chunk_id": source.chunk_id,
                    "title": source.title,
                    "statute_number": source.statute_number,
                    "case_citation": source.case_citation,
                    "hierarchy_path": source.hierarchy_path,
                    "doc_type": source.doc_type,
                    "jurisdiction": source.jurisdiction,
                    "source_uri": source.source_uri,
                    "score": source.score
                },
                score=source.score
            ))
            used_source_ids.add(source_id)
    
    # ALWAYS add top 3 closest matches (by score), avoiding duplicates
    # Take up to 3 sources total, prioritizing cited ones but ensuring we have top 3 by score
    num_needed = max(3 - len(sources), 0)  # How many more we need to reach 3
    
    for source in sorted_sources:
        if len(sources) >= 3:
            break
        if source.source_id not in used_source_ids:
            sources.append(SourceDocument(
                text=source.text[:500] + "..." if len(source.text) > 500 else source.text,
                metadata={
                    "source_id": source.source_id,
                    "chunk_id": source.chunk_id,
                    "title": source.title,
                    "statute_number": source.statute_number,
                    "case_citation": source.case_citation,
                    "hierarchy_path": source.hierarchy_path,
                    "doc_type": source.doc_type,
                    "jurisdiction": source.jurisdiction,
                    "source_uri": source.source_uri,
                    "score": source.score
                },
                score=source.score
            ))
            used_source_ids.add(source.source_id)
    
    # Sort final sources list by score (highest first) for consistent display
    sources.sort(key=lambda x: x.score, reverse=True)
    
    # Add disclaimer to answer
    disclaimer = "\n\n⚠️ DISCLAIMER: This information is for informational purposes only and does not constitute legal advice."
    
    # Check if use-of-force caution flag exists
    if "USE_OF_FORCE_CAUTION" in flags:
        disclaimer += "\n\n🚨 USE OF FORCE CAUTION: This response involves use-of-force matters. Verify information with official department policies and legal counsel before taking action."
    
    answer_text = answer_text + disclaimer
    
    return ChatResponse(
        response=answer_text,
        sources=sources,
        confidence=confidence,
        flags=flags,
        conversation_id="default"  # TODO: implement conversation management
    )
