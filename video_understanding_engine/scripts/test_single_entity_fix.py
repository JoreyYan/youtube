# -*- coding: utf-8 -*-
"""测试单个实体的修复效果 - 直接处理现有数据"""

import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers.entity_extractor import EntityExtractor

def main():
    print("=" * 70)
    print("测试单个实体修复效果")
    print("=" * 70)

    # 加载原子数据
    atoms_file = Path("data/output_pipeline_v3/atoms.jsonl")
    atom_texts = {}

    if atoms_file.exists():
        with open(atoms_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    atom_data = json.loads(line)
                    atom_texts[atom_data['atom_id']] = atom_data['merged_text']

    print(f"[OK] 加载了 {len(atom_texts)} 个原子的文本")

    if len(atom_texts) < 300:
        print(f"[WARNING] 原子数量异常少，预期应该有342个")
        print(f"文件路径: {atoms_file.absolute()}")
        print(f"文件存在: {atoms_file.exists()}")

    # 创建测试实体提取器
    extractor = EntityExtractor()

    # 测试"罗星汉"实体
    test_entities = ["罗星汉", "罗兴汉", "坤沙", "张奇夫", "昆沙"]

    print("\n" + "=" * 70)
    print("实体匹配测试")
    print("=" * 70)

    for entity_name in test_entities:
        print(f"\n测试实体: {entity_name}")
        matched_atoms = []
        total_mentions = 0

        # 遍历所有原子，查找匹配
        for atom_id, atom_text in atom_texts.items():
            if extractor._enhanced_entity_match(entity_name, atom_text):
                matched_atoms.append(atom_id)
                # 计算在此原子中的出现次数
                count = atom_text.count(entity_name)
                # 也检查字符变体
                if "星" in entity_name:
                    variant = entity_name.replace("星", "兴")
                    count += atom_text.count(variant)
                elif "兴" in entity_name:
                    variant = entity_name.replace("兴", "星")
                    count += atom_text.count(variant)

                total_mentions += count
                if count > 0:
                    print(f"  - 原子 {atom_id}: {count}次")

        print(f"  总计: 出现在 {len(matched_atoms)} 个原子中，共 {total_mentions} 次提及")

    # 测试别名标准化
    print("\n" + "=" * 70)
    print("别名标准化测试")
    print("=" * 70)

    alias_tests = [
        ("罗兴汉", "persons"),
        ("罗兴汉投降", "persons"),
        ("张奇夫", "persons"),
        ("张奇夫(昆沙)", "persons"),
        ("坤沙(张奇夫)", "persons")
    ]

    for original_name, entity_type in alias_tests:
        core_entity = extractor._extract_entity_from_compound(original_name)
        normalized = extractor._normalize_entity_name(core_entity, entity_type)
        print(f"{original_name} -> {core_entity} -> {normalized}")

    # 手动计算罗星汉的准确数据
    print("\n" + "=" * 70)
    print("罗星汉精确统计")
    print("=" * 70)

    luo_variants = ["罗星汉", "罗兴汉"]
    luo_atoms = []
    luo_total = 0

    for atom_id, atom_text in atom_texts.items():
        found = False
        local_count = 0
        for variant in luo_variants:
            count = atom_text.count(variant)
            if count > 0:
                local_count += count
                found = True

        if found:
            luo_atoms.append(atom_id)
            luo_total += local_count
            print(f"  原子 {atom_id}: {local_count}次")

    print(f"\n罗星汉总计:")
    print(f"  出现在 {len(luo_atoms)} 个原子中")
    print(f"  总提及次数: {luo_total}")
    print(f"  原子列表: {', '.join(luo_atoms[:10])}{'...' if len(luo_atoms) > 10 else ''}")

    print("\n测试完成!")

if __name__ == "__main__":
    main()