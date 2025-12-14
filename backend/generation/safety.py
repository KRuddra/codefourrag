"""
Safety and accuracy features: confidence scoring, flags, and disclaimers.
"""

import logging
from typing import List, Dict, Any
from backend.retrieval.context import ContextPacket
from backend.retrieval.vector_store import ScoredChunk

logger = logging.getLogger(__name__)

# Flag constants
LOW_CONFIDENCE = "LOW_CONFIDENCE"
OUTDATED_POSSIBLE = "OUTDATED_POSSIBLE"
JURISDICTION_NOTE = "JURISDICTION_NOTE"
USE_OF_FORCE_CAUTION = "USE_OF_FORCE_CAUTION"


# Use-of-force keywords
USE_OF_FORCE_KEYWORDS = [
    "use of force", "force", "deadly force", "lethal force",
    "shooting", "taser", "taser", "restraint", "chokehold",
    "neck restraint", "handcuff", "take down", "take-down",
    "self-defense", "defense", "threat", "imminent threat",
    "reasonable force", "excessive force", "force policy"
]


def detect_use_of_force(query: str) -> bool:
    """
    Detect if query involves use-of-force matters.
    
    Args:
        query: User query string
        
    Returns:
        True if use-of-force keywords detected
    """
    query_lower = query.lower()
    
    for keyword in USE_OF_FORCE_KEYWORDS:
        if keyword in query_lower:
            return True
    
    return False


def check_source_currency(context_packet: ContextPacket) -> bool:
    """
    Check if sources might be outdated.
    
    Args:
        context_packet: Context packet with sources
        
    Returns:
        True if sources might be outdated
    """
    from datetime import datetime
    
    current_year = datetime.now().year
    
    for source in context_packet.sources:
        # ContextSource doesn't have date field directly - skip date checking for now
        # Date information would need to be added to ContextSource model if needed
        # For now, we'll skip outdated source detection based on date
        
        # Check is_current flag if available (though ContextSource doesn't have this either)
        # This is a placeholder for future enhancement
        pass
    
    return False


def check_jurisdiction_mismatch(query: str, context_packet: ContextPacket) -> bool:
    """
    Check if query implies WI jurisdiction but sources are federal.
    
    Args:
        query: User query
        context_packet: Context packet with sources
        
    Returns:
        True if jurisdiction mismatch detected
    """
    query_lower = query.lower()
    
    # Check if query mentions Wisconsin
    wi_indicators = ["wisconsin", "wi", "wis. stat", "state statute"]
    query_mentions_wi = any(indicator in query_lower for indicator in wi_indicators)
    
    if not query_mentions_wi:
        return False
    
    # Check if sources are federal
    for source in context_packet.sources:
        if source.jurisdiction and source.jurisdiction.upper() == "US":
            return True
    
    return False


def compute_confidence(
    retrieval_signals: Dict[str, Any],
    citations: List[str],
    context_packet: ContextPacket
) -> float:
    """
    Compute confidence score based on retrieval signals and citations.
    
    Args:
        retrieval_signals: Dict with signals like:
            - exact_match: bool (exact statute/case match)
            - top_score: float (highest retrieval score)
            - num_sources: int (number of sources)
            - score_variance: float (variance in scores)
        citations: List of source_ids cited in response
        context_packet: Context packet with sources
        
    Returns:
        Confidence score (0.0 to 1.0)
    """
    confidence = 0.4  # Lower base confidence to allow more variation
    
    # Exact match boost (strongest signal)
    if retrieval_signals.get("exact_match", False):
        confidence += 0.35
        logger.info(f"Confidence boost: exact match (+0.35)")
    
    # Top score boost (more granular based on actual score)
    top_score = retrieval_signals.get("top_score", 0.0)
    if top_score > 0.9:
        confidence += 0.25
        logger.info(f"Confidence boost: very high top score {top_score:.2f} (+0.25)")
    elif top_score > 0.8:
        confidence += 0.2
        logger.info(f"Confidence boost: high top score {top_score:.2f} (+0.2)")
    elif top_score > 0.7:
        confidence += 0.15
        logger.info(f"Confidence boost: good top score {top_score:.2f} (+0.15)")
    elif top_score > 0.6:
        confidence += 0.1
        logger.info(f"Confidence boost: moderate top score {top_score:.2f} (+0.1)")
    elif top_score > 0.5:
        confidence += 0.05
        logger.info(f"Confidence boost: low top score {top_score:.2f} (+0.05)")
    elif top_score < 0.3:
        confidence -= 0.25
        logger.info(f"Confidence penalty: very low top score {top_score:.2f} (-0.25)")
    elif top_score < 0.4:
        confidence -= 0.15
        logger.info(f"Confidence penalty: low top score {top_score:.2f} (-0.15)")
    
    # Multiple sources boost (stronger signal)
    num_sources = retrieval_signals.get("num_sources", 0)
    if num_sources >= 5:
        confidence += 0.15
        logger.info(f"Confidence boost: many sources {num_sources} (+0.15)")
    elif num_sources >= 3:
        confidence += 0.1
        logger.info(f"Confidence boost: multiple sources {num_sources} (+0.1)")
    elif num_sources >= 2:
        confidence += 0.05
        logger.info(f"Confidence boost: some sources {num_sources} (+0.05)")
    elif num_sources == 0:
        confidence = 0.1  # Very low if no sources
        logger.info(f"Confidence penalty: no sources (set to 0.1)")
    
    # Citation quality boost (stronger signal)
    if len(citations) >= 3:
        confidence += 0.1
        logger.info(f"Confidence boost: many citations {len(citations)} (+0.1)")
    elif len(citations) >= 2:
        confidence += 0.05
        logger.info(f"Confidence boost: some citations {len(citations)} (+0.05)")
    elif len(citations) == 1:
        confidence += 0.02
        logger.info(f"Confidence boost: one citation (+0.02)")
    
    # Low score variance (consistent sources) boost
    score_variance = retrieval_signals.get("score_variance", 1.0)
    if score_variance < 0.05:  # Very consistent scores
        confidence += 0.08
        logger.info(f"Confidence boost: very consistent scores variance {score_variance:.3f} (+0.08)")
    elif score_variance < 0.1:
        confidence += 0.05
        logger.info(f"Confidence boost: consistent scores variance {score_variance:.3f} (+0.05)")
    elif score_variance > 0.5:  # Inconsistent scores
        confidence -= 0.1
        logger.info(f"Confidence penalty: inconsistent scores variance {score_variance:.3f} (-0.1)")
    
    # Clamp to [0.0, 1.0]
    confidence = max(0.0, min(1.0, confidence))
    
    logger.info(f"Final confidence: {confidence:.3f} (exact_match={retrieval_signals.get('exact_match')}, top_score={top_score:.3f}, num_sources={num_sources}, citations={len(citations)}, variance={score_variance:.3f})")
    
    return confidence


def generate_flags(
    query: str,
    context_packet: ContextPacket,
    confidence: float,
    retrieval_signals: Dict[str, Any]
) -> List[str]:
    """
    Generate safety and accuracy flags.
    
    Args:
        query: User query
        context_packet: Context packet with sources
        confidence: Confidence score
        retrieval_signals: Retrieval signals
        
    Returns:
        List of flag strings
    """
    flags = []
    
    # Low confidence flag
    if confidence < 0.5:
        flags.append(LOW_CONFIDENCE)
        logger.debug("Flag: LOW_CONFIDENCE")
    
    # Outdated sources flag
    if check_source_currency(context_packet):
        flags.append(OUTDATED_POSSIBLE)
        logger.debug("Flag: OUTDATED_POSSIBLE")
    
    # Jurisdiction mismatch flag
    if check_jurisdiction_mismatch(query, context_packet):
        flags.append(JURISDICTION_NOTE)
        logger.debug("Flag: JURISDICTION_NOTE")
    
    # Use-of-force caution
    if detect_use_of_force(query):
        flags.append(USE_OF_FORCE_CAUTION)
        logger.debug("Flag: USE_OF_FORCE_CAUTION")
        
        # For use-of-force, require explicit supporting policy/statute
        has_policy_or_statute = False
        for source in context_packet.sources:
            statute_number = None
            doc_type = None
            
            if hasattr(source, 'statute_number'):
                statute_number = source.statute_number
            elif hasattr(source, 'metadata') and isinstance(source.metadata, dict):
                statute_number = source.metadata.get('statute_number')
            
            if hasattr(source, 'doc_type'):
                doc_type = source.doc_type
            elif hasattr(source, 'metadata') and isinstance(source.metadata, dict):
                doc_type = source.metadata.get('doc_type')
            
            if statute_number or (doc_type == "policy"):
                has_policy_or_statute = True
                break
        
        if not has_policy_or_statute:
            # This will trigger special handling in response generation
            flags.append("USE_OF_FORCE_INSUFFICIENT")
    
    return flags


def should_allow_use_of_force_response(
    query: str,
    context_packet: ContextPacket
) -> bool:
    """
    Check if use-of-force query has sufficient supporting sources.
    
    Args:
        query: User query
        context_packet: Context packet with sources
        
    Returns:
        True if sufficient sources exist, False otherwise
    """
    if not detect_use_of_force(query):
        return True  # Not a use-of-force query
    
    # Require explicit policy or statute
    for source in context_packet.sources:
        if source.statute_number or source.doc_type == "policy":
            return True
    
    return False
