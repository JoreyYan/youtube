"""
处理完整2小时视频（切分成10分钟片段）
"""

import sys
from pathlib import Path
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import SRTParser, Cleaner
from atomizers import Atomizer, AtomValidator, OverlapFixer
from utils import save_jsonl, save_json, setup_logger
from config import CLAUDE_API_KEY

logger = setup_logger(__name__)


def process_full_video(segment_duration_minutes: int = 10):
    """
    处理完整视频，切分成多个片段

    Args:
        segment_duration_minutes: 每个片段的时长（分钟）
    """
    print("\n" + "="*60)
    print("处理完整视频（切分处理）")
    print("="*60)

    if not CLAUDE_API_KEY:
        print("ERROR: 未配置CLAUDE_API_KEY")
        return

    start_time = time.time()

    # Step 1: 解析字幕
    print("\n[1/6] 解析SRT文件...")
    parser = SRTParser()
    utterances = parser.parse("data/raw/test.srt")
    print(f"  解析完成：{len(utterances)}条字幕")

    # Step 2: 清洗
    print("\n[2/6] 清洗字幕...")
    cleaner = Cleaner()
    utterances_clean = cleaner.clean(utterances)
    print(f"  清洗完成：{len(utterances_clean)}条")

    # 获取视频总时长
    max_time_ms = max(u.end_ms for u in utterances_clean)
    total_minutes = max_time_ms // 60000
    print(f"  视频总时长：{total_minutes}分钟")

    # Step 3: 计算切分方案
    print(f"\n[3/6] 切分方案...")
    segment_duration_ms = segment_duration_minutes * 60 * 1000
    total_segments = (max_time_ms + segment_duration_ms - 1) // segment_duration_ms
    print(f"  切分粒度：{segment_duration_minutes}分钟/片段")
    print(f"  片段总数：{total_segments}个")

    # 创建输出目录
    output_dir = Path("data/output/segments")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 4: 处理各个片段
    print(f"\n[4/6] 处理各片段...")
    all_atoms = []
    all_stats = {
        'segments': [],
        'total_api_calls': 0,
        'total_cost': 0.0,
        'total_atoms': 0,
        'total_overlaps_fixed': 0
    }

    for seg_num in range(1, total_segments + 1):
        seg_start_ms = (seg_num - 1) * segment_duration_ms
        seg_end_ms = min(seg_num * segment_duration_ms, max_time_ms)

        print(f"\n--- 片段 {seg_num}/{total_segments} ---")
        print(f"  时间范围: {_ms_to_time(seg_start_ms)} - {_ms_to_time(seg_end_ms)}")

        # 提取该片段的字幕
        segment_utterances = [
            u for u in utterances_clean
            if u.start_ms < seg_end_ms and u.end_ms > seg_start_ms
        ]
        print(f"  字幕数量: {len(segment_utterances)}条")

        if len(segment_utterances) == 0:
            print(f"  [跳过] 该片段无字幕")
            continue

        # 原子化（使用缓存和断点）
        checkpoint_id = f"segment_{seg_num:03d}"
        atomizer = Atomizer(
            CLAUDE_API_KEY,
            batch_size=50,
            checkpoint_id=checkpoint_id
        )

        try:
            segment_atoms = atomizer.atomize(segment_utterances)
            print(f"  生成原子: {len(segment_atoms)}个")

            # 修复时间重叠
            fixer = OverlapFixer(strategy='proportional_split')
            segment_atoms_fixed = fixer.fix(segment_atoms)
            overlap_report = fixer.get_overlap_report(segment_atoms, segment_atoms_fixed)
            print(f"  修复重叠: {overlap_report['fixed_count']}处")

            # 统计
            stats = atomizer.client.get_stats()
            segment_stats = {
                'segment_num': seg_num,
                'start_ms': seg_start_ms,
                'end_ms': seg_end_ms,
                'utterances_count': len(segment_utterances),
                'atoms_count': len(segment_atoms_fixed),
                'api_calls': stats['total_calls'],
                'cost': stats['estimated_cost'],
                'overlaps_fixed': overlap_report['fixed_count']
            }
            all_stats['segments'].append(segment_stats)
            all_stats['total_api_calls'] += stats['total_calls']
            all_stats['total_atoms'] += len(segment_atoms_fixed)
            all_stats['total_overlaps_fixed'] += overlap_report['fixed_count']

            # 解析成本字符串 "$0.42" -> 0.42
            cost_str = stats['estimated_cost'].replace('$', '')
            all_stats['total_cost'] += float(cost_str)

            # 保存片段结果
            segment_file = output_dir / f"segment_{seg_num:03d}.json"
            segment_data = {
                'segment_info': segment_stats,
                'atoms': [atom.to_dict() for atom in segment_atoms_fixed]
            }
            save_json(segment_data, str(segment_file))
            print(f"  已保存: {segment_file.name}")

            # 添加到总列表
            all_atoms.extend(segment_atoms_fixed)

        except Exception as e:
            logger.error(f"  片段{seg_num}处理失败: {e}")
            print(f"  [失败] 可重新运行继续处理此片段")
            continue

    # Step 5: 质量验证（全局）
    print(f"\n[5/6] 全局质量验证...")
    validator = AtomValidator()
    # 需要传入完整的utterances来计算覆盖率
    report = validator.validate(all_atoms, utterances_clean)
    print(f"  质量评分: {report['quality_score']}")
    print(f"  时间覆盖率: {report['coverage_rate']*100:.1f}%")
    print(f"  问题数: {len(report['issues'])}个")
    print(f"  警告数: {len(report['warnings'])}个")

    # Step 6: 保存结果
    print(f"\n[6/6] 保存最终结果...")

    # 保存完整原子列表
    save_jsonl(all_atoms, "data/output/atoms_full.jsonl")
    print(f"  完整原子: data/output/atoms_full.jsonl")

    # 保存验证报告
    save_json(report, "data/output/validation_full.json")
    print(f"  验证报告: data/output/validation_full.json")

    # 保存统计信息
    all_stats['total_cost_formatted'] = f"${all_stats['total_cost']:.2f}"
    save_json(all_stats, "data/output/stats_full.json")
    print(f"  统计信息: data/output/stats_full.json")

    # 保存前端数据
    atoms_for_frontend = []
    for atom in all_atoms:
        atoms_for_frontend.append({
            "atom_id": atom.atom_id,
            "start_ms": atom.start_ms,
            "end_ms": atom.end_ms,
            "duration_ms": atom.duration_ms,
            "start_time": atom.start_time,
            "end_time": atom.end_time,
            "duration_seconds": atom.duration_seconds,
            "merged_text": atom.merged_text,
            "type": atom.type,
            "completeness": atom.completeness,
            "source_utterance_ids": atom.source_utterance_ids
        })

    frontend_data = {
        "atoms": atoms_for_frontend,
        "stats": {
            'total_calls': all_stats['total_api_calls'],
            'estimated_cost': all_stats['total_cost_formatted']
        },
        "report": report
    }
    save_json(frontend_data, "data/output/frontend_data_full.json")
    print(f"  前端数据: data/output/frontend_data_full.json")

    # 总结
    elapsed_time = time.time() - start_time
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)
    print(f"总耗时: {elapsed_time:.1f}秒 ({elapsed_time/60:.1f}分钟)")
    print(f"片段数: {len(all_stats['segments'])}个")
    print(f"原子数: {all_stats['total_atoms']}个")
    print(f"API调用: {all_stats['total_api_calls']}次")
    print(f"预估成本: {all_stats['total_cost_formatted']}")
    print(f"质量评分: {report['quality_score']}")
    print(f"时间覆盖: {report['coverage_rate']*100:.1f}%")
    print(f"修复重叠: {all_stats['total_overlaps_fixed']}处")
    print("\n类型分布:")
    for t, count in report['type_distribution'].items():
        print(f"  {t}: {count}个")
    print("="*60)

    return all_atoms, report, all_stats


def _ms_to_time(ms: int) -> str:
    """毫秒转时间格式"""
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


if __name__ == "__main__":
    process_full_video(segment_duration_minutes=10)
