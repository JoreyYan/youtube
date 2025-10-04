# -*- coding: utf-8 -*-
"""Test Day 2 Modules - QueryUnderstanding & HybridRetriever"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from conversational.data_loader import DataLoader
from conversational.context_manager import ContextManager, SessionMode
from conversational.query_understanding import QueryUnderstanding
from conversational.hybrid_retriever import HybridRetriever
from core.llm_client import LLMClient

def test_query_understanding():
    """Test QueryUnderstanding module"""
    print("\n" + "="*60)
    print("TEST 1: QueryUnderstanding - Intent Classification")
    print("="*60)

    # Initialize
    try:
        llm_client = LLMClient(provider="openai", model="gpt-4o-mini")
        context_manager = ContextManager()
        query_engine = QueryUnderstanding(llm_client, context_manager)
        print("[OK] QueryUnderstanding initialized")
    except Exception as e:
        print(f"[FAIL] Initialization failed: {e}")
        return

    # Create test session
    session_id = context_manager.create_session("test_video", SessionMode.EXPLORATION)

    # Test cases
    test_queries = [
        "What is this video about?",
        "Who is Elon Musk?",
        "What's the relationship between Tesla and SpaceX?",
        "Find clips suitable for TikTok",
        "Tell me about AI topics in first 5 minutes"
    ]

    print("\nTesting query parsing:")
    for i, query in enumerate(test_queries, 1):
        print(f"\n[Query {i}] {query}")
        try:
            result = query_engine.parse(query, session_id)
            print(f"  Intent: {result.intent.value}")
            print(f"  Entities: {result.entities}")
            print(f"  Keywords: {result.keywords[:3]}")
            print(f"  Confidence: {result.confidence:.2f}")
            print("  [OK] Parsed successfully")
        except Exception as e:
            print(f"  [FAIL] Parse failed: {e}")

def test_hybrid_retriever():
    """Test HybridRetriever module"""
    print("\n" + "="*60)
    print("TEST 2: HybridRetriever - Multi-Strategy Retrieval")
    print("="*60)

    # Initialize
    try:
        data_loader = DataLoader("data/output_pipeline_v3")
        retriever = HybridRetriever(data_loader)
        print("[OK] HybridRetriever initialized")
    except Exception as e:
        print(f"[FAIL] Initialization failed: {e}")
        return

    # Check data availability
    print("\nData availability check:")
    try:
        atoms = data_loader.get_atoms()
        segments = data_loader.get_segments()
        entities = data_loader.get_entities()
        print(f"  Atoms: {len(atoms)}")
        print(f"  Segments: {len(segments)}")
        print(f"  Entities: {len(entities)}")
    except Exception as e:
        print(f"  [FAIL] Data loading failed: {e}")
        return

    # Test retrieval strategies
    from conversational.query_understanding import QueryResult, QueryIntent

    test_cases = [
        QueryResult(
            intent=QueryIntent.SEARCH_ENTITY,
            entities=["AI", "machine learning"],
            keywords=["technology"],
            time_constraint=None,
            filters={},
            resolved_query="What is AI?",
            confidence=0.9,
            metadata={}
        ),
        QueryResult(
            intent=QueryIntent.SUMMARY,
            entities=[],
            keywords=["overview"],
            time_constraint=None,
            filters={},
            resolved_query="Summarize the video",
            confidence=0.95,
            metadata={}
        )
    ]

    print("\nTesting retrieval strategies:")
    for i, query_result in enumerate(test_cases, 1):
        print(f"\n[Test {i}] Intent: {query_result.intent.value}")
        try:
            results = retriever.retrieve(query_result, top_k=5)
            print(f"  Retrieved {len(results)} results")
            for j, result in enumerate(results[:3], 1):
                print(f"    [{j}] {result.item_type} | score={result.score:.2f} | by={result.matched_by}")
            print("  [OK] Retrieval successful")
        except Exception as e:
            print(f"  [FAIL] Retrieval failed: {e}")

def test_integration():
    """Test QueryUnderstanding + HybridRetriever integration"""
    print("\n" + "="*60)
    print("TEST 3: Integration - End-to-End Query Pipeline")
    print("="*60)

    # Initialize all components
    try:
        llm_client = LLMClient(provider="openai", model="gpt-4o-mini")
        context_manager = ContextManager()
        data_loader = DataLoader("data/output_pipeline_v3")
        query_engine = QueryUnderstanding(llm_client, context_manager)
        retriever = HybridRetriever(data_loader)
        print("[OK] All components initialized")
    except Exception as e:
        print(f"[FAIL] Initialization failed: {e}")
        return

    # Create session
    session_id = context_manager.create_session("test_video", SessionMode.EXPLORATION)

    # Test end-to-end pipeline
    test_query = "What are the main topics discussed in this video?"
    print(f"\nQuery: {test_query}")

    try:
        # Step 1: Parse query
        print("\n[Step 1] Parsing query...")
        query_result = query_engine.parse(test_query, session_id)
        print(f"  Intent: {query_result.intent.value}")
        print(f"  Keywords: {query_result.keywords[:3]}")

        # Step 2: Retrieve content
        print("\n[Step 2] Retrieving content...")
        results = retriever.retrieve(query_result, top_k=5)
        print(f"  Retrieved {len(results)} results")

        # Step 3: Update context
        print("\n[Step 3] Updating context...")
        context_manager.add_turn(session_id, "user", test_query)
        context_manager.update_focus_entities(session_id, query_result.entities)
        print(f"  Focus entities: {context_manager.get_recent_entities(session_id, 3)}")

        print("\n[OK] End-to-end pipeline successful!")

    except Exception as e:
        print(f"\n[FAIL] Pipeline failed: {e}")

def main():
    print("\n" + "="*60)
    print("Day 2 Module Testing Suite")
    print("Testing: QueryUnderstanding, HybridRetriever, Integration")
    print("="*60)

    # Check if API key is available
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("\nWARNING: OPENAI_API_KEY not found in environment")
        print("Some tests may fail. Set the API key to run all tests.")

    # Run tests
    test_query_understanding()
    test_hybrid_retriever()
    test_integration()

    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)

if __name__ == "__main__":
    main()
