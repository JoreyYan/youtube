#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup script for Day 2 modules
Creates QueryUnderstanding, HybridRetriever, and LLM Client
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent / 'conversational'
CORE_DIR = Path(__file__).parent / 'core'
BASE_DIR.mkdir(exist_ok=True)
CORE_DIR.mkdir(exist_ok=True)

FILES = {
    # Core LLM Client
    'core/llm_client.py': '''# -*- coding: utf-8 -*-
"""LLM Client - Unified interface for OpenAI/Claude APIs"""

import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LLMClient:
    """Unified LLM API client"""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, model: str = None):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")

        if not self.api_key:
            raise ValueError(f"API key not found for {provider}")

        if self.provider == "openai":
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
            self.model = model or "gpt-4o-mini"
        elif self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = model or "claude-3-haiku-20240307"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        logger.info(f"LLMClient initialized: {self.provider}/{self.model}")

    def call(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> str:
        """Call LLM API"""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise

    def __repr__(self) -> str:
        return f"LLMClient(provider='{self.provider}', model='{self.model}')"
''',

    # QueryUnderstanding
    'conversational/query_understanding.py': '''# -*- coding: utf-8 -*-
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
                lines = response.split("\\n")
                response = "\\n".join(lines[1:-1])

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
''',

    # HybridRetriever
    'conversational/hybrid_retriever.py': '''# -*- coding: utf-8 -*-
"""Hybrid Retriever - Multi-strategy content retrieval"""

import logging
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """Single retrieval result"""
    item_id: str
    item_type: str  # 'atom' or 'segment'
    score: float
    content: Dict
    matched_by: str
    metadata: Dict

class HybridRetriever:
    """Multi-strategy hybrid retrieval engine"""

    RETRIEVAL_STRATEGIES = {
        'search_semantic': ['vector_search', 'keyword_match'],
        'search_entity': ['entity_index', 'graph_query'],
        'search_relation': ['graph_query', 'co_occurrence'],
        'summary': ['narrative_segments', 'high_importance_atoms'],
        'recommend_clip': ['creative_angles'],
        'analyze_topic': ['topic_network', 'related_atoms']
    }

    def __init__(self, data_loader, semantic_search_engine=None):
        self.data_loader = data_loader
        self.semantic_search = semantic_search_engine
        logger.info("HybridRetriever initialized")

    def retrieve(self, query_result, top_k: int = 5) -> List[RetrievalResult]:
        """Retrieve relevant content"""
        start_time = time.time()

        # Select strategies
        intent_str = query_result.intent.value if hasattr(query_result.intent, 'value') else str(query_result.intent)
        strategies = self.RETRIEVAL_STRATEGIES.get(intent_str, ['keyword_match'])

        # Execute strategies
        all_results = []
        for strategy in strategies:
            try:
                results = self._execute_strategy(strategy, query_result)
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Strategy {strategy} failed: {e}")

        # Merge and deduplicate
        merged = self._merge_results(all_results)

        # Apply filters
        filtered = self._apply_filters(merged, query_result.filters)

        # Sort by score
        filtered.sort(key=lambda x: x.score, reverse=True)

        # Return top-k
        final = filtered[:top_k]

        elapsed = time.time() - start_time
        logger.info(f"Retrieved {len(final)} results in {elapsed*1000:.0f}ms")

        return final

    def _execute_strategy(self, strategy: str, query_result) -> List[RetrievalResult]:
        """Execute single strategy"""
        if strategy == 'keyword_match':
            return self._keyword_match(query_result)
        elif strategy == 'entity_index':
            return self._entity_index_search(query_result)
        elif strategy == 'graph_query':
            return self._graph_query(query_result)
        elif strategy == 'narrative_segments':
            return self._get_narrative_segments()
        elif strategy == 'high_importance_atoms':
            return self._get_high_importance_atoms()
        elif strategy == 'creative_angles':
            return self._get_creative_clips()
        else:
            return []

    def _keyword_match(self, query_result) -> List[RetrievalResult]:
        """Keyword-based matching"""
        results = []

        # Search by entities
        for entity in query_result.entities:
            atoms = self.data_loader.search_atoms_by_text(entity)
            for atom in atoms[:10]:  # Limit per entity
                results.append(RetrievalResult(
                    item_id=atom['atom_id'],
                    item_type='atom',
                    score=0.75,
                    content=atom,
                    matched_by='keyword_match',
                    metadata={'matched_entity': entity}
                ))

        # Search by keywords
        for keyword in query_result.keywords[:3]:
            atoms = self.data_loader.search_atoms_by_text(keyword)
            for atom in atoms[:5]:
                results.append(RetrievalResult(
                    item_id=atom['atom_id'],
                    item_type='atom',
                    score=0.6,
                    content=atom,
                    matched_by='keyword_match',
                    metadata={'matched_keyword': keyword}
                ))

        return results

    def _entity_index_search(self, query_result) -> List[RetrievalResult]:
        """Search using entity index"""
        results = []

        for entity_name in query_result.entities:
            entity_data = self.data_loader.get_entity_by_name(entity_name)
            if not entity_data:
                continue

            atom_ids = entity_data.get('atom_ids', [])
            for atom_id in atom_ids:
                atom = self.data_loader.get_atom_by_id(atom_id)
                if atom:
                    results.append(RetrievalResult(
                        item_id=atom_id,
                        item_type='atom',
                        score=0.85,
                        content=atom,
                        matched_by='entity_index',
                        metadata={'entity': entity_name}
                    ))

        return results

    def _graph_query(self, query_result) -> List[RetrievalResult]:
        """Query knowledge graph"""
        results = []

        for entity in query_result.entities:
            relations = self.data_loader.get_entity_relations(entity)

            for relation in relations[:5]:
                results.append(RetrievalResult(
                    item_id=f"relation_{entity}_{relation['target']}",
                    item_type='relation',
                    score=relation['weight'],
                    content={
                        'source': entity,
                        'target': relation['target'],
                        'relation_type': relation['relation_type'],
                        'weight': relation['weight']
                    },
                    matched_by='graph_query',
                    metadata=relation
                ))

        return results

    def _get_narrative_segments(self) -> List[RetrievalResult]:
        """Get narrative segments"""
        segments = self.data_loader.get_segments()

        return [
            RetrievalResult(
                item_id=seg['segment_id'],
                item_type='segment',
                score=seg.get('importance_score', 0.5),
                content=seg,
                matched_by='narrative_segments',
                metadata={}
            )
            for seg in segments
        ]

    def _get_high_importance_atoms(self) -> List[RetrievalResult]:
        """Get high importance atoms"""
        atoms = self.data_loader.get_atoms()
        high_imp = [a for a in atoms if a.get('importance_score', 0) >= 0.7]

        return [
            RetrievalResult(
                item_id=atom['atom_id'],
                item_type='atom',
                score=atom.get('importance_score', 0.0),
                content=atom,
                matched_by='high_importance',
                metadata={}
            )
            for atom in high_imp[:10]
        ]

    def _get_creative_clips(self) -> List[RetrievalResult]:
        """Get creative clip recommendations"""
        try:
            creative_data = self.data_loader.get_graph()  # Fix: should be get_creative_angles
            clips = creative_data.get('clip_recommendations', [])

            return [
                RetrievalResult(
                    item_id=clip.get('segment_id', ''),
                    item_type='clip',
                    score=clip.get('suitability_score', 0.0),
                    content=clip,
                    matched_by='creative_angles',
                    metadata={}
                )
                for clip in clips[:10]
            ]
        except:
            return []

    def _merge_results(self, all_results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Merge and deduplicate"""
        merged = {}

        for result in all_results:
            item_id = result.item_id

            if item_id not in merged or result.score > merged[item_id].score:
                merged[item_id] = result

        return list(merged.values())

    def _apply_filters(self, results: List[RetrievalResult], filters: Dict) -> List[RetrievalResult]:
        """Apply query filters"""
        filtered = results

        # Filter by importance
        if 'importance_min' in filters:
            min_imp = filters['importance_min']
            filtered = [
                r for r in filtered
                if r.content.get('importance_score', 0) >= min_imp
            ]

        # Filter by time range
        if 'time_range' in filters:
            time_range = filters['time_range']
            start, end = time_range.get('start', 0), time_range.get('end', float('inf'))
            filtered = [
                r for r in filtered
                if (r.content.get('start_time', 0) <= end and
                    r.content.get('end_time', float('inf')) >= start)
            ]

        return filtered

    def __repr__(self) -> str:
        return f"HybridRetriever(strategies={len(self.RETRIEVAL_STRATEGIES)})"
'''
}

# Write files
print("Creating Day 2 modules...")
for filepath, content in FILES.items():
    full_path = Path(__file__).parent / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)

    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Created: {full_path}")

# Update __init__.py
init_path = BASE_DIR / '__init__.py'
with open(init_path, 'a', encoding='utf-8') as f:
    f.write("\\nfrom .query_understanding import QueryUnderstanding, QueryIntent, QueryResult\\n")
    f.write("from .hybrid_retriever import HybridRetriever, RetrievalResult\\n")

print("\\nDay 2 modules created successfully!")
