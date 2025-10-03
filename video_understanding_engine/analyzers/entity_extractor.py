"""
EntityExtractor - 实体提取聚合器
从所有叙事片段中提取和聚合实体信息
"""

import json
from typing import List, Dict, Any
from pathlib import Path
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import NarrativeSegment
from utils import setup_logger

logger = setup_logger(__name__)


class EntityExtractor:
    """实体提取聚合器"""

    def extract(self, segments: List[NarrativeSegment], atoms: List = None) -> Dict[str, Any]:
        """
        从所有片段中提取并聚合实体

        Args:
            segments: 叙事片段列表
            atoms: 原子列表（用于精确定位实体所在的原子）

        Returns:
            实体聚合结果字典
        """
        logger.info(f"开始提取实体，共{len(segments)}个片段")

        # 初始化实体字典
        entities_agg = {
            "persons": defaultdict(lambda: {
                "name": "",
                "mentions": 0,
                "segments": [],
                "atoms": set(),
                "context": set()
            }),
            "countries": defaultdict(lambda: {
                "name": "",
                "mentions": 0,
                "segments": [],
                "atoms": set(),
                "context": set()
            }),
            "organizations": defaultdict(lambda: {
                "name": "",
                "mentions": 0,
                "segments": [],
                "atoms": set(),
                "context": set()
            }),
            "time_points": defaultdict(lambda: {
                "name": "",
                "mentions": 0,
                "segments": [],
                "atoms": set(),
                "context": set()
            }),
            "events": defaultdict(lambda: {
                "name": "",
                "mentions": 0,
                "segments": [],
                "atoms": set(),
                "context": set()
            }),
            "concepts": defaultdict(lambda: {
                "name": "",
                "mentions": 0,
                "segments": [],
                "atoms": set(),
                "context": set()
            })
        }

        # 构建atom_id -> text映射（用于查找实体）
        atom_texts = {}
        if atoms:
            for atom in atoms:
                atom_texts[atom.atom_id] = atom.merged_text

        # 遍历所有片段
        for segment in segments:
            segment_id = segment.segment_id
            entities = segment.entities

            # 对每个实体类型进行处理
            entity_types = [
                ("persons", entities.persons),
                ("countries", entities.countries),
                ("organizations", entities.organizations),
                ("time_points", entities.time_points),
                ("events", entities.events),
                ("concepts", entities.concepts)
            ]

            for entity_type, entity_list in entity_types:
                for entity_name in entity_list:
                    entities_agg[entity_type][entity_name]["name"] = entity_name
                    entities_agg[entity_type][entity_name]["mentions"] += 1
                    entities_agg[entity_type][entity_name]["segments"].append(segment_id)

                    # 找到包含该实体的具体原子
                    if atom_texts:
                        for atom_id in segment.atoms:
                            if atom_id in atom_texts:
                                atom_text = atom_texts[atom_id]
                                # 检查实体名称是否在原子文本中
                                if entity_name in atom_text:
                                    entities_agg[entity_type][entity_name]["atoms"].add(atom_id)

                    # 添加上下文（从片段主题）
                    if segment.topics.primary_topic:
                        entities_agg[entity_type][entity_name]["context"].add(segment.topics.primary_topic)

        # 转换为最终格式
        result = self._format_entities(entities_agg)

        logger.info(f"实体提取完成:")
        logger.info(f"  人物: {len(result['persons'])}个")
        logger.info(f"  国家: {len(result['countries'])}个")
        logger.info(f"  组织: {len(result['organizations'])}个")
        logger.info(f"  时间点: {len(result['time_points'])}个")
        logger.info(f"  事件: {len(result['events'])}个")
        logger.info(f"  概念: {len(result['concepts'])}个")

        return result

    def _format_entities(self, entities_agg: Dict) -> Dict[str, Any]:
        """格式化实体数据"""
        result = {}

        for entity_type, entities in entities_agg.items():
            formatted_entities = []
            for entity_data in entities.values():
                # 对atoms进行排序（按atom_id）
                atoms_list = sorted(list(entity_data["atoms"]))

                formatted_entities.append({
                    "name": entity_data["name"],
                    "mentions": entity_data["mentions"],
                    "segments": list(set(entity_data["segments"])),  # 去重
                    "atoms": atoms_list,  # 已排序的原子列表
                    "context": list(entity_data["context"]),  # 转为列表
                    "related_entities": []  # 后续可扩展
                })

            # 按提及次数排序
            formatted_entities.sort(key=lambda x: x["mentions"], reverse=True)
            result[entity_type] = formatted_entities

        # 添加统计信息
        result["statistics"] = {
            "total_entities": sum(len(entities) for entities in result.values() if isinstance(entities, list)),
            "by_type": {
                entity_type: len(entities)
                for entity_type, entities in result.items()
                if isinstance(entities, list)
            }
        }

        return result

    def save(self, entities: Dict[str, Any], output_path: Path):
        """保存实体数据到文件"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(entities, f, ensure_ascii=False, indent=2)
        logger.info(f"实体数据已保存到: {output_path}")
