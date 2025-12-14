"""
Query enhancement: abbreviations, synonyms, and light spell correction.
Enhances queries for better retrieval without corrupting statute numbers.
"""

import re
import logging
from typing import List, Dict, Set
from backend.utils.abbreviations import expand_abbreviation, get_abbreviations
from backend.utils.legal_terms import get_synonyms, is_legal_term, correct_spelling

logger = logging.getLogger(__name__)


class EnhancedQuery:
    """
    Enhanced query with original and variants.
    """
    
    def __init__(self, original: str, variants: List[str] = None):
        self.original = original
        self.variants = variants or []
        self.enhancement_log: List[str] = []
    
    def add_variant(self, variant: str, reason: str):
        """Add a query variant with reason."""
        if variant and variant not in self.variants and variant != self.original:
            self.variants.append(variant)
            self.enhancement_log.append(f"Added variant: '{variant}' ({reason})")
    
    def get_all_queries(self) -> List[str]:
        """Get all queries: original + variants."""
        return [self.original] + self.variants


def protect_statute_numbers(query: str) -> tuple[str, Dict[int, str]]:
    """
    Extract and protect statute numbers from query to avoid corruption.
    
    Args:
        query: Original query string
        
    Returns:
        Tuple of (query_with_placeholders, placeholder_map)
    """
    # Pattern to match statute numbers: § 939.50(3)(a), Section 940.01, etc.
    statute_pattern = r'(?:§\s*|Section\s+|Sec\.\s+|section\s+|Wis\.?\s*Stat\.?\s*)(\d+\.\d+(?:\([0-9a-zA-Z]+\))*)'
    
    placeholder_map = {}
    protected_query = query
    placeholder_counter = 0
    
    # Find all statute numbers and replace with placeholders
    for match in re.finditer(statute_pattern, query, re.IGNORECASE):
        statute_num = match.group(0)  # Full match including § symbol
        placeholder = f"__STATUTE_{placeholder_counter}__"
        placeholder_map[placeholder_counter] = statute_num
        protected_query = protected_query.replace(statute_num, placeholder, 1)
        placeholder_counter += 1
    
    return protected_query, placeholder_map


def restore_statute_numbers(query: str, placeholder_map: Dict[int, str]) -> str:
    """
    Restore statute numbers from placeholders.
    
    Args:
        query: Query with placeholders
        placeholder_map: Map of placeholder index to statute number
        
    Returns:
        Query with statute numbers restored
    """
    restored = query
    for idx, statute_num in placeholder_map.items():
        placeholder = f"__STATUTE_{idx}__"
        restored = restored.replace(placeholder, statute_num)
    return restored


def enhance_query(query: str) -> EnhancedQuery:
    """
    Enhance query with abbreviations, synonyms, and light spell correction.
    
    Steps:
    1. Protect statute numbers from corruption
    2. Expand abbreviations (OWI -> operating while intoxicated)
    3. Add synonyms (Terry stop -> investigatory detention)
    4. Light spell correction for legal terms
    5. Restore statute numbers
    
    Args:
        query: Original query string
        
    Returns:
        EnhancedQuery object with original and variants
    """
    enhanced = EnhancedQuery(query)
    
    if not query or not query.strip():
        return enhanced
    
    # Step 1: Protect statute numbers
    protected_query, placeholder_map = protect_statute_numbers(query)
    
    # Step 2: Check for multi-word abbreviations first (e.g., "terry stop")
    abbreviation_found = False
    protected_lower = protected_query.lower()
    
    # Check for multi-word abbreviations (case-insensitive)
    # Import ABBREVIATIONS directly
    from backend.utils.abbreviations import ABBREVIATIONS
    for abbrev, expansions in ABBREVIATIONS.items():
        if len(abbrev.split()) > 1:  # Multi-word abbreviation
            if abbrev.lower() in protected_lower:
                abbreviation_found = True
                variant = protected_lower
                variant = variant.replace(abbrev.lower(), expansions[0] if expansions else abbrev)
                enhanced.add_variant(restore_statute_numbers(variant, placeholder_map), f"expanded abbreviation: {abbrev}")
    
    # Step 3: Split query into words/tokens
    # Tokenize by whitespace and punctuation, but keep words together
    words = re.findall(r'\b\w+\b', protected_lower)
    
    # Step 4: Expand single-word abbreviations and add variants
    expanded_words = []
    
    for word in words:
        expansions = expand_abbreviation(word)
        if expansions and word in protected_lower:
            abbreviation_found = True
            # Create variant with abbreviation expanded
            variant = protected_lower
            # Replace abbreviation with first expansion
            variant = re.sub(r'\b' + re.escape(word) + r'\b', expansions[0], variant, flags=re.IGNORECASE)
            enhanced.add_variant(restore_statute_numbers(variant, placeholder_map), f"expanded abbreviation: {word}")
            expanded_words.extend(expansions)
        else:
            expanded_words.append(word)
    
    # Step 5: Add synonym variants
    synonym_variants = []
    for word in words:
        synonyms = get_synonyms(word)
        if synonyms:
            for synonym in synonyms[:2]:  # Limit to 2 synonyms per term
                variant = protected_query.lower()
                # Replace word with synonym (case-insensitive)
                variant = re.sub(r'\b' + re.escape(word) + r'\b', synonym, variant, flags=re.IGNORECASE)
                synonym_variants.append(variant)
    
    # Add synonym variants
    for variant in synonym_variants[:2]:  # Limit total synonym variants
        enhanced.add_variant(restore_statute_numbers(variant, placeholder_map), "added synonym")
    
    # Step 6: Light spell correction (only for known legal terms)
    corrected_words = []
    for word in words:
        if is_legal_term(word):
            corrected = correct_spelling(word)
            if corrected != word:
                corrected_words.append((word, corrected))
    
    if corrected_words:
        variant = protected_query.lower()
        for original, corrected in corrected_words:
            variant = re.sub(r'\b' + re.escape(original) + r'\b', corrected, variant, flags=re.IGNORECASE)
        enhanced.add_variant(restore_statute_numbers(variant, placeholder_map), "corrected spelling")
    
    # Step 7: Create combined variant (abbreviation + synonym expansion)
    if abbreviation_found and synonym_variants:
        combined = protected_query.lower()
        for word in words:
            expansions = expand_abbreviation(word)
            if expansions:
                combined = re.sub(r'\b' + re.escape(word) + r'\b', expansions[0], combined, flags=re.IGNORECASE)
        if synonym_variants:
            # Add first synonym to combined variant
            synonym_term = get_synonyms(words[0])
            if synonym_term:
                combined = re.sub(r'\b' + re.escape(words[0]) + r'\b', synonym_term[0], combined, flags=re.IGNORECASE)
        enhanced.add_variant(restore_statute_numbers(combined, placeholder_map), "combined enhancement")
    
    # Limit total variants to avoid too many queries
    enhanced.variants = enhanced.variants[:3]  # Max 3 variants
    
    # Log enhancement plan
    if enhanced.enhancement_log:
        logger.info(f"Query enhancement for '{query}':")
        for log_entry in enhanced.enhancement_log:
            logger.info(f"  - {log_entry}")
    else:
        logger.debug(f"No enhancements applied to query: '{query}'")
    
    return enhanced
