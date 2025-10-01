"""
SemanticSearchEngine - 语义搜索引擎

提供多种搜索模式：
- 原子级搜索
- 片段级搜索
- 相似度搜索
- 混合搜索（向量+关键词）
"""

from typing import List, Dict, Any, Optional
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embedders.embedding_generator import EmbeddingGenerator
from vectorstores.qdrant_store import QdrantVectorStore


class SemanticSearchEngine:
    """语义搜索引擎"""

    def __init__(
        self,
        vector_store: QdrantVectorStore,
        embedder: EmbeddingGenerator
    ):
        """
        初始化搜索引擎

        Args:
            vector_store: 向量存储实例
            embedder: 向量生成器实例
        """
        self.vector_store = vector_store
        self.embedder = embedder

    def search_atoms(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索原子

        Args:
            query: 查询文本（自然语言）
            limit: 返回结果数量
            filters: 过滤条件（例如：时间范围、类型等）
            score_threshold: 相似度阈值（0-1之间）

        Returns:
            搜索结果列表，每个结果包含：
            - atom_id: 原子ID
            - text: 文本内容
            - score: 相似度分数
            - start_ms/end_ms: 时间范围
            - type: 类型
            - 其他payload字段
        """
        # 生成查询向量
        query_vector = self.embedder.generate_embedding(query)

        # 添加data_type过滤
        search_filters = filters or {}
        search_filters["data_type"] = "atom"

        # 执行搜索
        results = self.vector_store.search(
            query_vector=query_vector,
            limit=limit,
            filters=search_filters,
            score_threshold=score_threshold
        )

        # 格式化结果
        formatted_results = []
        for hit in results:
            payload = hit["payload"]
            formatted_results.append({
                "atom_id": payload.get("atom_id"),
                "text": payload.get("text"),
                "type": payload.get("type"),
                "start_ms": payload.get("start_ms"),
                "end_ms": payload.get("end_ms"),
                "duration_seconds": payload.get("duration_seconds"),
                "completeness": payload.get("completeness"),
                "score": hit["score"],
                "start_time": self._ms_to_time(payload.get("start_ms", 0)),
                "end_time": self._ms_to_time(payload.get("end_ms", 0))
            })

        return formatted_results

    def search_segments(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索片段

        Args:
            query: 查询文本（自然语言）
            limit: 返回结果数量
            filters: 过滤条件
            score_threshold: 相似度阈值

        Returns:
            搜索结果列表，每个结果包含：
            - segment_id: 片段ID
            - title: 标题
            - summary: 摘要
            - score: 相似度分数
            - start_ms/end_ms: 时间范围
            - 其他payload字段
        """
        # 生成查询向量
        query_vector = self.embedder.generate_embedding(query)

        # 添加data_type过滤
        search_filters = filters or {}
        search_filters["data_type"] = "segment"

        # 执行搜索
        results = self.vector_store.search(
            query_vector=query_vector,
            limit=limit,
            filters=search_filters,
            score_threshold=score_threshold
        )

        # 格式化结果
        formatted_results = []
        for hit in results:
            payload = hit["payload"]
            formatted_results.append({
                "segment_id": payload.get("segment_id"),
                "title": payload.get("title"),
                "summary": payload.get("summary"),
                "full_text": payload.get("full_text"),
                "primary_topic": payload.get("primary_topic"),
                "free_tags": payload.get("free_tags", []),
                "persons": payload.get("persons", []),
                "events": payload.get("events", []),
                "start_ms": payload.get("start_ms"),
                "end_ms": payload.get("end_ms"),
                "duration_minutes": payload.get("duration_minutes"),
                "importance_score": payload.get("importance_score"),
                "quality_score": payload.get("quality_score"),
                "score": hit["score"],
                "start_time": self._ms_to_time(payload.get("start_ms", 0)),
                "end_time": self._ms_to_time(payload.get("end_ms", 0))
            })

        return formatted_results

    def find_similar_atoms(
        self,
        atom_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        查找与指定原子相似的其他原子

        Args:
            atom_id: 原子ID
            limit: 返回结果数量

        Returns:
            相似原子列表
        """
        # 先搜索出该原子
        results = self.vector_store.search(
            query_vector=[0.0] * self.embedder.get_dimension(),  # 临时向量 (使用float)
            limit=1,
            filters={"atom_id": atom_id}
        )

        if not results:
            return []

        # 使用该原子的文本生成向量
        atom_text = results[0]["payload"].get("text", "")
        if not atom_text:
            return []

        atom_vector = self.embedder.generate_embedding(atom_text)

        # 搜索相似原子（排除自己）
        similar_results = self.vector_store.search(
            query_vector=atom_vector,
            limit=limit + 1,  # 多取一个以便排除自己
            filters={"data_type": "atom"}
        )

        # 格式化并过滤掉自己
        formatted_results = []
        for hit in similar_results:
            payload = hit["payload"]
            if payload.get("atom_id") == atom_id:
                continue

            formatted_results.append({
                "atom_id": payload.get("atom_id"),
                "text": payload.get("text"),
                "type": payload.get("type"),
                "completeness": payload.get("completeness"),
                "start_ms": payload.get("start_ms"),
                "end_ms": payload.get("end_ms"),
                "duration_seconds": payload.get("duration_seconds"),
                "score": hit["score"],
                "start_time": self._ms_to_time(payload.get("start_ms", 0)),
                "end_time": self._ms_to_time(payload.get("end_ms", 0))
            })

            if len(formatted_results) >= limit:
                break

        return formatted_results

    def find_similar_segments(
        self,
        segment_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        查找与指定片段相似的其他片段

        Args:
            segment_id: 片段ID
            limit: 返回结果数量

        Returns:
            相似片段列表
        """
        # 先搜索出该片段
        results = self.vector_store.search(
            query_vector=[0.0] * self.embedder.get_dimension(),
            limit=1,
            filters={"segment_id": segment_id}
        )

        if not results:
            return []

        # 使用该片段的文本生成向量
        segment_summary = results[0]["payload"].get("summary", "")
        segment_vector = self.embedder.generate_embedding(segment_summary)

        # 搜索相似片段（排除自己）
        similar_results = self.vector_store.search(
            query_vector=segment_vector,
            limit=limit + 1,
            filters={"data_type": "segment"}
        )

        # 格式化并过滤掉自己
        formatted_results = []
        for hit in similar_results:
            payload = hit["payload"]
            if payload.get("segment_id") == segment_id:
                continue

            formatted_results.append({
                "segment_id": payload.get("segment_id"),
                "title": payload.get("title"),
                "summary": payload.get("summary"),
                "primary_topic": payload.get("primary_topic"),
                "score": hit["score"],
                "start_time": self._ms_to_time(payload.get("start_ms", 0)),
                "end_time": self._ms_to_time(payload.get("end_ms", 0))
            })

            if len(formatted_results) >= limit:
                break

        return formatted_results

    def hybrid_search(
        self,
        query: str,
        keywords: List[str],
        limit: int = 10,
        semantic_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        混合搜索：结合语义搜索和关键词匹配

        Args:
            query: 查询文本
            keywords: 关键词列表
            limit: 返回结果数量
            semantic_weight: 语义搜索权重（0-1之间，剩余为关键词权重）

        Returns:
            搜索结果列表
        """
        # 1. 执行语义搜索
        semantic_results = self.search_atoms(query, limit=limit * 2)

        # 2. 关键词匹配评分
        keyword_scores = {}
        for result in semantic_results:
            atom_id = result["atom_id"]
            text = result["text"].lower()

            # 计算关键词匹配度
            matched_keywords = sum(1 for kw in keywords if kw.lower() in text)
            keyword_score = matched_keywords / len(keywords) if keywords else 0

            keyword_scores[atom_id] = keyword_score

        # 3. 混合评分
        for result in semantic_results:
            atom_id = result["atom_id"]
            semantic_score = result["score"]
            keyword_score = keyword_scores.get(atom_id, 0)

            # 加权平均
            hybrid_score = (
                semantic_weight * semantic_score +
                (1 - semantic_weight) * keyword_score
            )

            result["hybrid_score"] = hybrid_score
            result["keyword_score"] = keyword_score
            result["semantic_score"] = semantic_score

        # 4. 按混合分数排序
        semantic_results.sort(key=lambda x: x["hybrid_score"], reverse=True)

        return semantic_results[:limit]

    def search_by_time_range(
        self,
        start_ms: int,
        end_ms: int,
        data_type: str = "atom",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        按时间范围搜索

        Args:
            start_ms: 开始时间（毫秒）
            end_ms: 结束时间（毫秒）
            data_type: 数据类型（atom或segment）
            limit: 返回结果数量

        Returns:
            搜索结果列表
        """
        # 使用零向量（Qdrant会返回所有匹配过滤条件的结果）
        dummy_vector = [0.0] * self.embedder.get_dimension()

        results = self.vector_store.search(
            query_vector=dummy_vector,
            limit=limit,
            filters={
                "data_type": data_type,
                "start_ms_gte": start_ms,
                "end_ms_lte": end_ms
            }
        )

        # 格式化结果
        formatted_results = []
        for hit in results:
            payload = hit["payload"]
            formatted_results.append({
                "id": payload.get(f"{data_type}_id"),
                "text": payload.get("text") or payload.get("summary"),
                "start_ms": payload.get("start_ms"),
                "end_ms": payload.get("end_ms"),
                "start_time": self._ms_to_time(payload.get("start_ms", 0)),
                "end_time": self._ms_to_time(payload.get("end_ms", 0))
            })

        return formatted_results

    def search_by_topic(
        self,
        topic: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        按主题搜索片段

        Args:
            topic: 主题名称
            limit: 返回结果数量

        Returns:
            搜索结果列表
        """
        # 使用主题作为查询进行语义搜索
        return self.search_segments(
            query=topic,
            limit=limit
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        获取搜索引擎统计信息

        Returns:
            统计字典
        """
        vector_stats = self.vector_store.get_stats()
        embedder_stats = self.embedder.get_stats()

        return {
            "vector_store": vector_stats,
            "embedder": embedder_stats
        }

    def _ms_to_time(self, ms: int) -> str:
        """
        毫秒转时间格式

        Args:
            ms: 毫秒数

        Returns:
            格式化时间字符串 (HH:MM:SS)
        """
        hours = ms // 3600000
        minutes = (ms % 3600000) // 60000
        seconds = (ms % 60000) // 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# 便捷函数
def create_search_engine(
    embedder_api_key: str,
    vector_store_location: str = ":memory:",
    collection_name: str = "vectors",
    embedding_model: str = "text-embedding-3-small"
) -> SemanticSearchEngine:
    """
    创建搜索引擎实例

    Args:
        embedder_api_key: OpenAI API密钥
        vector_store_location: 向量存储位置
        collection_name: collection名称
        embedding_model: embedding模型

    Returns:
        SemanticSearchEngine实例
    """
    # 创建embedder
    embedder = EmbeddingGenerator(
        api_key=embedder_api_key,
        model=embedding_model,
        provider='openai'
    )

    # 创建vector store
    vector_store = QdrantVectorStore(
        location=vector_store_location,
        collection_name=collection_name
    )

    # 创建搜索引擎
    search_engine = SemanticSearchEngine(
        vector_store=vector_store,
        embedder=embedder
    )

    return search_engine
