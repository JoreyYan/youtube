"""
处理30分钟字幕数据
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import SRTParser, Cleaner
from atomizers import Atomizer, AtomValidator, OverlapFixer
from utils import save_jsonl, save_json, setup_logger
from config import CLAUDE_API_KEY
import time

logger = setup_logger(__name__)


def process_30min():
    """处理前30分钟"""
    print("\n" + "="*60)
    print("处理前30分钟字幕")
    print("="*60)

    if not CLAUDE_API_KEY:
        print("ERROR 未配置CLAUDE_API_KEY")
        return

    start_time = time.time()

    # Step 1: 解析字幕
    print("\n[1/5] 解析SRT文件...")
    parser = SRTParser()
    utterances = parser.parse("data/raw/test.srt")
    print(f"  解析完成：{len(utterances)}条字幕")

    # Step 2: 清洗
    print("\n[2/5] 清洗字幕...")
    cleaner = Cleaner()
    utterances_clean = cleaner.clean(utterances)
    print(f"  清洗完成：{len(utterances_clean)}条")

    # 截取前30分钟（1800秒 = 1800000毫秒）
    utterances_30min = [u for u in utterances_clean if u.start_ms < 1800000]
    print(f"  截取前30分钟：{len(utterances_30min)}条")

    # Step 3: 原子化
    print("\n[3/5] 原子化处理...")
    atomizer = Atomizer(CLAUDE_API_KEY, batch_size=50)  # 恢复到50，质量更好
    atoms = atomizer.atomize(utterances_30min)
    print(f"  生成原子：{len(atoms)}个")

    # API统计
    stats = atomizer.client.get_stats()
    print(f"  API调用: {stats['total_calls']}次")
    print(f"  预估成本: {stats['estimated_cost']}")

    # Step 3.5: 修复时间重叠（新增）
    print("\n[3.5/5] 修复时间重叠...")
    fixer = OverlapFixer(strategy='proportional_split')  # 使用比例分割，更公平
    atoms_fixed = fixer.fix(atoms)
    overlap_report = fixer.get_overlap_report(atoms, atoms_fixed)
    print(f"  修复前重叠: {overlap_report['overlaps_before']}处")
    print(f"  修复后重叠: {overlap_report['overlaps_after']}处")
    print(f"  修复数量: {overlap_report['fixed_count']}处")

    # 使用修复后的原子继续后续步骤
    atoms = atoms_fixed

    # Step 4: 质量验证
    print("\n[4/5] 质量验证...")
    validator = AtomValidator()
    report = validator.validate(atoms, utterances_30min)
    print(f"  质量评分: {report['quality_score']}")
    print(f"  时间覆盖率: {report['coverage_rate']*100:.1f}%")
    print(f"  问题数: {len(report['issues'])}")
    print(f"  警告数: {len(report['warnings'])}")

    # Step 5: 保存结果
    print("\n[5/5] 保存结果...")

    # 保存原子数据
    save_jsonl(atoms, "data/output/atoms_30min.jsonl")
    print(f"  原子数据: data/output/atoms_30min.jsonl")

    # 保存验证报告
    save_json(report, "data/output/validation_30min.json")
    print(f"  验证报告: data/output/validation_30min.json")

    # 保存API统计
    save_json(stats, "data/output/stats_30min.json")
    print(f"  API统计: data/output/stats_30min.json")

    # 保存前端需要的JSON（包含所有原子的完整信息）
    atoms_for_frontend = []
    for atom in atoms:
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

    save_json({
        "atoms": atoms_for_frontend,
        "stats": stats,
        "report": report
    }, "data/output/frontend_data.json")
    print(f"  前端数据: data/output/frontend_data.json")

    # 总结
    elapsed_time = time.time() - start_time
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)
    print(f"总耗时: {elapsed_time:.1f}秒")
    print(f"原子数: {len(atoms)}个")
    print(f"质量评分: {report['quality_score']}")
    print(f"预估成本: {stats['estimated_cost']}")
    print("\n类型分布:")
    for t, count in report['type_distribution'].items():
        print(f"  {t}: {count}个")
    print("="*60)

    return atoms, report, stats


if __name__ == "__main__":
    process_30min()
