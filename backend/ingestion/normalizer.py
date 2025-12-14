"""
Document normalization utilities
Cleans and standardizes document text while preserving legal context
"""

import re
from typing import List
from collections import Counter


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text:
    - Collapse multiple spaces to single space
    - Normalize line breaks (keep double breaks for paragraphs)
    - Remove trailing/leading whitespace from lines
    - Preserve intentional spacing around section markers
    
    Args:
        text: Raw text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # First, preserve section markers with their spacing
    # Replace section markers with placeholders temporarily
    section_pattern = r'§\s*(\d+\.\d+[a-zA-Z]*)'
    placeholders = {}
    placeholder_idx = 0
    
    def replace_section(match):
        nonlocal placeholder_idx
        placeholder = f"__SECTION_MARKER_{placeholder_idx}__"
        placeholders[placeholder] = match.group(0)
        placeholder_idx += 1
        return placeholder
    
    text = re.sub(section_pattern, replace_section, text)
    
    # Normalize line breaks: collapse multiple line breaks to max 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove trailing whitespace from lines
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Collapse multiple spaces within lines (but preserve section marker spacing)
    lines = text.split('\n')
    normalized_lines = []
    for line in lines:
        # Collapse spaces, but preserve single spaces
        line = re.sub(r'[ \t]+', ' ', line)
        normalized_lines.append(line)
    
    text = '\n'.join(normalized_lines)
    
    # Restore section markers
    for placeholder, original in placeholders.items():
        text = text.replace(placeholder, original)
    
    # Final cleanup: remove excessive blank lines at start/end
    text = text.strip()
    
    return text


def remove_repeated_headers_footers(text: str, threshold: int = 3) -> str:
    """
    Remove repeated headers and footers using line frequency analysis.
    Lines that appear more than threshold times are likely headers/footers.
    
    Args:
        text: Text to clean
        threshold: Minimum occurrences for a line to be considered header/footer
        
    Returns:
        Text with repeated headers/footers removed
    """
    if not text:
        return ""
    
    lines = text.split('\n')
    
    # Count line frequencies (normalized to lowercase, trimmed)
    line_counts = Counter()
    line_mapping = {}  # Map normalized to original
    
    for line in lines:
        normalized = line.strip().lower()
        if normalized and len(normalized) > 3:  # Ignore very short lines
            line_counts[normalized] += 1
            if normalized not in line_mapping:
                line_mapping[normalized] = line
    
    # Identify headers/footers (lines that appear too frequently)
    header_footer_lines = {
        normalized for normalized, count in line_counts.items()
        if count >= threshold
    }
    
    # Filter out header/footer lines, but preserve section markers
    section_pattern = r'§\s*\d+\.\d+'
    filtered_lines = []
    
    for line in lines:
        normalized = line.strip().lower()
        
        # Always keep section markers
        if re.search(section_pattern, line, re.IGNORECASE):
            filtered_lines.append(line)
        # Keep lines that aren't repeated headers/footers
        elif not normalized or normalized not in header_footer_lines:
            filtered_lines.append(line)
        # Skip header/footer lines (but keep blank lines for paragraph separation)
        elif not normalized:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


def preserve_section_markers(text: str) -> str:
    """
    Ensure section markers like "§ 940.01" are preserved with proper spacing.
    This is mainly handled in normalize_whitespace, but this function
    ensures markers are formatted consistently.
    
    Args:
        text: Text that may contain section markers
        
    Returns:
        Text with normalized section markers
    """
    if not text:
        return ""
    
    # Normalize section marker format: § 940.01 (single space after §)
    text = re.sub(r'§\s+', '§ ', text)
    
    # Ensure space after section numbers when followed by text
    text = re.sub(r'(§ \d+\.\d+[a-zA-Z]*)([a-zA-Z])', r'\1 \2', text)
    
    return text


def normalize_text(text: str, remove_headers_footers: bool = True) -> str:
    """
    Main normalization function that applies all normalization steps.
    
    Args:
        text: Raw text to normalize
        remove_headers_footers: Whether to remove repeated headers/footers
        
    Returns:
        Fully normalized text
    """
    if not text:
        return ""
    
    # Step 1: Preserve section markers format
    text = preserve_section_markers(text)
    
    # Step 2: Remove repeated headers/footers if requested
    if remove_headers_footers:
        text = remove_repeated_headers_footers(text)
    
    # Step 3: Normalize whitespace (this also preserves section markers)
    text = normalize_whitespace(text)
    
    return text
