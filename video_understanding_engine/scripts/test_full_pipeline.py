# -*- coding: utf-8 -*-
"""Test Full Pipeline - End-to-End Without API Key"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from conversational import (
    DataLoader, ContextManager, SessionMode,
    HybridRetriever, ConversationalInterface
)
from conversational.query_understanding import QueryResult, QueryIntent
from conversational.response_generator import ResponseGenerator

# Mock LLM Client
class MockLLMClient:
    """Mock LLM client for testing"""
    def __init__(self):
        self.provider = "mock"
        self.model = "mock-model"

    def call(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        """Return mock response"""
        if "summarize" in prompt.lower() or "summary" in prompt.lower():
            return "This video provides a historical overview of the Golden Triangle region, focusing on Myanmar's border areas and the complex history of local conflicts and international relations."
        elif "entities" in prompt.lower() or "who is" in prompt.lower():
            return "Based on the video content, the mentioned entities include various historical figures and organizations related to the Myanmar border region."
        else:
            return "The video discusses the historical context of the Myanmar-China border region, particularly focusing on the Golden Triangle area and its significance in regional history."

# Mock QueryUnderstanding
class MockQueryUnderstanding:
    """Mock query understanding for testing"""
    def __init__(self, llm_client, context_manager):
        self.llm_client = llm_client
        self.context_manager = context_manager

    def parse(self, query: str, session_id=None):
        """Return mock query result"""
        query_lower = query.lower()

        if "summary" in query_lower or "about" in query_lower:
            intent = QueryIntent.SUMMARY
            entities = []
            keywords = ["overview", "summary"]
        elif "who" in query_lower or "entity" in query_lower:
            intent = QueryIntent.SEARCH_ENTITY
            entities = ["Myanmar", "Golden Triangle"]
            keywords = ["entity", "person"]
        elif "clip" in query_lower or "tiktok" in query_lower:
            intent = QueryIntent.RECOMMEND_CLIP
            entities = []
            keywords = ["clip", "short"]
        else:
            intent = QueryIntent.SEARCH_SEMANTIC
            entities = []
            keywords = query_lower.split()[:3]

        return QueryResult(
            intent=intent,
            entities=entities,
            keywords=keywords,
            time_constraint=None,
            filters={},
            resolved_query=query,
            confidence=0.85,
            metadata={}
        )

def test_full_pipeline():
    """Test complete pipeline without real API"""
    print("="*60)
    print("Full Pipeline Test - Mock Mode (No API Key)")
    print("="*60)

    # Initialize all components
    print("\n[1] Initializing components...")
    try:
        data_loader = DataLoader("data/output_pipeline_v3")
        context_manager = ContextManager()
        mock_llm = MockLLMClient()
        query_engine = MockQueryUnderstanding(mock_llm, context_manager)
        retriever = HybridRetriever(data_loader)
        response_gen = ResponseGenerator(mock_llm)

        interface = ConversationalInterface(
            data_loader,
            context_manager,
            query_engine,
            retriever,
            response_gen
        )
        print("  [OK] All components initialized")
    except Exception as e:
        print(f"  [FAIL] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test queries
    test_queries = [
        "What is this video about?",
        "Tell me about Myanmar",
        "Find clips for TikTok"
    ]

    print("\n[2] Testing queries...")
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Query {i} ---")
        print(f"Question: {query}")

        try:
            response = interface.ask(query)

            print(f"\nAnswer:\n{response.answer}\n")

            if response.sources:
                print("Sources:")
                for j, source in enumerate(response.sources[:3], 1):
                    print(f"  [{j}] {source.item_type} | {source.start_time:.0f}s-{source.end_time:.0f}s | score={source.relevance_score:.2f}")

            print(f"\nMetrics:")
            print(f"  Response time: {response.response_time_ms:.0f}ms")
            print(f"  Confidence: {response.confidence:.2f}")
            print(f"  Retrieved items: {response.retrieved_count}")
            print(f"  Session ID: {response.metadata.get('session_id', 'N/A')}")

        except Exception as e:
            print(f"  [FAIL] Query failed: {e}")
            import traceback
            traceback.print_exc()

    # Test conversation context
    print("\n[3] Testing conversation context...")
    session_id = None
    try:
        # First query
        response1 = interface.ask("What is this video about?")
        session_id = response1.metadata.get('session_id')
        print(f"  Created session: {session_id}")

        # Follow-up query (should use context)
        response2 = interface.ask("Tell me more", session_id=session_id)
        print(f"  Follow-up query processed")

        # Check history
        history = interface.get_session_history(session_id)
        print(f"  Conversation history: {len(history)} turns")

        print("  [OK] Context management working")
    except Exception as e:
        print(f"  [FAIL] Context test failed: {e}")

    print("\n" + "="*60)
    print("Full Pipeline Test Complete!")
    print("="*60)

if __name__ == "__main__":
    test_full_pipeline()
