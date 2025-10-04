#!/usr/bin/env python3
"""重新生成所有实体注释，使用修复后的AI方法"""

import sys
import json
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / 'video_understanding_engine'))

from analyzers.deep_analyzer import DeepAnalyzer

def main():
    print("=== 重新生成实体注释（使用修复后的AI） ===")

    # 读取API密钥
    api_key_file = Path("video_understanding_engine/.env")
    if not api_key_file.exists():
        print("[ERROR] .env文件不存在")
        return

    api_key = None
    with open(api_key_file, 'r') as f:
        for line in f:
            if line.startswith('CLAUDE_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break

    if not api_key:
        print("[ERROR] 未找到CLAUDE_API_KEY")
        return

    # 加载原子数据
    atoms_file = Path("video_understanding_engine/data/output_pipeline_v3/atoms.jsonl")
    if not atoms_file.exists():
        print("[ERROR] atoms.jsonl不存在")
        return

    atoms = []
    with open(atoms_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                atoms.append(json.loads(line))

    print(f"[OK] 加载了{len(atoms)}个原子")

    # 创建DeepAnalyzer
    analyzer = DeepAnalyzer(api_key)

    # 重新生成注释
    new_annotations = []

    for i, atom in enumerate(atoms[:5]):  # 先测试前5个
        print(f"\n[{i+1}/5] 分析原子 {atom['atom_id']}")

        text = atom.get('merged_text', '')
        if not text.strip():
            print("  跳过：文本为空")
            continue

        print(f"  文本: {text[:50]}...")

        # 使用修复后的AI方法
        try:
            result = analyzer.analyze_segment_entities(text)
            entities_data = result.get('entities', {})

            # 转换为注释格式
            entities_list = []
            for entity_type, entity_names in entities_data.items():
                for entity_name in entity_names:
                    entities_list.append({
                        'name': entity_name,
                        'type': entity_type.rstrip('s'),  # 去掉复数
                        'confidence': 0.9
                    })

            annotation = {
                'atom_id': atom['atom_id'],
                'entities': entities_list,
                'topics': [],  # 简化处理
                'emotion': {
                    'type': 'neutral',
                    'score': 0.5,
                    'confidence': 0.8,
                    'distribution': {'neutral': 0.8, 'positive': 0.1, 'negative': 0.1}
                },
                'importance_score': 0.7,
                'quality_score': 0.8
            }

            new_annotations.append(annotation)
            print(f"  成功：提取了{len(entities_list)}个实体")

            # 显示提取的实体
            if entities_list:
                print("  实体:", [e['name'] for e in entities_list])

        except Exception as e:
            print(f"  [ERROR] {e}")
            continue

    # 保存新注释
    if new_annotations:
        backup_file = Path("video_understanding_engine/data/output_pipeline_v3/atom_annotations_old.json")
        output_file = Path("video_understanding_engine/data/output_pipeline_v3/atom_annotations.json")

        # 备份旧文件
        if output_file.exists():
            with open(backup_file, 'w', encoding='utf-8') as f:
                with open(output_file, 'r', encoding='utf-8') as old_f:
                    f.write(old_f.read())
            print(f"[OK] 已备份旧注释到: {backup_file}")

        # 保存新注释
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(new_annotations, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] 已生成{len(new_annotations)}个新注释")
        print(f"[OK] 保存到: {output_file}")
        print("\n刷新浏览器查看修复结果！")
    else:
        print("[ERROR] 未生成任何注释")

if __name__ == "__main__":
    main()