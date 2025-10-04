# -*- coding: utf-8 -*-
"""Response Generator - Natural Language Answer Generation"""

import logging
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Source:
    """Answer source reference"""
    item_id: str
    item_type: str
    start_time: float
    end_time: float
    excerpt: str
    relevance_score: float

@dataclass
class Response:
    """Conversation response"""
    answer: str
    sources: List[Source]
    confidence: float
    retrieved_count: int
    response_time_ms: float
    metadata: Dict

class ResponseGenerator:
    """Natural language response generator"""

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.answer_prompt = self._load_answer_prompt()
        logger.info("ResponseGenerator initialized")

    def generate(
        self,
        query: str,
        query_result,
        retrieval_results: List,
        context = None
    ) -> Response:
        """Generate final answer"""
        start_time = time.time()

        # Build prompt
        prompt = self._build_prompt(query, query_result, retrieval_results, context)

        # Call LLM
        try:
            answer_text = self.llm_client.call(prompt, max_tokens=800, temperature=0.3)
            confidence = 0.8
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            answer_text = self._generate_fallback_answer(query_result, retrieval_results)
            confidence = 0.4

        # Extract sources
        sources = self._extract_sources(retrieval_results)

        # Build response
        response = Response(
            answer=answer_text,
            sources=sources,
            confidence=confidence,
            retrieved_count=len(retrieval_results),
            response_time_ms=(time.time() - start_time) * 1000,
            metadata={'intent': query_result.intent.value if hasattr(query_result.intent, 'value') else str(query_result.intent)}
        )

        logger.info(f"Generated response in {response.response_time_ms:.0f}ms")
        return response

    def _build_prompt(self, query: str, query_result, retrieval_results: List, context) -> str:
        """Build LLM prompt"""
        intent_str = query_result.intent.value if hasattr(query_result.intent, 'value') else str(query_result.intent)

        # Format retrieved content
        content_items = []
        for i, result in enumerate(retrieval_results[:5], 1):
            item = result.content
            excerpt = self._get_excerpt(item)
            time_str = self._format_time(item.get('start_time', 0), item.get('end_time', 0))
            content_items.append(f"[{i}] {time_str}\n{excerpt}")

        content_str = "\n\n".join(content_items)

        # Build prompt
        prompt = f"""You are answering questions about a video based on retrieved content.

User Query: {query}
Query Intent: {intent_str}

Retrieved Content:
{content_str}

Instructions:
- Answer the question directly based on the retrieved content
- Cite sources using [Source N: MM:SS-MM:SS] format
- If content is insufficient, say so honestly
- Keep answer concise (2-3 paragraphs max)

Answer:"""

        return prompt

    def _generate_fallback_answer(self, query_result, retrieval_results: List) -> str:
        """Generate fallback answer when LLM fails"""
        if not retrieval_results:
            return "I couldn't find relevant information to answer your question."

        # Simple concatenation
        excerpts = []
        for result in retrieval_results[:3]:
            excerpt = self._get_excerpt(result.content)
            excerpts.append(excerpt)

        return " ".join(excerpts)

    def _extract_sources(self, retrieval_results: List) -> List[Source]:
        """Extract sources from retrieval results"""
        sources = []

        for result in retrieval_results[:5]:
            item = result.content
            sources.append(Source(
                item_id=result.item_id,
                item_type=result.item_type,
                start_time=item.get('start_time', 0.0),
                end_time=item.get('end_time', 0.0),
                excerpt=self._get_excerpt(item),
                relevance_score=result.score
            ))

        return sources

    def _get_excerpt(self, item: Dict) -> str:
        """Get text excerpt from item"""
        if 'text' in item:
            return item['text'][:200]
        elif 'content' in item:
            return item['content'][:200]
        elif 'summary' in item:
            return item['summary'][:200]
        else:
            return str(item)[:200]

    def _format_time(self, start: float, end: float) -> str:
        """Format timestamp"""
        def seconds_to_mmss(seconds):
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins:02d}:{secs:02d}"

        if start == 0 and end == 0:
            return "[Time N/A]"

        return f"[{seconds_to_mmss(start)}-{seconds_to_mmss(end)}]"

    def _load_answer_prompt(self) -> str:
        """Load answer generation prompt"""
        return ""  # Prompt built dynamically in _build_prompt

    def __repr__(self) -> str:
        return f"ResponseGenerator(llm={self.llm_client.provider})"
