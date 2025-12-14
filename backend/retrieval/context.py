"""
Context window management: builds context packets from ranked chunks
with budget constraints and diversity enforcement.
"""

import logging
from typing import List, Dict, Set, Optional
from backend.retrieval.vector_store import ScoredChunk
from backend.retrieval.crossref import expand_crossrefs
from backend.api.models import Chunk, ContextSource
from backend.ingestion.chunking import estimate_tokens

logger = logging.getLogger(__name__)


class ContextPacket:
    """
    Context packet containing ordered sources for LLM generation.
    Provides stable source_ids for citations.
    """
    
    def __init__(self):
        self.sources: List[ContextSource] = []  # List of ContextSource objects
        self.chunk_map: Dict[str, Chunk] = {}  # source_id -> Chunk
        self.total_tokens: int = 0
        self.source_counter: int = 0  # For generating stable source IDs
    
    def add_chunk(self, chunk: Chunk, score: float, source_type: str = "primary") -> str:
        """
        Add a chunk to the context packet.
        
        Args:
            chunk: Chunk to add
            score: Relevance score
            source_type: Type of source ("primary", "crossref", etc.)
            
        Returns:
            Stable source_id for this chunk
        """
        # Generate stable source_id based on chunk_id
        # Use chunk_id as base to ensure stability
        source_id = f"src_{self.source_counter:03d}_{chunk.chunk_id[:20]}"
        self.source_counter += 1
        
        # Calculate token count for this chunk
        chunk_tokens = estimate_tokens(chunk.text)
        
        # Create ContextSource object
        source = ContextSource(
            source_id=source_id,
            chunk_id=chunk.chunk_id,
            text=chunk.text,
            title=chunk.title,
            statute_number=chunk.statute_number,
            case_citation=chunk.case_citation,
            hierarchy_path=chunk.hierarchy_path,
            doc_type=chunk.doc_type,
            jurisdiction=chunk.jurisdiction,
            source_uri=chunk.source_uri,
            score=score,
            source_type=source_type,
            tokens=chunk_tokens
        )
        
        self.sources.append(source)
        self.chunk_map[source_id] = chunk
        self.total_tokens += chunk_tokens
        
        return source_id
    
    def get_context_text(self) -> str:
        """Get concatenated context text from all sources."""
        context_parts = []
        for source in self.sources:
            context_parts.append(f"[Source {source.source_id}]\n{source.text}")
        return "\n\n".join(context_parts)
    
    def get_sources_summary(self) -> List[Dict]:
        """Get summary of sources for citations."""
        return [
            {
                "source_id": src.source_id,
                "title": src.title,
                "statute_number": src.statute_number,
                "case_citation": src.case_citation,
                "source_uri": src.source_uri,
                "score": src.score
            }
            for src in self.sources
        ]
    
    def to_pydantic(self):
        """Convert to Pydantic model for API responses."""
        from backend.api.models import ContextPacket as ContextPacketModel
        return ContextPacketModel(
            sources=self.sources,
            total_tokens=self.total_tokens
        )


def build_context(
    ranked_chunks: List[ScoredChunk],
    max_chunks: Optional[int] = None,
    max_tokens: Optional[int] = None,
    expand_crossrefs_flag: bool = True,
    max_crossrefs: int = 5,
    enforce_diversity: bool = True
) -> ContextPacket:
    """
    Build context packet from ranked chunks with budget and diversity constraints.
    
    Args:
        ranked_chunks: List of ScoredChunk objects sorted by relevance
        max_chunks: Maximum number of chunks to include (None = no limit)
        max_tokens: Maximum token budget (None = no limit)
        expand_crossrefs_flag: Whether to expand cross-references
        max_crossrefs: Maximum number of cross-references to resolve
        enforce_diversity: Whether to enforce diversity across doc_types
        
    Returns:
        ContextPacket with ordered sources and stable source_ids
    """
    packet = ContextPacket()
    
    if not ranked_chunks:
        return packet
    
    # Extract chunks from ScoredChunks
    chunks_with_scores = [(sc.chunk, sc.score) for sc in ranked_chunks]
    
    # Apply diversity constraint if enabled
    if enforce_diversity:
        chunks_with_scores = _ensure_diversity(chunks_with_scores)
    
    # Expand cross-references if enabled
    if expand_crossrefs_flag:
        primary_chunks = [chunk for chunk, _ in chunks_with_scores]
        expanded_chunks = expand_crossrefs(primary_chunks, max_refs=max_crossrefs)
        
        # Map expanded chunks back to scores (use original chunk's score or 0.5 for crossrefs)
        expanded_with_scores = []
        expanded_chunk_ids = {chunk.chunk_id for chunk in expanded_chunks}
        primary_chunk_ids = {chunk.chunk_id for chunk in primary_chunks}
        
        for chunk in expanded_chunks:
            if chunk.chunk_id in primary_chunk_ids:
                # Find original score
                score = next(score for c, score in chunks_with_scores if c.chunk_id == chunk.chunk_id)
                expanded_with_scores.append((chunk, score))
            else:
                # Cross-reference chunk, use lower score
                expanded_with_scores.append((chunk, 0.5))
        
        chunks_with_scores = expanded_with_scores
    
    # Apply budget constraints
    selected_chunks = []
    token_count = 0
    
    for chunk, score in chunks_with_scores:
        chunk_tokens = estimate_tokens(chunk.text)
        
        # Check max_chunks constraint
        if max_chunks is not None and len(selected_chunks) >= max_chunks:
            break
        
        # Check max_tokens constraint
        if max_tokens is not None and (token_count + chunk_tokens) > max_tokens:
            # Try to fit at least one chunk even if slightly over budget
            if len(selected_chunks) == 0:
                selected_chunks.append((chunk, score))
                token_count += chunk_tokens
            break
        
        selected_chunks.append((chunk, score))
        token_count += chunk_tokens
    
    # Add chunks to packet
    for chunk, score in selected_chunks:
        # Determine source type
        source_type = "primary"
        if expand_crossrefs_flag and chunk.chunk_id not in primary_chunk_ids:
            source_type = "crossref"
        
        packet.add_chunk(chunk, score, source_type=source_type)
    
    logger.info(
        f"Built context packet: {len(packet.sources)} sources, "
        f"{packet.total_tokens} tokens, "
        f"doc_types: {set(src.doc_type for src in packet.sources)}"
    )
    
    return packet


def _ensure_diversity(chunks_with_scores: List[tuple]) -> List[tuple]:
    """
    Ensure diversity across document types (statute, case_law, policy, training).
    
    Args:
        chunks_with_scores: List of (chunk, score) tuples
        
    Returns:
        Reordered list with diversity enforced
    """
    if not chunks_with_scores:
        return chunks_with_scores
    
    # Group by doc_type
    by_type: Dict[str, List[tuple]] = {
        "statute": [],
        "case_law": [],
        "policy": [],
        "training": []
    }
    
    for chunk, score in chunks_with_scores:
        doc_type = chunk.doc_type
        if doc_type in by_type:
            by_type[doc_type].append((chunk, score))
        else:
            # Unknown type, add to first available or create misc category
            if "misc" not in by_type:
                by_type["misc"] = []
            by_type["misc"].append((chunk, score))
    
    # Interleave chunks from different types
    # Take top 2 from each type, then continue with remaining chunks
    diverse_chunks = []
    max_per_type = 2
    
    for doc_type in ["statute", "case_law", "policy", "training"]:
        if doc_type in by_type:
            diverse_chunks.extend(by_type[doc_type][:max_per_type])
    
    # Add remaining chunks (maintain original order within type)
    seen_chunk_ids = {chunk.chunk_id for chunk, _ in diverse_chunks}
    for chunk, score in chunks_with_scores:
        if chunk.chunk_id not in seen_chunk_ids:
            diverse_chunks.append((chunk, score))
            seen_chunk_ids.add(chunk.chunk_id)
    
    return diverse_chunks

