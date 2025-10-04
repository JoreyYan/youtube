#!/usr/bin/env python3
"""修复segments_state.json中的原子ID引用"""

import sys
import json
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / 'video_understanding_engine'))

def load_atom_mapping():
    """加载原子ID映射关系"""
    atoms_file = Path("video_understanding_engine/data/output_pipeline_v3/atoms.jsonl")

    if not atoms_file.exists():
        print("[ERROR] atoms.jsonl不存在")
        return {}

    # 读取所有原子，建立新ID映射
    atom_id_mapping = {}
    with open(atoms_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if line.strip():
                atom = json.loads(line)
                # 新的原子ID（如A001, A002等）对应原来的复合索引
                atom_id_mapping[i] = atom['atom_id']

    print(f"[OK] 加载了{len(atom_id_mapping)}个原子ID映射")
    return atom_id_mapping

def create_compound_to_simple_mapping():
    """创建复合ID到简单ID的映射"""
    # 从之前的fix_atom_ids.py逻辑推断映射关系
    # 复合ID格式: A001_0, A002_1, A003_2, ..., A001_34, A002_35, ...
    # 对应原子索引: 0, 1, 2, ..., 34, 35, ...

    mapping = {}

    # 读取原子数量
    atoms_file = Path("video_understanding_engine/data/output_pipeline_v3/atoms.jsonl")
    atom_count = 0
    with open(atoms_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                atom_count += 1

    print(f"[INFO] 当前有{atom_count}个原子")

    # 根据之前的fix_atom_ids.py中的逻辑重建映射
    # 复合ID的格式是: {original_id}_{index}
    # 其中original_id循环使用A001-A036，index从0递增

    for i in range(atom_count):
        # 计算原来的原子ID（A001-A036循环）
        original_base = i % 36 + 1
        original_id = f"A{original_base:03d}"

        # 复合ID
        compound_id = f"{original_id}_{i}"

        # 对应现在的简单ID
        current_atom_id = f"A{i+1:03d}"

        mapping[compound_id] = current_atom_id

    return mapping

def fix_segments():
    """修复segments_state.json中的原子ID"""
    segments_file = Path("video_understanding_engine/data/output_pipeline_v3/segments_state.json")

    if not segments_file.exists():
        print("[ERROR] segments_state.json不存在")
        return

    # 加载段落状态
    with open(segments_file, 'r', encoding='utf-8') as f:
        segments = json.load(f)

    # 创建ID映射
    compound_to_simple = create_compound_to_simple_mapping()

    print(f"[OK] 创建了{len(compound_to_simple)}个ID映射关系")
    print("示例映射:", list(compound_to_simple.items())[:5])

    # 更新每个段落的原子ID
    updated_count = 0
    for segment in segments:
        segment_id = segment.get('segment_id', 'unknown')
        old_atom_ids = segment.get('atom_ids', [])

        if old_atom_ids:
            new_atom_ids = []
            converted_count = 0

            for old_id in old_atom_ids:
                if old_id in compound_to_simple:
                    new_atom_ids.append(compound_to_simple[old_id])
                    converted_count += 1
                else:
                    # 保留无法映射的ID
                    new_atom_ids.append(old_id)
                    print(f"[WARNING] 无法映射ID: {old_id}")

            segment['atom_ids'] = new_atom_ids

            # 如果成功转换了ID，重置错误状态
            if converted_count > 0:
                if segment.get('status') == 'failed' and segment.get('error_message') == 'No atoms in segment':
                    segment['status'] = 'atomized'
                    segment['error_message'] = None
                    print(f"[FIX] {segment_id}: 修复了{converted_count}个原子ID，重置状态为atomized")
                    updated_count += 1

            print(f"[OK] {segment_id}: {len(old_atom_ids)}个原子ID -> {converted_count}个转换成功")

    # 备份原文件
    backup_file = segments_file.with_suffix('.json.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)

    # 保存更新后的文件
    with open(segments_file, 'w', encoding='utf-8') as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 成功修复{updated_count}个段落的状态")
    print(f"[OK] 已保存备份: {backup_file}")
    print(f"[OK] 已更新: {segments_file}")

def main():
    print("=== 修复段落原子ID引用 ===")

    try:
        fix_segments()
        print("\n[SUCCESS] 修复完成！")
        print("\n刷新浏览器查看修复结果！")
    except Exception as e:
        print(f"[ERROR] 修复失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()