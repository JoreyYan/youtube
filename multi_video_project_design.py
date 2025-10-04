#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多视频项目管理设计原型
处理项目内多个视频的数据合并与关联
"""

import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import uuid
from datetime import datetime

@dataclass
class VideoAtom:
    """单个视频的原子数据"""
    atom_id: str  # 格式: {video_id}_A{number}
    video_id: str
    start_time: str
    end_time: str
    duration_seconds: float
    merged_text: str
    original_segments: List[dict]

@dataclass
class ProjectEntity:
    """项目级别的实体（可能跨多个视频）"""
    entity_id: str
    name: str
    type: str
    category: str

    # 跨视频数据
    video_appearances: Dict[str, List[str]]  # video_id -> [atom_ids]
    total_mentions: int
    confidence_score: float  # 实体合并的置信度

    # 元数据
    first_appearance: str  # 首次出现的视频ID
    last_appearance: str   # 最后出现的视频ID

@dataclass
class ProjectVideo:
    """项目中的单个视频信息"""
    video_id: str
    filename: str
    duration: float
    upload_time: datetime
    processing_status: str

    # 处理结果
    atoms: List[VideoAtom]
    local_entities: Dict[str, dict]  # 视频内部实体
    vectors: Dict[str, List[float]]  # atom_id -> embedding

class MultiVideoProjectManager:
    """多视频项目管理器"""

    def __init__(self, project_id: str, base_path: str):
        self.project_id = project_id
        self.base_path = Path(base_path)
        self.project_path = self.base_path / project_id
        self.project_path.mkdir(exist_ok=True)

        # 子目录结构
        self.videos_path = self.project_path / "videos"
        self.merged_path = self.project_path / "merged"
        self.videos_path.mkdir(exist_ok=True)
        self.merged_path.mkdir(exist_ok=True)

    def add_video(self, video_file: str) -> str:
        """添加新视频到项目"""
        video_id = f"v{int(datetime.now().timestamp())}"

        # 1. 处理单个视频（保持独立）
        video_data = self._process_single_video(video_file, video_id)

        # 2. 保存视频数据
        self._save_video_data(video_id, video_data)

        # 3. 触发项目级合并
        self._merge_project_data()

        return video_id

    def _process_single_video(self, video_file: str, video_id: str) -> ProjectVideo:
        """处理单个视频（模拟现有pipeline）"""
        print(f"Processing video {video_id}: {video_file}")

        # 模拟原子创建（带视频ID前缀）
        atoms = []
        for i in range(1, 101):  # 模拟100个原子
            atom = VideoAtom(
                atom_id=f"{video_id}_A{i:03d}",
                video_id=video_id,
                start_time=f"{i*3}s",
                end_time=f"{(i+1)*3}s",
                duration_seconds=3.0,
                merged_text=f"这是视频{video_id}的第{i}个片段内容...",
                original_segments=[]
            )
            atoms.append(atom)

        # 模拟实体提取
        local_entities = self._extract_video_entities(atoms, video_id)

        # 模拟向量化
        vectors = self._create_video_vectors(atoms)

        return ProjectVideo(
            video_id=video_id,
            filename=video_file,
            duration=300.0,
            upload_time=datetime.now(),
            processing_status="completed",
            atoms=atoms,
            local_entities=local_entities,
            vectors=vectors
        )

    def _extract_video_entities(self, atoms: List[VideoAtom], video_id: str) -> Dict[str, dict]:
        """从视频原子中提取实体（模拟）"""
        entities = {}

        # 模拟实体提取结果
        sample_entities = ["罗星汉", "北京", "会议", "项目"]

        for entity_name in sample_entities:
            # 模拟该实体出现的原子
            appearing_atoms = [atom.atom_id for atom in atoms[::10]]  # 每10个原子出现一次

            entities[entity_name] = {
                "name": entity_name,
                "type": "person" if entity_name == "罗星汉" else "location",
                "atom_ids": appearing_atoms,
                "mentions": len(appearing_atoms),
                "video_id": video_id
            }

        return entities

    def _create_video_vectors(self, atoms: List[VideoAtom]) -> Dict[str, List[float]]:
        """为原子创建向量（模拟）"""
        vectors = {}
        for atom in atoms:
            # 模拟768维向量
            vectors[atom.atom_id] = [0.1] * 768
        return vectors

    def _save_video_data(self, video_id: str, video_data: ProjectVideo):
        """保存单个视频的处理结果"""
        video_file = self.videos_path / f"{video_id}.json"

        # 转换为可序列化格式
        data = {
            "video_id": video_data.video_id,
            "filename": video_data.filename,
            "duration": video_data.duration,
            "upload_time": video_data.upload_time.isoformat(),
            "processing_status": video_data.processing_status,
            "atoms": [
                {
                    "atom_id": atom.atom_id,
                    "video_id": atom.video_id,
                    "start_time": atom.start_time,
                    "end_time": atom.end_time,
                    "duration_seconds": atom.duration_seconds,
                    "merged_text": atom.merged_text
                }
                for atom in video_data.atoms
            ],
            "local_entities": video_data.local_entities,
            "vectors": video_data.vectors
        }

        with open(video_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _merge_project_data(self):
        """合并项目内所有视频数据"""
        print(f"Merging data for project {self.project_id}")

        # 1. 加载所有视频数据
        all_videos = self._load_all_videos()

        # 2. 合并实体
        merged_entities = self._merge_entities(all_videos)

        # 3. 创建跨视频关系
        cross_relationships = self._find_cross_relationships(all_videos, merged_entities)

        # 4. 保存合并结果
        self._save_merged_data(merged_entities, cross_relationships)

    def _load_all_videos(self) -> List[dict]:
        """加载项目内所有视频数据"""
        videos = []
        for video_file in self.videos_path.glob("*.json"):
            with open(video_file, 'r', encoding='utf-8') as f:
                videos.append(json.load(f))
        return videos

    def _merge_entities(self, all_videos: List[dict]) -> Dict[str, ProjectEntity]:
        """合并跨视频实体"""
        entity_groups = {}  # entity_name -> ProjectEntity

        for video in all_videos:
            video_id = video["video_id"]

            for entity_name, entity_data in video["local_entities"].items():
                if entity_name not in entity_groups:
                    # 创建新的项目实体
                    entity_groups[entity_name] = ProjectEntity(
                        entity_id=f"e_{uuid.uuid4().hex[:8]}",
                        name=entity_name,
                        type=entity_data["type"],
                        category=entity_data.get("category", "unknown"),
                        video_appearances={},
                        total_mentions=0,
                        confidence_score=1.0,
                        first_appearance=video_id,
                        last_appearance=video_id
                    )

                # 添加视频出现记录
                project_entity = entity_groups[entity_name]
                project_entity.video_appearances[video_id] = entity_data["atom_ids"]
                project_entity.total_mentions += entity_data["mentions"]
                project_entity.last_appearance = video_id

        return entity_groups

    def _find_cross_relationships(self, all_videos: List[dict], entities: Dict[str, ProjectEntity]) -> List[dict]:
        """发现跨视频关系"""
        relationships = []

        # 示例：如果两个实体在多个视频中都出现，创建关系
        entity_pairs = []
        entity_names = list(entities.keys())

        for i in range(len(entity_names)):
            for j in range(i+1, len(entity_names)):
                entity_a = entities[entity_names[i]]
                entity_b = entities[entity_names[j]]

                # 检查是否在同一视频中出现
                common_videos = set(entity_a.video_appearances.keys()) & set(entity_b.video_appearances.keys())

                if len(common_videos) >= 2:  # 在至少2个视频中都出现
                    relationships.append({
                        "source": entity_a.entity_id,
                        "target": entity_b.entity_id,
                        "relation": "co_appears_across_videos",
                        "common_videos": list(common_videos),
                        "strength": len(common_videos)
                    })

        return relationships

    def _save_merged_data(self, entities: Dict[str, ProjectEntity], relationships: List[dict]):
        """保存项目合并数据"""
        # 保存合并实体
        entities_file = self.merged_path / "entities.json"
        entities_data = {}
        for name, entity in entities.items():
            entities_data[name] = {
                "entity_id": entity.entity_id,
                "name": entity.name,
                "type": entity.type,
                "category": entity.category,
                "video_appearances": entity.video_appearances,
                "total_mentions": entity.total_mentions,
                "confidence_score": entity.confidence_score,
                "first_appearance": entity.first_appearance,
                "last_appearance": entity.last_appearance
            }

        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(entities_data, f, ensure_ascii=False, indent=2)

        # 保存关系
        relationships_file = self.merged_path / "relationships.json"
        with open(relationships_file, 'w', encoding='utf-8') as f:
            json.dump(relationships, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(entities)} merged entities and {len(relationships)} cross-video relationships")

    def get_project_summary(self) -> dict:
        """获取项目摘要"""
        all_videos = self._load_all_videos()

        # 加载合并数据
        entities_file = self.merged_path / "entities.json"
        relationships_file = self.merged_path / "relationships.json"

        merged_entities = {}
        relationships = []

        if entities_file.exists():
            with open(entities_file, 'r', encoding='utf-8') as f:
                merged_entities = json.load(f)

        if relationships_file.exists():
            with open(relationships_file, 'r', encoding='utf-8') as f:
                relationships = json.load(f)

        return {
            "project_id": self.project_id,
            "videos_count": len(all_videos),
            "total_atoms": sum(len(v["atoms"]) for v in all_videos),
            "unique_entities": len(merged_entities),
            "cross_video_relationships": len(relationships),
            "videos": [
                {
                    "video_id": v["video_id"],
                    "filename": v["filename"],
                    "atoms_count": len(v["atoms"]),
                    "local_entities_count": len(v["local_entities"])
                }
                for v in all_videos
            ]
        }

# 使用示例
def main():
    # 创建项目管理器
    manager = MultiVideoProjectManager("project_001", "D:/code/youtube/projects")

    # 添加第一个视频
    print("=== 添加第一个视频 ===")
    video1_id = manager.add_video("video1.mp4")
    print(f"Video 1 ID: {video1_id}")

    # 添加第二个视频
    print("\n=== 添加第二个视频 ===")
    video2_id = manager.add_video("video2.mp4")
    print(f"Video 2 ID: {video2_id}")

    # 获取项目摘要
    print("\n=== 项目摘要 ===")
    summary = manager.get_project_summary()
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()