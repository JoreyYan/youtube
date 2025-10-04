# -*- coding: utf-8 -*-
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
