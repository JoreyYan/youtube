# -*- coding: utf-8 -*-
"""测试实体提取修复效果"""

import json
import sys
from pathlib import Path
from dataclasses import asdict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers.entity_extractor import EntityExtractor
from models import NarrativeSegment, Atom

def load_atoms():
    """加载原子数据"""
    atoms_file = Path("data/output_pipeline_v3/atoms.jsonl")
    atoms = []

    if atoms_file.exists():
        with open(atoms_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    atom_data = json.loads(line)
                    atom = Atom(
                        atom_id=atom_data['atom_id'],
                        start_ms=atom_data['start_ms'],
                        end_ms=atom_data['end_ms'],
                        duration_ms=atom_data['duration_ms'],
                        merged_text=atom_data['merged_text'],
                        type=atom_data.get('type', ''),
                        completeness=atom_data.get('completeness', ''),
                        source_utterance_ids=atom_data.get('source_utterance_ids', [])
                    )
                    atoms.append(atom)

    return atoms

def load_segments():
    """加载叙事片段数据"""
    segments_file = Path("data/output_pipeline_v3/narrative_segments.json")
    segments = []

    if segments_file.exists():
        with open(segments_file, 'r', encoding='utf-8') as f:
            segments_data = json.load(f)

        # 使用 pydantic 的 model_validate 方法反序列化
        for seg_data in segments_data:
            try:
                segment = NarrativeSegment.model_validate(seg_data)
                segments.append(segment)
            except Exception as e:
                print(f"Error loading segment {seg_data.get('segment_id', 'unknown')}: {e}")
                continue

    return segments

def main():
    print("=" * 70)
    print("测试实体提取修复效果")
    print("=" * 70)

    # 加载数据
    print("加载原子数据...")
    atoms = load_atoms()
    print(f"[OK] 加载了 {len(atoms)} 个原子")

    print("加载叙事片段...")
    segments = load_segments()
    print(f"[OK] 加载了 {len(segments)} 个片段")

    # 运行新的实体提取器
    print("\n开始实体提取...")
    extractor = EntityExtractor()
    entities_result = extractor.extract(segments, atoms)

    # 保存结果
    output_file = Path("data/output_pipeline_v3/entities_fixed.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(entities_result, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 保存修复后的实体数据到: {output_file}")

    # 显示关键修复效果
    print("\n" + "=" * 70)
    print("修复效果验证")
    print("=" * 70)

    # 检查罗星汉的情况
    persons = entities_result.get('persons', [])
    luo_entities = [p for p in persons if '罗' in p['name']]

    print(f"\n发现 {len(luo_entities)} 个与'罗'相关的人物实体:")
    for entity in luo_entities:
        name = entity['name']
        mentions = entity['mentions']
        atoms_count = len(entity.get('atoms', []))
        print(f"  - {name}: {mentions}次提及, 出现在{atoms_count}个原子中")

        # 显示前5个原子ID
        atom_ids = entity.get('atoms', [])[:5]
        if atom_ids:
            print(f"    前5个原子: {', '.join(atom_ids)}")

    # 检查坤沙的情况
    kunsha_entities = [p for p in persons if any(x in p['name'] for x in ['坤沙', '昆沙', '张奇夫'])]
    print(f"\n发现 {len(kunsha_entities)} 个与坤沙相关的人物实体:")
    for entity in kunsha_entities:
        name = entity['name']
        mentions = entity['mentions']
        atoms_count = len(entity.get('atoms', []))
        print(f"  - {name}: {mentions}次提及, 出现在{atoms_count}个原子中")

    # 统计信息
    total_entities = sum(len(entities_result.get(key, [])) for key in ['persons', 'countries', 'organizations', 'events', 'concepts', 'time_points'])

    print(f"\n总计实体数: {total_entities}")
    print(f"  人物: {len(entities_result.get('persons', []))}")
    print(f"  国家: {len(entities_result.get('countries', []))}")
    print(f"  组织: {len(entities_result.get('organizations', []))}")
    print(f"  事件: {len(entities_result.get('events', []))}")
    print(f"  概念: {len(entities_result.get('concepts', []))}")

    print("\n修复测试完成!")

if __name__ == "__main__":
    main()