"""
QdrantVectorStore - Qdrant 向量存储封装

支持原子级和片段级的向量存储与检索
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, Range
)
import uuid


class QdrantVectorStore:
    """Qdrant 向量存储"""

    def __init__(
        self,
        location: str = ":memory:",  # ":memory:" 或 "http://localhost:6333"
        collection_name: str = "vectors"
    ):
        """
        初始化向量存储

        Args:
            location: Qdrant位置（:memory: 表示内存模式）
            collection_name: collection名称
        """
        self.client = QdrantClient(location=location)
        self.collection_name = collection_name
        self.dimension = None

    def create_collection(
        self,
        dimension: int,
        distance: str = "Cosine",
        recreate: bool = False
    ):
        """
        创建collection

        Args:
            dimension: 向量维度
            distance: 距离度量（Cosine/Euclid/Dot）
            recreate: 是否重新创建（删除已存在的）
        """
        self.dimension = dimension

        # 检查是否已存在
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if exists and recreate:
            self.client.delete_collection(self.collection_name)
            exists = False

        if not exists:
            # 映射距离度量
            distance_map = {
                "Cosine": Distance.COSINE,
                "Euclid": Distance.EUCLID,
                "Dot": Distance.DOT
            }

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=distance_map.get(distance, Distance.COSINE)
                )
            )

    def insert_atoms(
        self,
        atoms: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> int:
        """
        插入原子向量

        Args:
            atoms: 原子列表（字典格式）
            embeddings: 对应的向量列表

        Returns:
            插入的数量
        """
        if len(atoms) != len(embeddings):
            raise ValueError(f"原子数量({len(atoms)})与向量数量({len(embeddings)})不匹配")

        points = []
        for atom, embedding in zip(atoms, embeddings):
            points.append(PointStruct(
                id=str(uuid.uuid4()),  # 使用UUID作为内部ID
                vector=embedding,
                payload={
                    "atom_id": atom.get("atom_id"),
                    "text": atom.get("merged_text", ""),
                    "type": atom.get("type", ""),
                    "start_ms": atom.get("start_ms", 0),
                    "end_ms": atom.get("end_ms", 0),
                    "duration_seconds": atom.get("duration_seconds", 0),
                    "completeness": atom.get("completeness", ""),
                    "data_type": "atom"  # 标记数据类型
                }
            ))

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        return len(points)

    def insert_segments(
        self,
        segments: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> int:
        """
        插入片段向量

        Args:
            segments: 片段列表（字典格式）
            embeddings: 对应的向量列表

        Returns:
            插入的数量
        """
        if len(segments) != len(embeddings):
            raise ValueError(f"片段数量({len(segments)})与向量数量({len(embeddings)})不匹配")

        points = []
        for segment, embedding in zip(segments, embeddings):
            # 提取主题标签
            topics = segment.get("topics", {})
            free_tags = topics.get("free_tags", []) if isinstance(topics, dict) else []

            # 提取实体
            entities = segment.get("entities", {})
            persons = entities.get("persons", []) if isinstance(entities, dict) else []
            events = entities.get("events", []) if isinstance(entities, dict) else []

            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "segment_id": segment.get("segment_id"),
                    "title": segment.get("title", ""),
                    "summary": segment.get("summary", ""),
                    "full_text": segment.get("full_text", ""),
                    "start_ms": segment.get("start_ms", 0),
                    "end_ms": segment.get("end_ms", 0),
                    "duration_minutes": segment.get("duration_minutes", 0),
                    "primary_topic": topics.get("primary_topic", ""),
                    "free_tags": free_tags,
                    "persons": persons,
                    "events": events,
                    "importance_score": segment.get("importance_score", 0.5),
                    "quality_score": segment.get("quality_score", 0.5),
                    "data_type": "segment"  # 标记数据类型
                }
            ))

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        return len(points)

    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        向量搜索

        Args:
            query_vector: 查询向量
            limit: 返回结果数量
            filters: 过滤条件
            score_threshold: 相似度阈值

        Returns:
            搜索结果列表
        """
        # 构建过滤器
        qdrant_filter = self._build_filter(filters) if filters else None

        # 执行搜索
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
            score_threshold=score_threshold
        )

        # 格式化结果
        formatted_results = []
        for hit in results:
            formatted_results.append({
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            })

        return formatted_results

    def delete_by_filter(self, filters: Dict[str, Any]) -> int:
        """
        根据过滤条件删除

        Args:
            filters: 过滤条件

        Returns:
            删除的数量（估计值）
        """
        qdrant_filter = self._build_filter(filters)

        # Qdrant 不直接返回删除数量，需要先查询
        points = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=qdrant_filter,
            limit=10000  # 假设不会超过这个数量
        )[0]

        if points:
            point_ids = [p.id for p in points]
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids
            )
            return len(point_ids)

        return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        获取collection统计信息

        Returns:
            统计字典
        """
        info = self.client.get_collection(self.collection_name)

        return {
            "collection_name": self.collection_name,
            "points_count": info.points_count,
            "vectors_count": info.vectors_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "dimension": self.dimension
        }

    def _build_filter(self, filters: Dict[str, Any]) -> Filter:
        """构建Qdrant过滤器"""
        conditions = []

        # data_type过滤
        if "data_type" in filters:
            conditions.append(
                FieldCondition(
                    key="data_type",
                    match=MatchValue(value=filters["data_type"])
                )
            )

        # atom_id/segment_id 精确匹配
        if "atom_id" in filters:
            conditions.append(
                FieldCondition(
                    key="atom_id",
                    match=MatchValue(value=filters["atom_id"])
                )
            )

        if "segment_id" in filters:
            conditions.append(
                FieldCondition(
                    key="segment_id",
                    match=MatchValue(value=filters["segment_id"])
                )
            )

        # 时间范围过滤
        if "start_ms_gte" in filters:
            conditions.append(
                FieldCondition(
                    key="start_ms",
                    range=Range(gte=filters["start_ms_gte"])
                )
            )

        if "end_ms_lte" in filters:
            conditions.append(
                FieldCondition(
                    key="end_ms",
                    range=Range(lte=filters["end_ms_lte"])
                )
            )

        # 重要性评分过滤
        if "importance_score_gte" in filters:
            conditions.append(
                FieldCondition(
                    key="importance_score",
                    range=Range(gte=filters["importance_score_gte"])
                )
            )

        # 类型过滤
        if "type" in filters:
            conditions.append(
                FieldCondition(
                    key="type",
                    match=MatchValue(value=filters["type"])
                )
            )

        return Filter(must=conditions) if conditions else None

    def clear_collection(self):
        """清空collection"""
        self.client.delete_collection(self.collection_name)
        if self.dimension:
            self.create_collection(self.dimension)
