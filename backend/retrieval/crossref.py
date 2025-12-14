"""
Cross-reference detection and resolution.
Detects "see also § ..." patterns and resolves referenced statute chunks.
"""

import re
import logging
from typing import List, Set, Optional
from backend.api.models import Chunk
from backend.retrieval.vector_store import VectorStore, get_vector_store

logger = logging.getLogger(__name__)


# Cross-reference patterns
CROSSREF_PATTERNS = [
    r'see also\s+§\s*(\d+\.\d+(?:\([0-9a-zA-Z]+\))*)',  # "see also § 940.01"
    r'see\s+§\s*(\d+\.\d+(?:\([0-9a-zA-Z]+\))*)',  # "see § 940.01"
    r'refer to\s+§\s*(\d+\.\d+(?:\([0-9a-zA-Z]+\))*)',  # "refer to § 940.01"
    r'under\s+§\s*(\d+\.\d+(?:\([0-9a-zA-Z]+\))*)',  # "under § 940.01"
    r'pursuant to\s+§\s*(\d+\.\d+(?:\([0-9a-zA-Z]+\))*)',  # "pursuant to § 940.01"
    r'§\s*(\d+\.\d+(?:\([0-9a-zA-Z]+\))*)\s+(?:and|,)\s+§',  # "§ 940.01 and § 940.02"
]

# Pattern to match any statute reference (for broader detection)
STATUTE_REF_PATTERN = r'§\s*(\d+\.\d+(?:\([0-9a-zA-Z]+\))*)'


def detect_crossrefs(chunk: Chunk) -> List[str]:
    """
    Detect cross-references to statutes in chunk text.
    
    Args:
        chunk: Chunk to analyze
        
    Returns:
        List of statute numbers referenced (e.g., ["940.01", "940.02"])
    """
    text = chunk.text
    statute_refs = set()
    
    # Use cross-reference patterns first (more specific)
    for pattern in CROSSREF_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        statute_refs.update(matches)
    
    # Also look for any statute references in the text
    # (but exclude the chunk's own statute number if present)
    all_statute_matches = re.findall(STATUTE_REF_PATTERN, text)
    for stat_num in all_statute_matches:
        # Skip if this is the chunk's own statute number
        if chunk.statute_number and stat_num in chunk.statute_number:
            continue
        statute_refs.add(stat_num)
    
    return sorted(list(statute_refs))


def resolve_crossref(
    statute_number: str,
    vector_store: Optional[VectorStore] = None,
    exclude_chunk_ids: Optional[Set[str]] = None
) -> Optional[Chunk]:
    """
    Resolve a cross-reference by finding the referenced statute chunk.
    
    Args:
        statute_number: Statute number to resolve (e.g., "940.01")
        vector_store: Vector store instance (uses global if not provided)
        exclude_chunk_ids: Set of chunk IDs to exclude (e.g., the original chunk)
        
    Returns:
        Chunk object if found, None otherwise
    """
    if vector_store is None:
        vector_store = get_vector_store()
    
    if exclude_chunk_ids is None:
        exclude_chunk_ids = set()
    
    try:
        # Query vector store for chunks with exact statute_number match
        # We'll use a query with filter on statute_number
        # Note: ChromaDB filter requires exact match, so we need to handle partial matches
        
        # Try exact match first
        results = vector_store.semantic_query(
            query_text=f"statute {statute_number}",
            filters={"statute_number": statute_number},
            top_k=1
        )
        
        if results:
            chunk = results[0].chunk
            if chunk.chunk_id not in exclude_chunk_ids:
                return chunk
        
        # If exact match fails, try partial match (statute_number contains the reference)
        # Get all chunks and filter manually
        all_chunks = vector_store.get_all_chunks()
        for chunk in all_chunks:
            if chunk.chunk_id in exclude_chunk_ids:
                continue
            
            if chunk.statute_number:
                # Check if statute_number matches (could be partial like "940.01(3)" contains "940.01")
                if statute_number in chunk.statute_number or chunk.statute_number in statute_number:
                    # Prefer exact match
                    if chunk.statute_number == statute_number:
                        return chunk
        
        # Return first partial match if no exact match found
        for chunk in all_chunks:
            if chunk.chunk_id in exclude_chunk_ids:
                continue
            if chunk.statute_number and statute_number in chunk.statute_number:
                return chunk
        
        logger.debug(f"Could not resolve cross-reference to statute {statute_number}")
        return None
        
    except Exception as e:
        logger.error(f"Error resolving cross-reference to {statute_number}: {e}")
        return None


def expand_crossrefs(
    chunks: List[Chunk],
    max_refs: int = 5,
    max_depth: int = 1,
    vector_store: Optional[VectorStore] = None
) -> List[Chunk]:
    """
    Expand cross-references for a list of chunks.
    
    Args:
        chunks: List of initial chunks
        max_refs: Maximum number of cross-references to resolve
        max_depth: Maximum depth of cross-reference resolution (only depth 1 supported)
        vector_store: Vector store instance (uses global if not provided)
        
    Returns:
        List of chunks with cross-references resolved (original chunks + referenced chunks)
    """
    if vector_store is None:
        vector_store = get_vector_store()
    
    # Track original chunk IDs to avoid duplicates
    seen_chunk_ids: Set[str] = {chunk.chunk_id for chunk in chunks}
    
    # Collect all cross-references from initial chunks
    all_refs: Set[str] = set()
    for chunk in chunks:
        refs = detect_crossrefs(chunk)
        all_refs.update(refs)
    
    # Resolve cross-references (max_refs limit)
    resolved_chunks: List[Chunk] = []
    resolved_count = 0
    
    for stat_num in sorted(list(all_refs)):
        if resolved_count >= max_refs:
            break
        
        resolved_chunk = resolve_crossref(
            stat_num,
            vector_store=vector_store,
            exclude_chunk_ids=seen_chunk_ids
        )
        
        if resolved_chunk and resolved_chunk.chunk_id not in seen_chunk_ids:
            resolved_chunks.append(resolved_chunk)
            seen_chunk_ids.add(resolved_chunk.chunk_id)
            resolved_count += 1
    
    # Return original chunks + resolved cross-references
    return chunks + resolved_chunks
