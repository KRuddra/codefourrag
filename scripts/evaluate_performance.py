"""
Performance Evaluation Script
Measures retrieval accuracy, response time, and relevance scoring
"""

import os
import sys
import time
import json
import statistics
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


# Test query set - representative queries for evaluation
TEST_QUERIES = [
    {
        "query": "What are the elements of OWI 3rd offense in Wisconsin?",
        "expected_statute": "§ 346.63",
        "query_type": "statute_lookup",
        "expected_sources": ["statute"],
    },
    {
        "query": "Can officers search a vehicle during a traffic stop without a warrant?",
        "expected_statute": None,
        "query_type": "case_law",
        "expected_sources": ["case_law", "statute"],
    },
    {
        "query": "What is the statute of limitations for misdemeanor theft?",
        "expected_statute": "§ 939.74",
        "query_type": "statute_lookup",
        "expected_sources": ["statute"],
    },
    {
        "query": "Recent Terry stop case law in Wisconsin",
        "expected_statute": None,
        "query_type": "case_law",
        "expected_sources": ["case_law"],
    },
    {
        "query": "Department pursuit policy",
        "expected_statute": None,
        "query_type": "policy",
        "expected_sources": ["policy"],
    },
    {
        "query": "Miranda warnings for juveniles",
        "expected_statute": None,
        "query_type": "case_law",
        "expected_sources": ["case_law", "statute"],
    },
    {
        "query": "§ 940.01",
        "expected_statute": "§ 940.01",
        "query_type": "statute_lookup",
        "expected_sources": ["statute"],
    },
    {
        "query": "Vehicle search during traffic stop",
        "expected_statute": None,
        "query_type": "case_law",
        "expected_sources": ["case_law", "statute"],
    },
]


def check_health() -> bool:
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False


def send_chat_query(query: str) -> Dict[str, Any]:
    """Send a chat query and measure response time"""
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json={"message": query},
            timeout=60
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json(),
                "response_time": response_time,
            }
        else:
            return {
                "success": False,
                "error": f"Status {response.status_code}: {response.text}",
                "response_time": response_time,
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_time": time.time() - start_time,
        }


def evaluate_retrieval_accuracy(result: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate retrieval accuracy metrics"""
    metrics = {
        "has_sources": len(result.get("sources", [])) > 0,
        "num_sources": len(result.get("sources", [])),
        "expected_statute_found": False,
        "expected_source_type_found": False,
        "top_score": 0.0,
        "avg_score": 0.0,
    }
    
    sources = result.get("sources", [])
    
    if sources:
        scores = [s.get("score", 0.0) for s in sources]
        metrics["top_score"] = max(scores) if scores else 0.0
        metrics["avg_score"] = statistics.mean(scores) if scores else 0.0
        
        # Check if expected statute is found
        if expected.get("expected_statute"):
            statute_num = expected["expected_statute"].replace("§", "").strip()
            for source in sources:
                metadata = source.get("metadata", {})
                if metadata.get("statute_number") and statute_num in metadata.get("statute_number", ""):
                    metrics["expected_statute_found"] = True
                    break
        
        # Check if expected source type is found
        expected_types = expected.get("expected_sources", [])
        source_types = [s.get("metadata", {}).get("doc_type", "") for s in sources]
        metrics["expected_source_type_found"] = any(
            expected_type in source_types for expected_type in expected_types
        )
    
    return metrics


def evaluate_relevance_scoring(result: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate relevance scoring"""
    sources = result.get("sources", [])
    confidence = result.get("confidence", 0.0)
    
    metrics = {
        "confidence": confidence,
        "num_sources": len(sources),
        "score_distribution": {},
        "score_variance": 0.0,
        "score_range": (0.0, 0.0),
    }
    
    if sources:
        scores = [s.get("score", 0.0) for s in sources]
        if scores:
            metrics["score_variance"] = statistics.variance(scores) if len(scores) > 1 else 0.0
            metrics["score_range"] = (min(scores), max(scores))
            
            # Score distribution buckets
            high = sum(1 for s in scores if s >= 0.8)
            medium = sum(1 for s in scores if 0.5 <= s < 0.8)
            low = sum(1 for s in scores if s < 0.5)
            
            metrics["score_distribution"] = {
                "high (≥0.8)": high,
                "medium (0.5-0.8)": medium,
                "low (<0.5)": low,
            }
    
    return metrics


def run_performance_evaluation() -> Dict[str, Any]:
    """Run full performance evaluation"""
    print("=" * 80)
    print("Performance Evaluation")
    print("=" * 80)
    print()
    
    # Check API health
    print("Checking API health...")
    if not check_health():
        print("❌ API is not running. Please start the backend server.")
        return {"error": "API not available"}
    print("✅ API is running")
    print()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_queries": len(TEST_QUERIES),
        "queries": [],
        "summary": {},
    }
    
    response_times = []
    retrieval_accuracies = []
    relevance_metrics = []
    
    print("Running test queries...")
    print("-" * 80)
    
    for i, test_query in enumerate(TEST_QUERIES, 1):
        query = test_query["query"]
        print(f"\n[{i}/{len(TEST_QUERIES)}] Query: {query}")
        
        result = send_chat_query(query)
        
        if not result["success"]:
            print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
            continue
        
        response_time = result["response_time"]
        response_data = result["data"]
        
        response_times.append(response_time)
        
        # Evaluate retrieval accuracy
        accuracy_metrics = evaluate_retrieval_accuracy(response_data, test_query)
        retrieval_accuracies.append(accuracy_metrics)
        
        # Evaluate relevance scoring
        relevance_metric = evaluate_relevance_scoring(response_data)
        relevance_metrics.append(relevance_metric)
        
        query_result = {
            "query": query,
            "query_type": test_query["query_type"],
            "response_time": response_time,
            "confidence": response_data.get("confidence", 0.0),
            "num_sources": len(response_data.get("sources", [])),
            "flags": response_data.get("flags", []),
            "accuracy": accuracy_metrics,
            "relevance": relevance_metric,
        }
        
        results["queries"].append(query_result)
        
        print(f"  ✅ Response time: {response_time:.2f}s")
        print(f"  📊 Confidence: {response_data.get('confidence', 0.0):.2%}")
        print(f"  📚 Sources: {len(response_data.get('sources', []))}")
        print(f"  🎯 Expected statute found: {accuracy_metrics['expected_statute_found']}")
        print(f"  📄 Expected source type found: {accuracy_metrics['expected_source_type_found']}")
    
    # Calculate summary statistics
    if response_times:
        results["summary"] = {
            "response_time": {
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "min": min(response_times),
                "max": max(response_times),
                "stdev": statistics.stdev(response_times) if len(response_times) > 1 else 0.0,
            },
            "retrieval_accuracy": {
                "queries_with_sources": sum(1 for m in retrieval_accuracies if m["has_sources"]),
                "expected_statute_found_rate": sum(1 for m in retrieval_accuracies if m["expected_statute_found"]) / len(retrieval_accuracies),
                "expected_source_type_found_rate": sum(1 for m in retrieval_accuracies if m["expected_source_type_found"]) / len(retrieval_accuracies),
                "avg_num_sources": statistics.mean([m["num_sources"] for m in retrieval_accuracies]),
                "avg_top_score": statistics.mean([m["top_score"] for m in retrieval_accuracies if m["top_score"] > 0]),
            },
            "relevance_scoring": {
                "avg_confidence": statistics.mean([m["confidence"] for m in relevance_metrics]),
                "avg_num_sources": statistics.mean([m["num_sources"] for m in relevance_metrics]),
                "avg_score_variance": statistics.mean([m["score_variance"] for m in relevance_metrics if m["score_variance"] > 0]),
            },
        }
    
    return results


def print_summary(results: Dict[str, Any]):
    """Print formatted summary"""
    print()
    print("=" * 80)
    print("PERFORMANCE SUMMARY")
    print("=" * 80)
    print()
    
    summary = results.get("summary", {})
    
    # Response Time
    rt = summary.get("response_time", {})
    print("📊 RESPONSE TIME BENCHMARKS")
    print("-" * 80)
    print(f"  Mean:   {rt.get('mean', 0):.2f}s")
    print(f"  Median: {rt.get('median', 0):.2f}s")
    print(f"  Min:    {rt.get('min', 0):.2f}s")
    print(f"  Max:    {rt.get('max', 0):.2f}s")
    print(f"  StdDev: {rt.get('stdev', 0):.2f}s")
    print()
    
    # Retrieval Accuracy
    ra = summary.get("retrieval_accuracy", {})
    print("🎯 RETRIEVAL ACCURACY METRICS")
    print("-" * 80)
    print(f"  Queries with sources: {ra.get('queries_with_sources', 0)}/{results['total_queries']}")
    expected_statute_rate = ra.get('expected_statute_found_rate', 0)
    print(f"  Expected statute found rate: {expected_statute_rate:.1%}")
    expected_source_rate = ra.get('expected_source_type_found_rate', 0)
    print(f"  Expected source type found rate: {expected_source_rate:.1%}")
    print(f"  Average number of sources: {ra.get('avg_num_sources', 0):.1f}")
    print(f"  Average top score: {ra.get('avg_top_score', 0):.3f}")
    print()
    
    # Relevance Scoring
    rs = summary.get("relevance_scoring", {})
    print("⭐ RELEVANCE SCORING EVALUATION")
    print("-" * 80)
    print(f"  Average confidence: {rs.get('avg_confidence', 0):.1%}")
    print(f"  Average number of sources: {rs.get('avg_num_sources', 0):.1f}")
    print(f"  Average score variance: {rs.get('avg_score_variance', 0):.3f}")
    print()
    
    print("=" * 80)


def main():
    """Main execution"""
    results = run_performance_evaluation()
    
    if "error" in results:
        return
    
    print_summary(results)
    
    # Save results to JSON file
    output_file = Path(__file__).parent.parent / "performance_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    print()


if __name__ == "__main__":
    main()

