# -*- coding: utf-8 -*-
"""Query Understanding - Parse natural language queries"""

import json
import logging
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class QueryIntent(Enum):
    """Query intent types"""
    SEARCH_SEMANTIC = "search_semantic"
    SEARCH_ENTITY = "search_entity"
    SEARCH_RELATION = "search_relation"
    SUMMARY = "summary"
    RECOMMEND_CLIP = "recommend_clip"
    ANALYZE_TOPIC = "analyze_topic"
    ANALYZE_QUALITY = "analyze_quality"
    UNKNOWN = "unknown"

@dataclass
class QueryResult:
    """Parsed query result"""
    intent: QueryIntent
    entities: List[str]
    keywords: List[str]
    time_constraint: Optional[Dict]
    filters: Dict
    resolved_query: str
    confidence: float
    metadata: Dict

class QueryUnderstanding:
    """Query understanding engine using LLM"""

    def __init__(self, llm_client, context_manager):
        self.llm_client = llm_client
        self.context_manager = context_manager
        self.intent_prompt = self._load_intent_prompt()
        logger.info("QueryUnderstanding initialized")

    def parse(self, query: str, session_id: Optional[str] = None) -> QueryResult:
        """Parse user query into structured intent"""
        # Get context
        context = self._get_context(session_id)

        # Build prompt
        prompt = self._build_prompt(query, context)

        # Call LLM
        try:
            response = self.llm_client.call(prompt, max_tokens=500)
            result = self._parse_response(response, query)
        except Exception as e:
            logger.error(f"Query parsing failed: {e}")
            result = self._get_default_result(query)

        # Resolve coreferences
        result = self._resolve_coreferences(result, context)

        return result

    def _get_context(self, session_id: Optional[str]) -> Dict:
        """Get conversation context"""
        if not session_id:
            return {}

        context_obj = self.context_manager.get_session(session_id)
        if not context_obj:
            return {}

        recent_entities = self.context_manager.get_recent_entities(session_id, 5)

        return {
            'recent_entities': recent_entities,
            'mode': context_obj.mode.value if hasattr(context_obj.mode, 'value') else str(context_obj.mode)
        }

    def _build_prompt(self, query: str, context: Dict) -> str:
        """Build LLM prompt"""
        context_str = self._format_context(context)
        return self.intent_prompt.format(QUERY=query, CONTEXT=context_str)

    def _parse_response(self, response: str, original_query: str) -> QueryResult:
        """Parse LLM JSON response"""
        try:
            # Try to extract JSON from response
            response = response.strip()

            # Remove markdown code blocks if present
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])

            data = json.loads(response)

            return QueryResult(
                intent=QueryIntent(data.get('intent', 'search_semantic')),
                entities=data.get('entities', []),
                keywords=data.get('keywords', []),
                time_constraint=data.get('time_constraint'),
                filters=data.get('filters', {}),
                resolved_query=data.get('resolved_query', original_query),
                confidence=data.get('confidence', 0.5),
                metadata=data.get('metadata', {})
            )

        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Response was: {response[:200]}")
            return self._get_default_result(original_query)

    def _resolve_coreferences(self, result: QueryResult, context: Dict) -> QueryResult:
        """Resolve pronouns using context"""
        if not result.entities and context.get('recent_entities'):
            # If no entities found but query might reference context
            query_lower = result.resolved_query.lower()
            if any(pronoun in query_lower for pronoun in ['he', 'she', 'it', 'him', 'her', 'they', 'them']):
                result.entities = [context['recent_entities'][0]]
                result.resolved_query = result.resolved_query.replace('he ', f"{result.entities[0]} ")
                result.resolved_query = result.resolved_query.replace('him', result.entities[0])

        return result

    def _load_intent_prompt(self) -> str:
        """Load intent classification prompt"""
        return """You are a query understanding assistant for a video analysis system.

User Query: {QUERY}
Context: {CONTEXT}

Analyze the query and output a JSON object:
{{
  "intent": "search_semantic|search_entity|search_relation|summary|recommend_clip|analyze_topic|analyze_quality",
  "entities": ["entity1", "entity2"],
  "keywords": ["keyword1", "keyword2"],
  "time_constraint": {{"start": 0, "end": 120}} or null,
  "filters": {{"importance_min": 0.7}},
  "resolved_query": "fully resolved query",
  "confidence": 0.85,
  "metadata": {{}}
}}

Rules:
- "what is this video about" -> summary
- "who is X" -> search_entity, entities: ["X"]
- "relationship between X and Y" -> search_relation
- "clips for short videos/TikTok/Reels" -> recommend_clip
- Extract all entities and keywords
- Identify time constraints ("first 5 minutes" -> {{"start": 0, "end": 300}})
- Resolve pronouns using context

Output ONLY the JSON, no other text."""

    def _format_context(self, context: Dict) -> str:
        """Format context for prompt"""
        if not context:
            return "No previous context"

        parts = []
        if context.get('recent_entities'):
            parts.append(f"Recently mentioned: {', '.join(context['recent_entities'])}")
        if context.get('mode'):
            parts.append(f"Mode: {context['mode']}")

        return " | ".join(parts) if parts else "No context"

    def _get_default_result(self, query: str) -> QueryResult:
        """Return default result"""
        return QueryResult(
            intent=QueryIntent.SEARCH_SEMANTIC,
            entities=[],
            keywords=[],
            time_constraint=None,
            filters={},
            resolved_query=query,
            confidence=0.3,
            metadata={'error': 'Failed to parse intent'}
        )

    def __repr__(self) -> str:
        return f"QueryUnderstanding(llm={self.llm_client.provider})"
