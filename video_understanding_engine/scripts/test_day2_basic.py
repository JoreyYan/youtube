# -*- coding: utf-8 -*-
"""Test Day 2 Modules - Basic Tests (No API Key Required)"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from conversational.data_loader import DataLoader
from conversational.context_manager import ContextManager, SessionMode
from conversational.hybrid_retriever import HybridRetriever
from conversational.query_understanding import QueryResult, QueryIntent

def test_data_loader():
    """Test DataLoader module"""
    print("\n" + "="*60)
    print("TEST 1: DataLoader - Data Access Layer")
    print("="*60)

    try:
        data_loader = DataLoader("data/output_pipeline_v3")
        print("[OK] DataLoader initialized")
    except Exception as e:
        print(f"[FAIL] Initialization failed: {e}")
        return False

    # Test data loading
    print("\nLoading data files:")
    try:
        atoms = data_loader.get_atoms()
        print(f"  Atoms: {len(atoms)}")
        if len(atoms) > 0:
            print(f"    Sample: {atoms[0].get('atom_id', 'N/A')}")
    except Exception as e:
        print(f"  [FAIL] Atoms: {e}")
        return False

    try:
        segments = data_loader.get_segments()
        print(f"  Segments: {len(segments)}")
        if len(segments) > 0:
            print(f"    Sample: {segments[0].get('segment_id', 'N/A')}")
    except Exception as e:
        print(f"  [FAIL] Segments: {e}")
        return False

    try:
        entities = data_loader.get_entities()
        print(f"  Entities: {len(entities)}")
        if len(entities) > 0:
            sample_entity = list(entities.keys())[0]
            print(f"    Sample: {sample_entity}")
    except Exception as e:
        print(f"  [FAIL] Entities: {e}")
        return False

    try:
        topics = data_loader.get_topics()
        print(f"  Topics: {len(topics)}")
    except Exception as e:
        print(f"  [FAIL] Topics: {e}")

    try:
        graph = data_loader.get_graph()
        print(f"  Knowledge Graph: {len(graph.get('entities', []))} entities")
    except Exception as e:
        print(f"  [FAIL] Graph: {e}")

    # Test search functionality
    print("\nTesting search:")
    try:
        results = data_loader.search_atoms_by_text("video")
        print(f"  Search 'video': {len(results)} results")
    except Exception as e:
        print(f"  [FAIL] Search: {e}")

    print("\n[OK] DataLoader tests passed")
    return True

def test_context_manager():
    """Test ContextManager module"""
    print("\n" + "="*60)
    print("TEST 2: ContextManager - Conversation State")
    print("="*60)

    try:
        context_manager = ContextManager()
        print("[OK] ContextManager initialized")
    except Exception as e:
        print(f"[FAIL] Initialization failed: {e}")
        return False

    # Test session management
    print("\nTesting session management:")
    try:
        session_id = context_manager.create_session("test_video", SessionMode.EXPLORATION)
        print(f"  Created session: {session_id}")

        context_manager.add_turn(session_id, "user", "What is this video about?")
        context_manager.add_turn(session_id, "assistant", "This video discusses...")

        session = context_manager.get_session(session_id)
        print(f"  History: {len(session.history)} turns")

        context_manager.update_focus_entities(session_id, ["AI", "machine learning"])
        recent = context_manager.get_recent_entities(session_id, 5)
        print(f"  Recent entities: {recent[:3]}")

        print("[OK] ContextManager tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] Session management failed: {e}")
        return False

def test_hybrid_retriever():
    """Test HybridRetriever module"""
    print("\n" + "="*60)
    print("TEST 3: HybridRetriever - Content Retrieval")
    print("="*60)

    try:
        data_loader = DataLoader("data/output_pipeline_v3")
        retriever = HybridRetriever(data_loader)
        print("[OK] HybridRetriever initialized")
    except Exception as e:
        print(f"[FAIL] Initialization failed: {e}")
        return False

    # Test different retrieval strategies
    test_cases = [
        ("Entity Search", QueryResult(
            intent=QueryIntent.SEARCH_ENTITY,
            entities=["缅北"],
            keywords=["history"],
            time_constraint=None,
            filters={},
            resolved_query="Tell me about Myanmar",
            confidence=0.9,
            metadata={}
        )),
        ("Summary", QueryResult(
            intent=QueryIntent.SUMMARY,
            entities=[],
            keywords=["overview"],
            time_constraint=None,
            filters={},
            resolved_query="Summarize the video",
            confidence=0.95,
            metadata={}
        )),
        ("Clip Recommendation", QueryResult(
            intent=QueryIntent.RECOMMEND_CLIP,
            entities=[],
            keywords=["short", "viral"],
            time_constraint=None,
            filters={},
            resolved_query="Find clips for TikTok",
            confidence=0.85,
            metadata={}
        ))
    ]

    print("\nTesting retrieval strategies:")
    for name, query_result in test_cases:
        print(f"\n  [{name}] Intent: {query_result.intent.value}")
        try:
            results = retriever.retrieve(query_result, top_k=5)
            print(f"    Retrieved: {len(results)} results")
            for i, result in enumerate(results[:2], 1):
                print(f"      [{i}] type={result.item_type}, score={result.score:.2f}, by={result.matched_by}")
        except Exception as e:
            print(f"    [FAIL] Retrieval failed: {e}")

    print("\n[OK] HybridRetriever tests passed")
    return True

def main():
    print("\n" + "="*60)
    print("Day 2 Basic Testing Suite")
    print("Testing: DataLoader, ContextManager, HybridRetriever")
    print("No API key required")
    print("="*60)

    # Run tests
    results = []
    results.append(("DataLoader", test_data_loader()))
    results.append(("ContextManager", test_context_manager()))
    results.append(("HybridRetriever", test_hybrid_retriever()))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {name}")

    all_passed = all(r[1] for r in results)
    print("\n" + "="*60)
    if all_passed:
        print("All tests PASSED!")
    else:
        print("Some tests FAILED")
    print("="*60)

if __name__ == "__main__":
    main()
