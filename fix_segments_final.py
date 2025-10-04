#!/usr/bin/env python3
"""最终修复segments_state.json中的原子ID引用"""

import sys
import json
from pathlib import Path

def fix_segments_final():
    """最终修复segments_state.json中的原子ID"""
    segments_file = Path("video_understanding_engine/data/output_pipeline_v3/segments_state.json")

    if not segments_file.exists():
        print("[ERROR] segments_state.json不存在")
        return

    # 加载段落状态
    with open(segments_file, 'r', encoding='utf-8') as f:
        segments = json.load(f)

    print(f"[OK] 加载了{len(segments)}个段落")

    # 更新每个段落的原子ID
    updated_count = 0
    total_converted = 0

    for segment in segments:
        segment_id = segment.get('segment_id', 'unknown')
        old_atom_ids = segment.get('atom_ids', [])

        if old_atom_ids:
            new_atom_ids = []
            converted_count = 0

            for old_id in old_atom_ids:
                if '_' in old_id:
                    # 复合ID格式: A001_34 -> 提取索引号34，转为A035
                    try:
                        index = int(old_id.split('_')[1])
                        new_id = f"A{index+1:03d}"
                        new_atom_ids.append(new_id)
                        converted_count += 1
                    except (ValueError, IndexError):
                        # 保留无法解析的ID
                        new_atom_ids.append(old_id)
                        print(f"[WARNING] 无法解析复合ID: {old_id}")
                else:
                    # 简单ID格式，直接保留
                    new_atom_ids.append(old_id)

            segment['atom_ids'] = new_atom_ids
            total_converted += converted_count

            # 如果成功转换了ID，重置错误状态
            if converted_count > 0:
                if segment.get('status') == 'failed' and segment.get('error_message') == 'No atoms in segment':
                    segment['status'] = 'atomized'
                    segment['error_message'] = None
                    print(f"[FIX] {segment_id}: 修复了{converted_count}个原子ID，重置状态为atomized")
                    updated_count += 1

            print(f"[OK] {segment_id}: {len(old_atom_ids)}个原子ID -> {converted_count}个转换成功")

    # 备份原文件
    backup_file = segments_file.with_suffix('.json.backup2')
    import shutil
    shutil.copy(segments_file, backup_file)

    # 保存更新后的文件
    with open(segments_file, 'w', encoding='utf-8') as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 总共转换了{total_converted}个复合ID")
    print(f"[OK] 成功修复{updated_count}个段落的状态")
    print(f"[OK] 已保存备份: {backup_file}")
    print(f"[OK] 已更新: {segments_file}")

def main():
    print("=== 最终修复段落原子ID引用 ===")

    try:
        fix_segments_final()
        print("\n[SUCCESS] 修复完成！")
        print("\n刷新浏览器查看修复结果！")
    except Exception as e:
        print(f"[ERROR] 修复失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()