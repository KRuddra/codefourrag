"""
Law enforcement and legal abbreviations.
Used for query enhancement and expansion.
"""

# Dictionary of abbreviations and their expansions
# Format: {abbreviation: [expansions]}
ABBREVIATIONS = {
    # DUI/OWI variations
    "owi": ["operating while intoxicated", "dui", "driving under the influence"],
    "dui": ["driving under the influence", "owi", "operating while intoxicated"],
    "dwi": ["driving while intoxicated", "dui", "owi"],
    "owi": ["operating while intoxicated", "dui", "driving under the influence"],
    
    # Law enforcement
    "pd": ["police department"],
    "so": ["sheriff's office", "sheriff office"],
    "dept": ["department"],
    "det": ["detective", "detention"],
    "ofc": ["officer"],
    "lt": ["lieutenant"],
    "sgt": ["sergeant"],
    "cpt": ["captain"],
    
    # Legal terms
    "pc": ["probable cause"],
    "rs": ["reasonable suspicion"],
    "sw": ["search warrant"],
    "arw": ["arrest warrant"],
    "sub": ["subpoena"],
    
    # Court/legal procedures
    "da": ["district attorney", "district attorney's office"],
    "ada": ["assistant district attorney"],
    "pd": ["public defender"],
    "judge": ["judge", "magistrate"],
    
    # Wisconsin-specific
    "wis": ["wisconsin"],
    "wi": ["wisconsin"],
    "stat": ["statute", "statutes"],
    "wis. stat": ["wisconsin statute", "wisconsin statutes"],
    "ws": ["wisconsin statute", "wisconsin statutes"],
    
    # Multi-word terms
    "terry stop": ["investigatory detention", "stop and frisk", "temporary detention"],
    "terry v. ohio": ["terry stop", "investigatory detention"],
}

# Reverse mapping: expansion -> abbreviations
ABBREVIATION_EXPANSIONS = {}
for abbrev, expansions in ABBREVIATIONS.items():
    for expansion in expansions:
        if expansion not in ABBREVIATION_EXPANSIONS:
            ABBREVIATION_EXPANSIONS[expansion] = []
        ABBREVIATION_EXPANSIONS[expansion].append(abbrev)


def expand_abbreviation(abbrev: str) -> list[str]:
    """
    Get expansions for an abbreviation.
    
    Args:
        abbrev: Abbreviation to expand
        
    Returns:
        List of expansions (empty if not found)
    """
    abbrev_lower = abbrev.lower().strip()
    return ABBREVIATIONS.get(abbrev_lower, [])


def get_abbreviations(term: str) -> list[str]:
    """
    Get abbreviations for a term.
    
    Args:
        term: Term to get abbreviations for
        
    Returns:
        List of abbreviations (empty if not found)
    """
    term_lower = term.lower().strip()
    return ABBREVIATION_EXPANSIONS.get(term_lower, [])
