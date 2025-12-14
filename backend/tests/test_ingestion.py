"""
Tests for document ingestion pipeline
"""

import pytest
from backend.api.models import Document
from backend.ingestion.chunking import chunk_document, extract_statute_number_from_text


def test_statute_chunking_extracts_statute_number():
    """Test that chunker extracts statute number into chunk metadata"""
    
    # Create a sample statute document
    statute_text = """
    CHAPTER 940
    
    CRIMES AGAINST LIFE AND BODILY SECURITY
    
    940.01 First-degree intentional homicide. (1) Whoever causes the death 
    of another human being with intent to kill that person or another 
    is guilty of a Class A felony.
    
    (2) In this section "intent to kill" means the mental purpose to take 
    the life of another human being.
    
    940.02 Second-degree intentional homicide. Whoever causes the death 
    of another human being with intent to kill that person is guilty 
    of a Class B felony if the state does not prove beyond a reasonable 
    doubt that the killing was premeditated.
    """
    
    document = Document(
        text=statute_text,
        metadata={
            "title": "Wisconsin Statutes Chapter 940",
            "jurisdiction": "WI",
            "document_type": "statute",
            "statute_numbers": ["940.01", "940.02"],
            "dates": ["2023"],
            "source_path": "data/raw/statutes/chapter_940.pdf"
        },
        source_path="data/raw/statutes/chapter_940.pdf"
    )
    
    # Chunk the document
    chunks = chunk_document(document)
    
    # Verify chunks were created
    assert len(chunks) > 0, "Should create at least one chunk"
    
    # Check that statute numbers are extracted into chunk metadata
    statute_numbers_found = []
    for chunk in chunks:
        assert chunk.statute_number is not None or chunk.text.strip(), "Each chunk should have statute number or valid text"
        
        if chunk.statute_number:
            statute_numbers_found.append(chunk.statute_number)
        
        # Verify chunk has required fields
        assert chunk.chunk_id, "Chunk should have chunk_id"
        assert chunk.doc_id == document.source_path, "Chunk doc_id should match document source_path"
        assert chunk.doc_type == "statute", "Chunk doc_type should be statute"
        assert chunk.text, "Chunk should have text"
        assert chunk.hierarchy_path, "Chunk should have hierarchy_path"
        assert chunk.jurisdiction == "WI", "Chunk should preserve jurisdiction"
        assert chunk.title == document.metadata["title"], "Chunk should preserve title"
        assert chunk.source_uri == document.source_path, "Chunk should have source_uri"
    
    # Verify that at least one chunk contains a statute number
    assert len(statute_numbers_found) > 0, "At least one chunk should have a statute_number"
    
    # Verify statute numbers found are in the expected list
    for statute_num in statute_numbers_found:
        assert statute_num in ["940.01", "940.02"], f"Found unexpected statute number: {statute_num}"


def test_extract_statute_number_from_text():
    """Test the extract_statute_number_from_text helper function"""
    
    # Test with section marker
    text1 = "§ 940.01 First-degree intentional homicide."
    assert extract_statute_number_from_text(text1) == "940.01"
    
    # Test with "Section" prefix
    text2 = "Section 939.50(3)(a) defines the penalty structure."
    assert extract_statute_number_from_text(text2) == "939.50(3)(a)"
    
    # Test without statute number
    text3 = "This is just regular text without any statute reference."
    assert extract_statute_number_from_text(text3) is None
    
    # Test with multiple statute references (should return first one)
    text4 = "See § 940.01 and also § 940.02 for related offenses."
    result = extract_statute_number_from_text(text4)
    assert result in ["940.01", "940.02"]  # Either one is acceptable


def test_chunk_boundaries_align_with_sections():
    """Test that chunk boundaries align with legal sections"""
    
    statute_text = """
    940.01 First-degree intentional homicide. (1) Whoever causes the death 
    of another human being with intent to kill that person or another 
    is guilty of a Class A felony.
    
    (2) In this section "intent to kill" means the mental purpose to take 
    the life of another human being.
    
    940.02 Second-degree intentional homicide. Whoever causes the death 
    of another human being with intent to kill that person is guilty 
    of a Class B felony.
    """
    
    document = Document(
        text=statute_text,
        metadata={
            "title": "Test Statutes",
            "jurisdiction": "WI",
            "document_type": "statute",
            "statute_numbers": ["940.01", "940.02"],
            "source_path": "test.pdf"
        },
        source_path="test.pdf"
    )
    
    chunks = chunk_document(document)
    
    # Verify that chunks align with section boundaries
    # Each major section (940.01, 940.02) should ideally be in its own chunk or clearly separated
    assert len(chunks) >= 2, "Should create at least 2 chunks for 2 sections"
    
    # Check that statute numbers are preserved in hierarchy or metadata
    chunk_statutes = [chunk.statute_number for chunk in chunks if chunk.statute_number]
    assert len(set(chunk_statutes)) >= 1, "Should extract statute numbers from chunks"
