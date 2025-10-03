"""
测试实体提取功能
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import NarrativeSegment, Atom
from analyzers.entity_extractor import EntityExtractor

def main():
    print("="*70)
    print("测试实体提取功能")
    print("="*70)

    # 读取已有的叙事片段
    segments_path = Path("data/output_pipeline_v3/narrative_segments.json")
    atoms_path = Path("data/output_pipeline_v3/atoms.jsonl")

    if not segments_path.exists():
        print(f"[X] 找不到文件: {segments_path}")
        return

    if not atoms_path.exists():
        print(f"[X] 找不到文件: {atoms_path}")
        return

    # 加载片段
    with open(segments_path, 'r', encoding='utf-8') as f:
        segments_data = json.load(f)

    print(f"[OK] 加载了 {len(segments_data)} 个叙事片段")

    # 加载原子
    atoms = []
    with open(atoms_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                atoms.append(Atom(**json.loads(line)))

    print(f"[OK] 加载了 {len(atoms)} 个原子")

    # 转换为 NarrativeSegment 对象
    segments = [NarrativeSegment(**seg) for seg in segments_data]

    # 创建提取器
    extractor = EntityExtractor()

    # 提取实体
    print("\n开始提取实体...")
    entities = extractor.extract(segments, atoms)

    # 显示结果
    print("\n" + "="*70)
    print("提取结果")
    print("="*70)

    print(f"\n总实体数: {entities['statistics']['total_entities']}")
    print(f"\n各类型统计:")
    for entity_type, count in entities['statistics']['by_type'].items():
        print(f"  {entity_type}: {count}")

    # 显示前3个实体示例
    for entity_type in ['persons', 'countries', 'events', 'concepts']:
        if entities[entity_type]:
            print(f"\n{entity_type} 示例:")
            for entity in entities[entity_type][:3]:
                print(f"  - {entity['name']}: {entity['mentions']}次提及, 出现在{len(entity['atoms'])}个原子中")
                if entity['atoms']:
                    print(f"    原子: {', '.join(entity['atoms'][:5])}")
                if entity['context']:
                    print(f"    上下文: {', '.join(entity['context'][:2])}")

    # 保存结果
    output_path = Path("data/output_pipeline_v3/entities.json")
    extractor.save(entities, output_path)

    print("\n" + "="*70)
    print("测试完成！")
    print("="*70)

if __name__ == "__main__":
    main()
