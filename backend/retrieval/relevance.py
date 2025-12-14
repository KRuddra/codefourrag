"""
Relevance scoring and boosting logic for hybrid search results.
Applies jurisdiction, date, and department-specific boosts/penalties.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def apply_relevance_boosts(
    chunk: Any,
    base_score: float,
    filters: Optional[Dict[str, Any]] = None
) -> tuple[float, list[str]]:
    """
    Apply relevance boosts and penalties to a chunk's score.
    
    Boosting rules:
    - Prefer WI jurisdiction (+0.05 boost)
    - Prefer is_current=true or newest date (+0.03 boost)
    - Prefer department policy when doc_type=policy and department filter matches (+0.05 boost)
    
    Penalties:
    - Non-WI jurisdiction (-0.03 penalty)
    - Outdated documents (is_current=false and old date) (-0.05 penalty)
    
    Args:
        chunk: Chunk object with metadata (has attributes like .jurisdiction, .doc_type, etc.)
        base_score: Base relevance score from hybrid search
        filters: Optional filters that were applied (e.g., {"department": "madison"})
        
    Returns:
        Tuple of (adjusted_score, reasons) where reasons is a list of boost/penalty explanations
    """
    score = base_score
    reasons = []
    
    # Helper to get attribute from chunk (handles both object attributes and dict access)
    def get_chunk_attr(attr_name: str, default=None):
        if hasattr(chunk, attr_name):
            return getattr(chunk, attr_name)
        elif isinstance(chunk, dict):
            return chunk.get(attr_name, default)
        return default
    
    # Jurisdiction boost/penalty
    jurisdiction = get_chunk_attr('jurisdiction')
    if jurisdiction:
        if str(jurisdiction).upper() == 'WI':
            score += 0.05
            reasons.append("WI jurisdiction boost (+0.05)")
        else:
            score -= 0.03
            reasons.append("Non-WI jurisdiction penalty (-0.03)")
    
    # Date/currency boost
    is_current = get_chunk_attr('is_current')
    date_str = get_chunk_attr('date')
    
    if is_current:
        if str(is_current).lower() in ['true', 'yes', '1']:
            score += 0.03
            reasons.append("Current document boost (+0.03)")
        else:
            score -= 0.05
            reasons.append("Outdated document penalty (-0.05)")
    elif date_str:
        # Try to parse date and boost recent documents
        try:
            # Handle various date formats
            if isinstance(date_str, str):
                # Try parsing year only
                if len(date_str) == 4 and date_str.isdigit():
                    year = int(date_str)
                    current_year = datetime.now().year
                    if year >= current_year - 2:
                        score += 0.02
                        reasons.append(f"Recent date ({date_str}) boost (+0.02)")
                    elif year < current_year - 10:
                        score -= 0.03
                        reasons.append(f"Old date ({date_str}) penalty (-0.03)")
        except (ValueError, TypeError):
            pass  # Skip if date parsing fails
    
    # Department policy boost
    if filters:
        doc_type = get_chunk_attr('doc_type')
        department_filter = filters.get('department')
        
        if doc_type == 'policy' and department_filter:
            chunk_department = get_chunk_attr('department')
            if chunk_department:
                # Case-insensitive comparison
                if str(chunk_department).lower() == str(department_filter).lower():
                    score += 0.05
                    reasons.append(f"Department policy match ({department_filter}) boost (+0.05)")
    
    # Ensure score doesn't go negative
    score = max(0.0, score)
    
    return score, reasons
