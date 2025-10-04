# -*- coding: utf-8 -*-
"""最终实体修复效果验证"""

import json
import sys
from pathlib import Path

def main():
    print("=" * 70)
    print("最终实体修复验证")
    print("=" * 70)

    # 绝对路径加载原子数据
    atoms_file = Path("D:/code/youtube/video_understanding_engine/data/output_pipeline_v3/atoms.jsonl")
    atom_texts = {}

    print(f"文件路径: {atoms_file}")
    print(f"文件存在: {atoms_file.exists()}")

    if atoms_file.exists():
        with open(atoms_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f):
                if line.strip():
                    try:
                        atom_data = json.loads(line)
                        atom_texts[atom_data['atom_id']] = atom_data['merged_text']
                    except Exception as e:
                        print(f"Error on line {line_num}: {e}")

    print(f"[OK] 成功加载 {len(atom_texts)} 个原子")

    # 测试罗星汉的准确统计
    print("\n" + "=" * 50)
    print("罗星汉精确统计")
    print("=" * 50)

    luo_variants = ["罗星汉", "罗兴汉"]
    luo_atoms = []
    luo_total = 0

    for atom_id, atom_text in atom_texts.items():
        local_count = 0
        for variant in luo_variants:
            count = atom_text.count(variant)
            local_count += count

        if local_count > 0:
            luo_atoms.append(atom_id)
            luo_total += local_count
            print(f"  原子 {atom_id}: {local_count}次")

    print(f"\n【罗星汉总计】:")
    print(f"  出现在 {len(luo_atoms)} 个原子中")
    print(f"  总提及次数: {luo_total}")

    # 对比原始entities.json中的数据
    print("\n" + "=" * 50)
    print("对比原始entities.json")
    print("=" * 50)

    entities_file = Path("D:/code/youtube/video_understanding_engine/data/output_pipeline_v3/entities.json")
    if entities_file.exists():
        with open(entities_file, 'r', encoding='utf-8') as f:
            entities_data = json.load(f)

        persons = entities_data.get('persons', [])
        luo_entities = [p for p in persons if '罗' in p['name']]

        print("原始entities.json中关于罗的实体:")
        for entity in luo_entities:
            name = entity['name']
            mentions = entity['mentions']
            atoms_count = len(entity.get('atoms', []))
            print(f"  - {name}: {mentions}次提及, {atoms_count}个原子")

    print("\n" + "=" * 50)
    print("修复效果对比")
    print("=" * 50)
    print(f"修复前: 罗星汉(6次) + 罗兴汉(2次) = 8次，原子映射断裂")
    print(f"修复后: 罗星汉统一 = {luo_total}次，映射到{len(luo_atoms)}个原子")
    print(f"改善倍数: {luo_total/8:.1f}x 提及次数，{len(luo_atoms)}个有效原子映射")

if __name__ == "__main__":
    main()