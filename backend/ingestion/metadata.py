"""
Metadata extraction from legal documents
Extracts title, jurisdiction, dates, department, and other metadata
"""

import re
import os
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


def extract_title(text: str, doc_type: str, source_path: str) -> str:
    """
    Extract document title from text.
    
    For HTML: Uses <title> tag if available
    For other formats: Uses first non-empty line (up to 200 chars)
    Falls back to filename without extension
    
    Args:
        text: Document text
        doc_type: Document type (pdf, docx, html, text)
        source_path: Path to source file
        
    Returns:
        Extracted title
    """
    # For HTML, try to extract from title tag
    if doc_type == 'html':
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', text, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            if title:
                return title[:200]  # Limit length
    
    # Get first non-empty line (reasonable length)
    lines = text.split('\n')
    for line in lines:
        stripped = line.strip()
        # Skip very short lines or lines that look like page numbers
        if len(stripped) > 10 and not re.match(r'^\d+$', stripped):
            # Limit to reasonable title length
            return stripped[:200]
    
    # Fallback to filename
    path_obj = Path(source_path)
    return path_obj.stem  # Filename without extension


def detect_jurisdiction(text: str, source_path: str) -> str:
    """
    Detect jurisdiction from text content and path.
    
    Defaults to "WI" (Wisconsin) unless federal keywords are found.
    
    Args:
        text: Document text
        source_path: Path to source file
        
    Returns:
        Jurisdiction code ("WI", "US", "FEDERAL", etc.)
    """
    text_lower = text.lower()
    path_lower = str(source_path).lower()
    
    # Federal keywords
    federal_keywords = [
        'united states code',
        'usc',
        'federal law',
        'u.s. code',
        'federal statute',
        'congress',
        'federal court',
        'supreme court of the united states'
    ]
    
    # Check path first (if it contains "federal")
    if 'federal' in path_lower:
        return "US"
    
    # Check text for federal indicators
    for keyword in federal_keywords:
        if keyword in text_lower:
            return "US"
    
    # Default to Wisconsin state
    return "WI"


def extract_dates(text: str) -> List[str]:
    """
    Extract dates from text using simple regex patterns.
    
    Looks for common date formats:
    - MM/DD/YYYY, MM-DD-YYYY
    - Month DD, YYYY
    - YYYY-MM-DD
    - (YYYY) for years
    
    Args:
        text: Document text
        
    Returns:
        List of found date strings
    """
    dates = []
    
    # Pattern 1: MM/DD/YYYY or MM-DD-YYYY
    pattern1 = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
    matches = re.findall(pattern1, text)
    dates.extend(matches[:5])  # Limit to first 5
    
    # Pattern 2: Month DD, YYYY
    months = r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)'
    pattern2 = rf'\b{months}\s+\d{{1,2}},?\s+\d{{4}}\b'
    matches = re.findall(pattern2, text, re.IGNORECASE)
    dates.extend([m[0] if isinstance(m, tuple) else m for m in matches[:5]])
    
    # Pattern 3: YYYY-MM-DD
    pattern3 = r'\b\d{4}-\d{2}-\d{2}\b'
    matches = re.findall(pattern3, text)
    dates.extend(matches[:5])
    
    # Pattern 4: Standalone years in parentheses (likely statute years)
    pattern4 = r'\((\d{4})\)'
    matches = re.findall(pattern4, text)
    dates.extend([f"({m})" for m in matches[:5]])
    
    return list(set(dates))[:10]  # Deduplicate and limit


def detect_department(source_path: str) -> Optional[str]:
    """
    Detect department from file path.
    
    Looks for patterns like: .../policies/<dept>/...
    
    Args:
        source_path: Path to source file
        
    Returns:
        Department name if found, None otherwise
    """
    path_str = str(source_path).replace('\\', '/')  # Normalize path separators
    path_lower = path_str.lower()
    
    # Check if path contains "policies" directory
    if '/policies/' in path_lower or '\\policies\\' in path_lower:
        parts = path_lower.split('policies')
        if len(parts) > 1:
            # Get the part after "policies"
            after_policies = parts[1].strip('/\\')
            # Get first directory name after policies
            next_parts = [p for p in after_policies.split('/') if p]
            if next_parts and not next_parts[0].endswith(('.pdf', '.docx', '.html', '.txt')):
                return next_parts[0].title()  # Capitalize first letter
    
    return None


def extract_statute_numbers(text: str) -> List[str]:
    """
    Extract Wisconsin statute numbers from text.
    
    Looks for patterns like § 940.01, Section 940.01, Wis. Stat. 940.01
    
    Args:
        text: Document text
        
    Returns:
        List of statute numbers found
    """
    statute_numbers = set()
    
    # Pattern 1: § 940.01 or §940.01
    pattern1 = r'§\s*(\d+\.\d+[a-zA-Z]*)'
    matches = re.findall(pattern1, text)
    statute_numbers.update(matches)
    
    # Pattern 2: Section 940.01 or section 940.01
    pattern2 = r'section\s+(\d+\.\d+[a-zA-Z]*)'
    matches = re.findall(pattern2, text, re.IGNORECASE)
    statute_numbers.update(matches)
    
    # Pattern 3: Wis. Stat. 940.01 or W.S.A. 940.01
    pattern3 = r'(?:wis\.?\s*stat\.?|w\.s\.a\.?)\s*(\d+\.\d+[a-zA-Z]*)'
    matches = re.findall(pattern3, text, re.IGNORECASE)
    statute_numbers.update(matches)
    
    return sorted(list(statute_numbers))


def extract_metadata(text: str, doc_type: str, source_path: str) -> Dict:
    """
    Extract all metadata from a document.
    
    Args:
        text: Document text content
        doc_type: Document type (pdf, docx, html, text)
        source_path: Path to source file
        
    Returns:
        Dictionary containing all extracted metadata
    """
    path_obj = Path(source_path)
    
    # Determine document category from path
    path_str = str(source_path).replace('\\', '/').lower()
    if 'statutes' in path_str or 'statute' in path_str:
        document_type = 'statute'
    elif 'case_law' in path_str or 'case' in path_str:
        document_type = 'case_law'
    elif 'policies' in path_str or 'policy' in path_str:
        document_type = 'policy'
    elif 'training' in path_str:
        document_type = 'training'
    else:
        document_type = 'unknown'
    
    metadata = {
        'title': extract_title(text, doc_type, source_path),
        'source_path': str(source_path),
        'filename': path_obj.name,
        'file_extension': path_obj.suffix,
        'document_type': document_type,
        'file_type': doc_type,
        'jurisdiction': detect_jurisdiction(text, source_path),
        'department': detect_department(source_path),
        'dates': extract_dates(text),
        'statute_numbers': extract_statute_numbers(text),
        'file_size': os.path.getsize(source_path) if os.path.exists(source_path) else 0,
        'extracted_at': datetime.now().isoformat(),
    }
    
    return metadata
