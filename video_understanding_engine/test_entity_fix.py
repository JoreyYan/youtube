#!/usr/bin/env python3
"""
测试entity_extractor修复后的实体-原子映射
"""

import json
from pathlib import Path
from collections import defaultdict

def test_entity_mapping():
    """测试实体映射修复"""
    data_dir = Path('data/output_pipeline_v3')

    # 1. 加载atoms
    atoms = []
    atom_texts = {}

    with open(data_dir / 'atoms.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            atom = json.loads(line.strip())
            atoms.append(atom)
            atom_texts[atom['atom_id']] = atom['merged_text']

    print(f"加载了 {len(atoms)} 个原子")

    # 2. 直接测试实体在原子中的分布
    test_entities = ['毛泽东', '孙中山', '坤沙', '罗星汉']

    for entity_name in test_entities:
        found_atoms = []

        # 搜索包含该实体的所有原子
        for atom_id, atom_text in atom_texts.items():
            if entity_name in atom_text:
                found_atoms.append(atom_id)

        print(f"\n实体 '{entity_name}':")
        print(f"  实际出现在原子: {found_atoms}")
        print(f"  总出现次数: {len(found_atoms)}")

        # 显示前3个原子的内容片段
        for i, atom_id in enumerate(found_atoms[:3]):
            atom_text = atom_texts[atom_id]
            snippet = atom_text[:100] + "..." if len(atom_text) > 100 else atom_text
            print(f"  原子 {atom_id}: {snippet}")

    # 3. 生成修复后的实体映射（模拟entity_extractor._recalculate_mentions_from_atoms）
    print(f"\n=== 生成修复后的实体映射 ===")

    # 简化的实体聚合结构
    entities_agg = {
        "persons": defaultdict(lambda: {
            "name": "",
            "mentions": 0,
            "atoms": set(),
            "segments": [],
            "context": set()
        })
    }

    # 使用entity_extractor进行正确的实体匹配
    from analyzers.entity_extractor import EntityExtractor
    entity_extractor = EntityExtractor()

    # 为测试实体重新计算正确的原子映射
    for entity_name in test_entities:
        # 标准化实体名称
        normalized_name = entity_extractor._normalize_entity_name(entity_name, "persons")

        # 重置
        entity_data = entities_agg["persons"][normalized_name]
        entity_data["name"] = normalized_name
        entity_data["mentions"] = 0
        entity_data["atoms"].clear()

        # 遍历所有原子，使用增强匹配算法
        for atom_id, atom_text in atom_texts.items():
            if entity_extractor._enhanced_entity_match(normalized_name, atom_text):
                # 计算在该原子中的出现次数，考虑所有变体
                count_in_atom = 0

                # 搜索实体名本身
                count_in_atom += atom_text.count(normalized_name)

                # 检查毛泽东/毛主席别名
                if normalized_name == "毛主席":
                    count_in_atom += atom_text.count("毛泽东")
                elif normalized_name == "毛泽东":
                    count_in_atom += atom_text.count("毛主席")

                # 检查字符变体
                if "星" in normalized_name:
                    variant = normalized_name.replace("星", "兴")
                    count_in_atom += atom_text.count(variant)
                elif "兴" in normalized_name:
                    variant = normalized_name.replace("兴", "星")
                    count_in_atom += atom_text.count(variant)

                if count_in_atom > 0:
                    entity_data["atoms"].add(atom_id)
                    entity_data["mentions"] += count_in_atom

    # 4. 输出修复结果
    for entity_name in test_entities:
        # 获取标准化名称
        normalized_name = entity_extractor._normalize_entity_name(entity_name, "persons")
        entity_data = entities_agg["persons"][normalized_name]
        atoms_list = sorted(list(entity_data["atoms"]))

        print(f"\n修复后的 '{entity_name}' (标准化为: '{normalized_name}'):")
        print(f"  映射到原子: {atoms_list}")
        print(f"  提及次数: {entity_data['mentions']}")

    # 5. 保存修复后的测试结果
    test_result = {}
    for entity_type, entities in entities_agg.items():
        test_result[entity_type] = []
        for entity_data in entities.values():
            if entity_data["atoms"]:  # 只保存有原子的实体
                test_result[entity_type].append({
                    "name": entity_data["name"],
                    "mentions": entity_data["mentions"],
                    "atoms": sorted(list(entity_data["atoms"])),
                    "segments": list(entity_data["segments"]),
                    "context": list(entity_data["context"])
                })

    # 保存测试结果
    output_file = data_dir / 'entities_test_fixed.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_result, f, ensure_ascii=False, indent=2)

    print(f"\n修复后的测试结果已保存到: {output_file}")

if __name__ == "__main__":
    test_entity_mapping()