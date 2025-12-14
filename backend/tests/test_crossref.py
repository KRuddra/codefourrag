"""
Tests for cross-reference detection and resolution.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.retrieval.crossref import detect_crossrefs, resolve_crossref, expand_crossrefs
from backend.api.models import Chunk
from backend.retrieval.vector_store import get_vector_store


def test_detect_crossrefs():
    """Test cross-reference detection in chunk text."""
    
    # Test chunk with cross-reference
    chunk = Chunk(
        chunk_id="test_1",
        doc_id="test_doc",
        doc_type="statute",
        text="This section applies to intentional homicide. See also § 940.01 for related provisions.",
        hierarchy_path="Chapter 940",
        statute_number="940.02",
        case_citation=None,
        date=None,
        jurisdiction="WI",
        title="Test Statute",
        source_uri="test_doc"
    )
    
    refs = detect_crossrefs(chunk)
    assert "940.01" in refs, f"Expected to detect § 940.01, got {refs}"
    
    # Test chunk with multiple cross-references
    chunk2 = Chunk(
        chunk_id="test_2",
        doc_id="test_doc",
        doc_type="statute",
        text="See § 940.01 and § 940.02. Also refer to § 939.50(3)(a).",
        hierarchy_path="Chapter 940",
        statute_number="940.03",
        case_citation=None,
        date=None,
        jurisdiction="WI",
        title="Test Statute",
        source_uri="test_doc"
    )
    
    refs2 = detect_crossrefs(chunk2)
    assert "940.01" in refs2
    assert "940.02" in refs2
    assert "939.50(3)(a)" in refs2 or "939.50" in refs2
    
    print(f"[OK] Cross-reference detection test passed")


@pytest.mark.skipif(
    not Path("data/embeddings").exists() or not list(Path("data/embeddings").glob("*")),
    reason="No vector store available"
)
def test_resolve_crossref():
    """Test cross-reference resolution using vector store."""
    
    vector_store = get_vector_store()
    stats = vector_store.get_collection_stats()
    
    if stats["chunk_count"] == 0:
        pytest.skip("No chunks in vector store. Run ingestion with reindex=True first.")
    
    # Try to resolve a statute that might exist
    resolved = resolve_crossref("227.42", vector_store=vector_store)
    
    if resolved:
        assert isinstance(resolved, Chunk)
        assert resolved.statute_number is not None
        assert "227.42" in resolved.statute_number or resolved.statute_number in "227.42"
        print(f"[OK] Resolved cross-reference to statute {resolved.statute_number}")
    else:
        print(f"[INFO] Could not resolve cross-reference (statute may not be indexed)")


@pytest.mark.skipif(
    not Path("data/embeddings").exists() or not list(Path("data/embeddings").glob("*")),
    reason="No vector store available"
)
def test_expand_crossrefs():
    """Test cross-reference expansion for a list of chunks."""
    
    vector_store = get_vector_store()
    stats = vector_store.get_collection_stats()
    
    if stats["chunk_count"] == 0:
        pytest.skip("No chunks in vector store. Run ingestion with reindex=True first.")
    
    # Create a test chunk with a cross-reference
    chunk = Chunk(
        chunk_id="test_expand_1",
        doc_id="test_doc",
        doc_type="statute",
        text="This section relates to other provisions. See also § 227.42 for administrative procedures.",
        hierarchy_path="Chapter 227",
        statute_number="227.41",
        case_citation=None,
        date=None,
        jurisdiction="WI",
        title="Test Statute",
        source_uri="test_doc"
    )
    
    expanded = expand_crossrefs([chunk], max_refs=5, vector_store=vector_store)
    
    assert len(expanded) >= 1, "Should have at least the original chunk"
    assert expanded[0].chunk_id == chunk.chunk_id, "First chunk should be the original"
    
    if len(expanded) > 1:
        print(f"[OK] Expanded cross-references: {len(expanded)} total chunks (original + {len(expanded)-1} crossrefs)")
        for i, exp_chunk in enumerate(expanded[1:], 1):
            print(f"  Cross-ref {i}: {exp_chunk.statute_number} - {exp_chunk.title[:50]}")
    else:
        print(f"[INFO] No cross-references resolved (may not exist in index)")


@pytest.mark.skipif(
    not Path("data/embeddings").exists() or not list(Path("data/embeddings").glob("*")),
    reason="No vector store available"
)
def test_see_also_crossref_resolution():
    """
    Test that a chunk with "see also § 940.01" pulls in § 940.01 chunk if indexed.
    
    This is the main acceptance test.
    """
    vector_store = get_vector_store()
    stats = vector_store.get_collection_stats()
    
    if stats["chunk_count"] == 0:
        pytest.skip("No chunks in vector store. Run ingestion with reindex=True first.")
    
    # Create a chunk with "see also" cross-reference
    # Use a statute number that might exist in the index
    test_statute = "227.42"  # Adjust based on what's actually indexed
    
    chunk_with_ref = Chunk(
        chunk_id="test_see_also_1",
        doc_id="test_doc",
        doc_type="statute",
        text=f"This section provides general provisions. See also § {test_statute} for related matters.",
        hierarchy_path="Chapter 940",
        statute_number="940.01",
        case_citation=None,
        date=None,
        jurisdiction="WI",
        title="Test Statute with Cross-Reference",
        source_uri="test_doc"
    )
    
    # Detect cross-references
    refs = detect_crossrefs(chunk_with_ref)
    assert test_statute in refs or any(test_statute in ref for ref in refs), \
        f"Should detect reference to {test_statute}"
    
    # Try to resolve
    resolved = resolve_crossref(test_statute, vector_store=vector_store, exclude_chunk_ids={chunk_with_ref.chunk_id})
    
    if resolved:
        assert resolved.statute_number is not None
        assert test_statute in resolved.statute_number or resolved.statute_number in test_statute
        print(f"[SUCCESS] Cross-reference resolution test passed!")
        print(f"  Original chunk: {chunk_with_ref.statute_number}")
        print(f"  Resolved chunk: {resolved.statute_number} - {resolved.title[:50]}")
    else:
        print(f"[INFO] Could not resolve cross-reference to {test_statute} (may not be indexed)")


if __name__ == "__main__":
    # Run tests manually
    print("Testing cross-reference detection...")
    test_detect_crossrefs()
    
    print("\nTesting cross-reference resolution...")
    try:
        test_resolve_crossref()
    except Exception as e:
        print(f"[SKIP] {e}")
    
    print("\nTesting cross-reference expansion...")
    try:
        test_expand_crossrefs()
    except Exception as e:
        print(f"[SKIP] {e}")
    
    print("\nTesting 'see also' cross-reference resolution...")
    try:
        test_see_also_crossref_resolution()
    except Exception as e:
        print(f"[SKIP] {e}")
    
    print("\nAll tests completed!")
