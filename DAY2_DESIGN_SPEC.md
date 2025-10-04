# Phase 2 Unit 3 - Day 2 设计规范

**日期**: 2025-10-04
**任务**: 查询理解 + 混合检索
**状态**: 🚧 设计中

---

## 📋 目标

实现智能对话系统的核心检索能力：
1. **QueryUnderstanding** - 理解用户自然语言查询
2. **HybridRetriever** - 多策略混合检索引擎

---

## 🧠 模块1: QueryUnderstanding

### 功能定位
将用户的自然语言查询转换为结构化的查询意图，支持上下文理解和指代消解。

### 核心类设计

```python
# -*- coding: utf-8 -*-
"""
Query Understanding Module

Convert natural language queries into structured intents
"""

from typing import Dict, List, Optional
from enum import Enum
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Query intent types"""
    SEARCH_SEMANTIC = "search_semantic"      # Semantic search
    SEARCH_ENTITY = "search_entity"          # Entity query
    SEARCH_RELATION = "search_relation"      # Relation query
    SUMMARY = "summary"                      # Video summary
    RECOMMEND_CLIP = "recommend_clip"        # Clip recommendation
    ANALYZE_TOPIC = "analyze_topic"          # Topic analysis
    ANALYZE_QUALITY = "analyze_quality"      # Quality analysis
    UNKNOWN = "unknown"                      # Unknown intent


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
    """
    Query Understanding Engine

    Features:
    - Intent classification
    - Entity extraction
    - Query rewriting
    - Context fusion
    """

    def __init__(self, api_client, context_manager):
        """
        Initialize QueryUnderstanding

        Args:
            api_client: LLM API client (OpenAI/Claude)
            context_manager: ContextManager instance
        """
        self.api_client = api_client
        self.context_manager = context_manager

        # Intent classification prompt template
        self.intent_prompt = self._load_intent_prompt()

    def parse(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> QueryResult:
        """
        Parse user query into structured intent

        Args:
            query: User query string
            session_id: Session ID for context

        Returns:
            QueryResult object
        """
        # 1. Get conversation context
        context = self._get_context(session_id)

        # 2. Build prompt with context
        prompt = self._build_prompt(query, context)

        # 3. Call LLM for intent classification
        response = self.api_client.call(prompt)

        # 4. Parse LLM response
        result = self._parse_response(response)

        # 5. Apply coreference resolution
        result = self._resolve_coreferences(result, context)

        return result

    def _get_context(self, session_id: Optional[str]) -> Dict:
        """Get conversation context"""
        if not session_id:
            return {}

        context_obj = self.context_manager.get_session(session_id)
        if not context_obj:
            return {}

        return {
            'recent_entities': self.context_manager.get_recent_entities(session_id, 5),
            'last_user_message': self.context_manager.get_last_user_message(session_id),
            'mode': context_obj.mode.value
        }

    def _build_prompt(self, query: str, context: Dict) -> str:
        """Build LLM prompt with context"""
        prompt = self.intent_prompt.format(
            QUERY=query,
            CONTEXT=self._format_context(context)
        )
        return prompt

    def _parse_response(self, response: str) -> QueryResult:
        """Parse LLM JSON response into QueryResult"""
        import json

        try:
            data = json.loads(response)

            return QueryResult(
                intent=QueryIntent(data.get('intent', 'unknown')),
                entities=data.get('entities', []),
                keywords=data.get('keywords', []),
                time_constraint=data.get('time_constraint'),
                filters=data.get('filters', {}),
                resolved_query=data.get('resolved_query', query),
                confidence=data.get('confidence', 0.5),
                metadata=data.get('metadata', {})
            )
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._get_default_result(query)

    def _resolve_coreferences(
        self,
        result: QueryResult,
        context: Dict
    ) -> QueryResult:
        """Resolve pronouns and references using context"""
        # If query mentions "he/she/it/this" but no entities extracted
        # Try to infer from recent_entities in context

        if not result.entities and context.get('recent_entities'):
            # Simple heuristic: use most recent entity
            result.entities = [context['recent_entities'][0]]

        return result

    def _load_intent_prompt(self) -> str:
        """Load intent classification prompt template"""
        return """
You are a query understanding assistant. Analyze the user's query and extract structured information.

User Query: {QUERY}

Conversation Context: {CONTEXT}

Output a JSON object with the following fields:
{{
  "intent": "search_semantic|search_entity|search_relation|summary|recommend_clip|analyze_topic|analyze_quality",
  "entities": ["entity1", "entity2"],
  "keywords": ["keyword1", "keyword2"],
  "time_constraint": {{"start": 0, "end": 120}} or null,
  "filters": {{"importance_min": 0.7, "entity_type": "person"}},
  "resolved_query": "fully resolved query with context",
  "confidence": 0.85,
  "metadata": {{}}
}}

Rules:
1. If query asks "what is this video about" -> intent: summary
2. If query asks "who is X" -> intent: search_entity, entities: ["X"]
3. If query asks "relationship between X and Y" -> intent: search_relation
4. If query asks "clips for short videos" -> intent: recommend_clip
5. If query contains pronouns (he/she/it), resolve using context
6. Extract all mentioned entities and keywords
7. Identify time constraints if mentioned (e.g., "first 5 minutes")

Output ONLY the JSON object, no additional text.
"""

    def _format_context(self, context: Dict) -> str:
        """Format context for prompt"""
        if not context:
            return "No previous context"

        parts = []
        if context.get('recent_entities'):
            parts.append(f"Recently mentioned: {', '.join(context['recent_entities'])}")
        if context.get('last_user_message'):
            parts.append(f"Last question: {context['last_user_message'].content}")
        if context.get('mode'):
            parts.append(f"Mode: {context['mode']}")

        return " | ".join(parts)

    def _get_default_result(self, query: str) -> QueryResult:
        """Return default result when parsing fails"""
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
```

### 使用示例

```python
# Initialize
from core.llm_client import LLMClient
from conversational.context_manager import ContextManager
from conversational.query_understanding import QueryUnderstanding

api_client = LLMClient(api_key="...")
context_manager = ContextManager()
understander = QueryUnderstanding(api_client, context_manager)

# Create session
session_id = context_manager.create_session("video_123")

# Parse query 1
result1 = understander.parse("Who is Luo Xinghan?", session_id)
print(result1.intent)  # QueryIntent.SEARCH_ENTITY
print(result1.entities)  # ['Luo Xinghan']

# Add to context
context_manager.update_focus_entities(session_id, result1.entities)

# Parse query 2 with context
result2 = understander.parse("What happened to him later?", session_id)
print(result2.resolved_query)  # "What happened to Luo Xinghan later?"
print(result2.entities)  # ['Luo Xinghan'] (resolved from context)
```

---

## 🔍 模块2: HybridRetriever

### 功能定位
根据查询意图，组合多种检索策略找到最相关内容。

### 核心类设计

```python
# -*- coding: utf-8 -*-
"""
Hybrid Retriever Module

Multi-strategy content retrieval engine
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Single retrieval result"""
    item_id: str
    item_type: str  # 'atom' or 'segment'
    score: float
    content: Dict
    matched_by: str  # Which strategy matched this
    metadata: Dict


class HybridRetriever:
    """
    Hybrid Retrieval Engine

    Supports multiple retrieval strategies:
    - Vector similarity search
    - Keyword matching
    - Entity index lookup
    - Graph query
    - Multi-dimensional filtering
    """

    # Strategy mapping
    RETRIEVAL_STRATEGIES = {
        'search_semantic': ['vector_search', 'keyword_match'],
        'search_entity': ['entity_index', 'graph_query'],
        'search_relation': ['graph_query', 'co_occurrence'],
        'summary': ['narrative_segments', 'high_importance_atoms'],
        'recommend_clip': ['creative_angles', 'suitability_ranking'],
        'analyze_topic': ['topic_network', 'related_atoms']
    }

    def __init__(
        self,
        data_loader,
        semantic_search_engine=None
    ):
        """
        Initialize HybridRetriever

        Args:
            data_loader: DataLoader instance
            semantic_search_engine: SemanticSearchEngine instance (optional)
        """
        self.data_loader = data_loader
        self.semantic_search = semantic_search_engine

    def retrieve(
        self,
        query_result,
        top_k: int = 5,
        enable_reranking: bool = True
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant content based on query intent

        Args:
            query_result: QueryResult from QueryUnderstanding
            top_k: Number of results to return
            enable_reranking: Whether to rerank results

        Returns:
            List of RetrievalResult objects
        """
        start_time = time.time()

        # 1. Select retrieval strategies based on intent
        strategies = self._select_strategies(query_result.intent)

        # 2. Execute each strategy
        all_results = []
        for strategy in strategies:
            results = self._execute_strategy(strategy, query_result)
            all_results.extend(results)

        # 3. Merge and deduplicate
        merged_results = self._merge_results(all_results)

        # 4. Apply filters
        filtered_results = self._apply_filters(merged_results, query_result.filters)

        # 5. Rerank if enabled
        if enable_reranking:
            filtered_results = self._rerank(filtered_results, query_result)

        # 6. Return top-k
        final_results = filtered_results[:top_k]

        elapsed = time.time() - start_time
        logger.info(f"Retrieved {len(final_results)} results in {elapsed*1000:.1f}ms")

        return final_results

    def _select_strategies(self, intent) -> List[str]:
        """Select retrieval strategies based on intent"""
        intent_str = intent.value if hasattr(intent, 'value') else str(intent)
        return self.RETRIEVAL_STRATEGIES.get(intent_str, ['vector_search'])

    def _execute_strategy(
        self,
        strategy: str,
        query_result
    ) -> List[RetrievalResult]:
        """Execute a single retrieval strategy"""

        if strategy == 'vector_search':
            return self._vector_search(query_result)
        elif strategy == 'keyword_match':
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
        elif strategy == 'topic_network':
            return self._topic_network_search(query_result)
        else:
            logger.warning(f"Unknown strategy: {strategy}")
            return []

    def _vector_search(self, query_result) -> List[RetrievalResult]:
        """Semantic vector similarity search"""
        if not self.semantic_search:
            return []

        # Use resolved query for better context
        query_text = query_result.resolved_query

        # Search in vector database
        results = self.semantic_search.search(
            query=query_text,
            top_k=10
        )

        # Convert to RetrievalResult
        return [
            RetrievalResult(
                item_id=r['atom_id'],
                item_type='atom',
                score=r['score'],
                content=r,
                matched_by='vector_search',
                metadata={'similarity': r['score']}
            )
            for r in results
        ]

    def _keyword_match(self, query_result) -> List[RetrievalResult]:
        """Keyword-based exact matching"""
        results = []

        # Search by entities
        for entity in query_result.entities:
            atoms = self.data_loader.search_atoms_by_text(entity)
            for atom in atoms:
                results.append(RetrievalResult(
                    item_id=atom['atom_id'],
                    item_type='atom',
                    score=0.8,  # Fixed score for exact match
                    content=atom,
                    matched_by='keyword_match',
                    metadata={'matched_entity': entity}
                ))

        # Search by keywords
        for keyword in query_result.keywords:
            atoms = self.data_loader.search_atoms_by_text(keyword)
            for atom in atoms:
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

            # Get atoms where this entity appears
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
        """Query knowledge graph for relationships"""
        results = []

        for entity in query_result.entities:
            relations = self.data_loader.get_entity_relations(entity)

            # Add related entities as results
            for relation in relations[:5]:  # Top 5 relations
                target = relation['target']
                results.append(RetrievalResult(
                    item_id=f"relation_{entity}_{target}",
                    item_type='relation',
                    score=relation['weight'],
                    content={
                        'source': entity,
                        'target': target,
                        'relation_type': relation['relation_type'],
                        'weight': relation['weight']
                    },
                    matched_by='graph_query',
                    metadata=relation
                ))

        return results

    def _get_narrative_segments(self) -> List[RetrievalResult]:
        """Get all narrative segments (for summary)"""
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
        atoms = self.data_loader.get_atoms_by_importance(min_importance=0.7)

        return [
            RetrievalResult(
                item_id=atom['atom_id'],
                item_type='atom',
                score=atom.get('importance_score', 0.0),
                content=atom,
                matched_by='high_importance',
                metadata={}
            )
            for atom in atoms
        ]

    def _get_creative_clips(self) -> List[RetrievalResult]:
        """Get recommended clips for short videos"""
        creative_data = self.data_loader.get_creative_angles()
        clips = creative_data.get('clip_recommendations', [])

        return [
            RetrievalResult(
                item_id=clip.get('segment_id', ''),
                item_type='clip',
                score=clip.get('suitability_score', 0.0),
                content=clip,
                matched_by='creative_angles',
                metadata={'platforms': clip.get('recommended_platforms', [])}
            )
            for clip in clips
        ]

    def _topic_network_search(self, query_result) -> List[RetrievalResult]:
        """Search by topic network"""
        # Implementation: search topics.json for related atoms
        topics_data = self.data_loader.get_topics()
        # ... topic matching logic
        return []

    def _merge_results(self, all_results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Merge results from multiple strategies and deduplicate"""
        # Use dict to deduplicate by item_id
        merged = {}

        for result in all_results:
            item_id = result.item_id

            if item_id not in merged:
                merged[item_id] = result
            else:
                # If duplicate, keep the one with higher score
                if result.score > merged[item_id].score:
                    merged[item_id] = result

        return list(merged.values())

    def _apply_filters(
        self,
        results: List[RetrievalResult],
        filters: Dict
    ) -> List[RetrievalResult]:
        """Apply query filters"""
        filtered = results

        # Filter by importance
        if 'importance_min' in filters:
            min_imp = filters['importance_min']
            filtered = [
                r for r in filtered
                if r.content.get('importance_score', 0) >= min_imp
            ]

        # Filter by entity type
        if 'entity_type' in filters:
            entity_type = filters['entity_type']
            # ... filter logic

        # Filter by time range
        if 'time_range' in filters:
            time_range = filters['time_range']
            start, end = time_range['start'], time_range['end']
            filtered = [
                r for r in filtered
                if (r.content.get('start_time', 0) <= end and
                    r.content.get('end_time', float('inf')) >= start)
            ]

        return filtered

    def _rerank(
        self,
        results: List[RetrievalResult],
        query_result
    ) -> List[RetrievalResult]:
        """Rerank results by relevance"""
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results
```

### 使用示例

```python
# Initialize
from conversational.data_loader import DataLoader
from conversational.hybrid_retriever import HybridRetriever
from searchers.semantic_search import SemanticSearchEngine

data_loader = DataLoader("data/output_pipeline_v3/")
semantic_search = SemanticSearchEngine(...)  # From Phase 2
retriever = HybridRetriever(data_loader, semantic_search)

# Retrieve based on intent
from conversational.query_understanding import QueryResult, QueryIntent

query_result = QueryResult(
    intent=QueryIntent.SEARCH_ENTITY,
    entities=['Luo Xinghan'],
    keywords=[],
    time_constraint=None,
    filters={'importance_min': 0.7},
    resolved_query="Who is Luo Xinghan?",
    confidence=0.9,
    metadata={}
)

results = retriever.retrieve(query_result, top_k=5)

for r in results:
    print(f"[{r.item_type}] {r.item_id}: {r.score:.2f}")
    print(f"  Matched by: {r.matched_by}")
    print(f"  Content: {r.content.get('merged_text', '')[:100]}...")
```

---

## 🧪 测试计划

### QueryUnderstanding Tests

```python
def test_intent_classification():
    """Test intent recognition"""
    queries = [
        ("What is this video about?", QueryIntent.SUMMARY),
        ("Who is Luo Xinghan?", QueryIntent.SEARCH_ENTITY),
        ("Relationship between X and Y?", QueryIntent.SEARCH_RELATION),
        ("Show me clips for TikTok", QueryIntent.RECOMMEND_CLIP)
    ]

    for query, expected_intent in queries:
        result = understander.parse(query)
        assert result.intent == expected_intent

def test_entity_extraction():
    """Test entity extraction"""
    result = understander.parse("Tell me about Luo Xinghan and Kun Sa")
    assert 'Luo Xinghan' in result.entities
    assert 'Kun Sa' in result.entities

def test_coreference_resolution():
    """Test pronoun resolution"""
    # First query
    result1 = understander.parse("Who is Luo Xinghan?", session_id)
    context_manager.update_focus_entities(session_id, result1.entities)

    # Second query with pronoun
    result2 = understander.parse("What happened to him?", session_id)
    assert 'Luo Xinghan' in result2.entities  # Resolved from context
```

### HybridRetriever Tests

```python
def test_vector_search_strategy():
    """Test vector similarity search"""
    query_result = QueryResult(intent=QueryIntent.SEARCH_SEMANTIC, ...)
    results = retriever.retrieve(query_result, top_k=5)

    assert len(results) <= 5
    assert all(r.score > 0 for r in results)
    assert 'vector_search' in [r.matched_by for r in results]

def test_entity_index_strategy():
    """Test entity index search"""
    query_result = QueryResult(
        intent=QueryIntent.SEARCH_ENTITY,
        entities=['Luo Xinghan'],
        ...
    )
    results = retriever.retrieve(query_result)

    assert len(results) > 0
    assert any('Luo Xinghan' in r.content.get('merged_text', '')
               for r in results)

def test_strategy_selection():
    """Test correct strategy selection"""
    # SUMMARY intent should use narrative_segments
    intent = QueryIntent.SUMMARY
    strategies = retriever._select_strategies(intent)
    assert 'narrative_segments' in strategies

    # SEARCH_ENTITY should use entity_index
    intent = QueryIntent.SEARCH_ENTITY
    strategies = retriever._select_strategies(intent)
    assert 'entity_index' in strategies

def test_result_deduplication():
    """Test merging removes duplicates"""
    # Create duplicate results
    results = [
        RetrievalResult(item_id='atom_1', score=0.8, ...),
        RetrievalResult(item_id='atom_1', score=0.9, ...),  # Higher score
        RetrievalResult(item_id='atom_2', score=0.7, ...)
    ]

    merged = retriever._merge_results(results)
    assert len(merged) == 2  # Only 2 unique items
    assert merged[0].item_id == 'atom_1'
    assert merged[0].score == 0.9  # Kept higher score

def test_filter_application():
    """Test query filters"""
    query_result = QueryResult(
        filters={'importance_min': 0.8},
        ...
    )
    results = retriever.retrieve(query_result)

    # All results should meet importance threshold
    assert all(r.content.get('importance_score', 0) >= 0.8
               for r in results)
```

---

## ⚡ 性能优化

### 1. 缓存策略
```python
from functools import lru_cache

class HybridRetriever:
    @lru_cache(maxsize=100)
    def _cached_vector_search(self, query_hash):
        """Cache vector search results"""
        pass
```

### 2. 并发检索
```python
from concurrent.futures import ThreadPoolExecutor

def retrieve(self, query_result, top_k=5):
    strategies = self._select_strategies(query_result.intent)

    # Execute strategies in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(self._execute_strategy, s, query_result)
            for s in strategies
        ]
        all_results = []
        for future in futures:
            all_results.extend(future.result())

    # Merge and return
    return self._merge_results(all_results)[:top_k]
```

### 3. 早停机制
```python
def retrieve(self, query_result, top_k=5):
    # If first strategy returns enough high-quality results, skip others
    first_results = self._execute_strategy(strategies[0], query_result)

    if len(first_results) >= top_k and all(r.score > 0.85 for r in first_results[:top_k]):
        return first_results[:top_k]  # Early return

    # Otherwise, execute all strategies
    ...
```

---

## 📊 验收标准

### Day 2 Checklist

- [ ] QueryUnderstanding 实现完成 (~250行)
- [ ] HybridRetriever 实现完成 (~400行)
- [ ] 意图识别准确率 >85% (手动测试20个查询)
- [ ] 检索召回率 >80% (vector search top-5)
- [ ] 平均检索延迟 <500ms
- [ ] 单元测试覆盖率 >80%
- [ ] 端到端测试通过

### 测试案例

**Case 1: 实体查询**
```
Query: "Who is Luo Xinghan?"
Expected:
  - Intent: SEARCH_ENTITY
  - Entities: ['Luo Xinghan']
  - Results: 至少5个相关原子
  - Latency: <500ms
```

**Case 2: 关系查询**
```
Query: "What is the relationship between Luo Xinghan and Kun Sa?"
Expected:
  - Intent: SEARCH_RELATION
  - Entities: ['Luo Xinghan', 'Kun Sa']
  - Results: 包含关系类型和权重
  - Matched by: graph_query
```

**Case 3: 上下文对话**
```
Query 1: "Who is Luo Xinghan?"
Query 2: "What happened to him later?"
Expected:
  - Query 2 resolved entities: ['Luo Xinghan']
  - Query 2 resolved_query: "What happened to Luo Xinghan later?"
```

**Case 4: 创作推荐**
```
Query: "Show me clips suitable for TikTok"
Expected:
  - Intent: RECOMMEND_CLIP
  - Matched by: creative_angles
  - Results: 带有 suitability_score 和 recommended_platforms
```

---

## 🎯 下一步 (Day 3)

1. **ResponseGenerator** - 生成自然语言回答
2. **ConversationalInterface** - 主编排逻辑
3. **CLI** - 命令行交互界面
4. **端到端测试**

---

**文档状态**: 设计完成，待实现
**预计完成时间**: Day 2 结束
**下次更新**: 实现完成后
