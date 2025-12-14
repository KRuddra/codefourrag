"""
Legal terminology synonyms and related terms.
Used for query enhancement and expansion.
"""

# Dictionary of legal synonyms and related terms
# Format: {term: [synonyms, related_terms]}
LEGAL_SYNONYMS = {
    # Law enforcement terms
    "terry stop": ["investigatory detention", "stop and frisk", "temporary detention"],
    "investigatory detention": ["terry stop", "stop and frisk", "temporary detention"],
    "stop and frisk": ["terry stop", "investigatory detention", "temporary detention"],
    
    # Search and seizure
    "search warrant": ["warrant", "search authorization"],
    "probable cause": ["reasonable belief", "sufficient evidence"],
    "reasonable suspicion": ["articulable suspicion", "specific suspicion"],
    
    # Miranda rights
    "miranda warning": ["miranda rights", "miranda advisement", "rights advisement"],
    "miranda rights": ["miranda warning", "miranda advisement", "rights advisement"],
    
    # Traffic violations
    "traffic stop": ["vehicle stop", "traffic detention"],
    "vehicle stop": ["traffic stop", "traffic detention"],
    
    # Crimes
    "homicide": ["murder", "manslaughter", "killing"],
    "assault": ["battery", "physical harm"],
    "theft": ["larceny", "stealing"],
    "burglary": ["breaking and entering", "unlawful entry"],
    
    # Court proceedings
    "arraignment": ["initial appearance", "charging"],
    "plea bargain": ["plea agreement", "plea deal"],
    "sentencing": ["sentencing hearing", "imposition of sentence"],
    
    # Legal concepts
    "due process": ["procedural fairness", "constitutional process"],
    "equal protection": ["equal treatment", "non-discrimination"],
}

# Known legal terms for spell correction (avoid correcting statute numbers)
LEGAL_TERMS = {
    # Crimes
    "homicide", "murder", "manslaughter", "assault", "battery",
    "theft", "larceny", "burglary", "robbery", "fraud",
    
    # Legal procedures
    "arraignment", "plea", "sentencing", "bail", "probation",
    "parole", "warrant", "subpoena", "indictment",
    
    # Law enforcement
    "terry", "detention", "investigatory", "probable", "suspicion",
    "miranda", "custodial", "interrogation",
    
    # Legal concepts
    "jurisdiction", "venue", "statute", "regulation", "ordinance",
    "precedent", "case law", "common law",
    
    # Wisconsin-specific
    "owi", "dui", "operating", "intoxicated", "impaired",
}

# Common misspellings and corrections (only for legal terms)
LEGAL_SPELL_CORRECTIONS = {
    "terry stop": "terry stop",  # Common variations
    "terri stop": "terry stop",
    "miranda": "miranda",
    "mirranda": "miranda",
    "probable": "probable",
    "probabl": "probable",
    "arraignment": "arraignment",
    "arangement": "arraignment",
    "homicide": "homicide",
    "homocide": "homicide",
    "manslaughter": "manslaughter",
    "manslauter": "manslaughter",
}


def get_synonyms(term: str) -> list[str]:
    """
    Get synonyms and related terms for a legal term.
    
    Args:
        term: Legal term to look up
        
    Returns:
        List of synonyms and related terms (empty if not found)
    """
    term_lower = term.lower().strip()
    return LEGAL_SYNONYMS.get(term_lower, [])


def is_legal_term(term: str) -> bool:
    """
    Check if a term is a known legal term.
    
    Args:
        term: Term to check
        
    Returns:
        True if term is a known legal term
    """
    term_lower = term.lower().strip()
    return term_lower in LEGAL_TERMS


def correct_spelling(term: str) -> str:
    """
    Correct spelling of a legal term (if misspelled).
    Only corrects known legal terms, avoids overcorrection.
    
    Args:
        term: Term to correct
        
    Returns:
        Corrected term (original if no correction found)
    """
    term_lower = term.lower().strip()
    return LEGAL_SPELL_CORRECTIONS.get(term_lower, term)
