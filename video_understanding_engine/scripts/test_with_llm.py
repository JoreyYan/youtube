# -*- coding: utf-8 -*-
"""Test with Real LLM - Full Integration Test"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    print(f"[OK] Loaded environment from {env_path}")
else:
    print("[WARNING] No .env file found")

# Check API key
if 'OPENAI_API_KEY' in os.environ:
    print(f"[OK] OPENAI_API_KEY found (length: {len(os.environ['OPENAI_API_KEY'])})")
else:
    print("[FAIL] OPENAI_API_KEY not found")
    sys.exit(1)

from conversational import (
    DataLoader, ContextManager, SessionMode,
    QueryUnderstanding, HybridRetriever,
    ResponseGenerator, ConversationalInterface
)
from core.llm_client import LLMClient

def test_query_understanding():
    """Test QueryUnderstanding with real LLM"""
    print("\n" + "="*60)
    print("TEST 1: QueryUnderstanding with Real LLM")
    print("="*60)

    try:
        llm_client = LLMClient(provider="openai", model="gpt-4o-mini")
        context_manager = ContextManager()
        query_engine = QueryUnderstanding(llm_client, context_manager)
        print("[OK] Components initialized")
    except Exception as e:
        print(f"[FAIL] Initialization failed: {e}")
        return False

    # Test queries
    test_queries = [
        "What is this video about?",
        "Who is mentioned in the video?",
        "Find clips suitable for TikTok"
    ]

    print("\nTesting query parsing with LLM:")
    for i, query in enumerate(test_queries, 1):
        print(f"\n[Query {i}] {query}")
        try:
            result = query_engine.parse(query)
            print(f"  Intent: {result.intent.value}")
            print(f"  Entities: {result.entities}")
            print(f"  Keywords: {result.keywords[:3]}")
            print(f"  Confidence: {result.confidence:.2f}")
        except Exception as e:
            print(f"  [FAIL] Parse failed: {e}")
            return False

    print("\n[OK] QueryUnderstanding test passed")
    return True

def test_full_conversation():
    """Test full conversation with real LLM"""
    print("\n" + "="*60)
    print("TEST 2: Full Conversation Pipeline with Real LLM")
    print("="*60)

    # Initialize all components
    print("\nInitializing components...")
    try:
        data_loader = DataLoader("data/output_pipeline_v3")
        context_manager = ContextManager()
        llm_client = LLMClient(provider="openai", model="gpt-4o-mini")
        query_engine = QueryUnderstanding(llm_client, context_manager)
        retriever = HybridRetriever(data_loader)
        response_gen = ResponseGenerator(llm_client)

        interface = ConversationalInterface(
            data_loader,
            context_manager,
            query_engine,
            retriever,
            response_gen
        )
        print("[OK] All components initialized")
    except Exception as e:
        print(f"[FAIL] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test conversation
    test_queries = [
        "What is this video about?",
        "Tell me more about the main topics"
    ]

    session_id = None
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Conversation Turn {i} ---")
        print(f"User: {query}")

        try:
            response = interface.ask(query, session_id=session_id)

            if not session_id:
                session_id = response.metadata.get('session_id')

            print(f"\nAssistant:\n{response.answer}\n")

            if response.sources:
                print("Sources:")
                for j, source in enumerate(response.sources[:3], 1):
                    print(f"  [{j}] {source.item_type} | " +
                          f"{source.start_time:.0f}s-{source.end_time:.0f}s | " +
                          f"score={source.relevance_score:.2f}")

            print(f"\nMetrics:")
            print(f"  Response time: {response.response_time_ms:.0f}ms")
            print(f"  Confidence: {response.confidence:.2f}")
            print(f"  Retrieved items: {response.retrieved_count}")

        except Exception as e:
            print(f"[FAIL] Query failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    # Check conversation history
    print(f"\n--- Session History ---")
    history = interface.get_session_history(session_id)
    print(f"Total turns: {len(history)}")
    for msg in history:
        role = msg.role if hasattr(msg, 'role') else 'unknown'
        content = msg.content if hasattr(msg, 'content') else str(msg)
        print(f"  [{role}] {content[:50]}...")

    print("\n[OK] Full conversation test passed")
    return True

def main():
    print("="*60)
    print("Full Integration Test with Real LLM")
    print("="*60)

    results = []

    # Test 1: Query Understanding
    results.append(("QueryUnderstanding", test_query_understanding()))

    # Test 2: Full Conversation
    results.append(("Full Conversation", test_full_conversation()))

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
        print("All tests PASSED! System ready for use.")
    else:
        print("Some tests FAILED")
    print("="*60)

if __name__ == "__main__":
    main()
