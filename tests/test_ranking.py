
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.retrieval.retrieval_pipeline import RetrievalPipeline
from unittest.mock import MagicMock

def test_hierarchy_and_division_routing():
    pipeline = RetrievalPipeline()
    pipeline.embedding_service.search = MagicMock()
    
    # Sample results
    mock_results = [
        {"score": 0.8, "text": "Land registration rules", "court": "Magistrate Court", "document_title": "Case A"},
        {"score": 0.75, "text": "Title deed dispute", "court": "Environment and Land Court", "document_title": "Case B"},
        {"score": 0.7, "text": "Constitutional right to property", "court": "Supreme Court", "document_title": "Case C"},
    ]
    
    pipeline.embedding_service.search.return_value = mock_results.copy()
    
    # Test query: "land property dispute"
    # Expected: 
    # 1. Magistrate Court (0.8) -> Hierarchy weight 0.40 -> 0.32
    # 2. ELC (0.75) -> Hierarchy weight 0.70 -> 0.525. 
    #    PLUS Division boost (0.12) because query is about land -> 0.645
    # 3. Supreme Court (0.7) -> Hierarchy weight 1.00 -> 0.70
    
    results = pipeline.retrieve("land property dispute")
    
    print("\nRanking Results for 'land property dispute':")
    for r in results:
        print(f"- {r['document_title']} ({r['court']}): Final Score: {r.get('adjusted_score', r['score']):.3f} | HP: {r.get('hierarchy_weight', 1.0)} | DB: {r.get('division_boost', 0.0)}")

    assert results[0]['document_title'] == "Case C", "Supreme Court should be first due to hierarchy weight 1.0"
    assert results[1]['document_title'] == "Case B", "ELC should be second due to hierarchy 0.7 + division boost"
    assert results[2]['document_title'] == "Case A", "Magistrate Court should be last due to low hierarchy weight 0.4"
    
    print("\n✅ Ranking test passed!")

if __name__ == "__main__":
    try:
        test_hierarchy_and_division_routing()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
