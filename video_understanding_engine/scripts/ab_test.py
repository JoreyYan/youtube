"""
A/B测试：对比atomize_v1和v2的效果
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import SRTParser, Cleaner
from atomizers import Atomizer, AtomValidator
from utils import save_json, setup_logger
from config import CLAUDE_API_KEY
import time

logger = setup_logger(__name__)


def run_ab_test():
    """运行A/B测试"""
    print("\n" + "="*70)
    print("A/B测试：atomize_v1 vs atomize_v2")
    print("="*70)

    if not CLAUDE_API_KEY:
        print("ERROR 未配置CLAUDE_API_KEY")
        return

    # Step 1: 准备数据（使用相同的30分钟数据）
    print("\n[1/3] 准备测试数据...")
    parser = SRTParser()
    utterances = parser.parse("data/raw/test.srt")
    cleaner = Cleaner()
    utterances_clean = cleaner.clean(utterances)
    utterances_30min = [u for u in utterances_clean if u.start_ms < 1800000]
    print(f"  测试数据：{len(utterances_30min)}条字幕（前30分钟）")

    results = {}

    # Step 2: 测试v1
    print("\n[2/3] 测试 atomize_v1...")
    print("-" * 70)
    v1_start = time.time()
    atomizer_v1 = Atomizer(CLAUDE_API_KEY, batch_size=50, prompt_version='v1')
    atoms_v1 = atomizer_v1.atomize(utterances_30min)
    v1_time = time.time() - v1_start

    validator = AtomValidator()
    report_v1 = validator.validate(atoms_v1, utterances_30min)
    stats_v1 = atomizer_v1.client.get_stats()

    print(f"  [OK] 完成 - 耗时 {v1_time:.1f}秒")
    print(f"    原子数: {len(atoms_v1)}个")
    print(f"    质量评分: {report_v1['quality_score']}")
    print(f"    时间覆盖率: {report_v1['coverage_rate']*100:.1f}%")
    print(f"    问题数: {len(report_v1['issues'])}")
    print(f"    预估成本: {stats_v1['estimated_cost']}")

    results['v1'] = {
        'atoms_count': len(atoms_v1),
        'quality_score': report_v1['quality_score'],
        'coverage_rate': report_v1['coverage_rate'],
        'issues': report_v1['issues'],
        'warnings': report_v1['warnings'],
        'time_seconds': v1_time,
        'cost': stats_v1['estimated_cost'],
        'type_distribution': report_v1['type_distribution']
    }

    # 重置API统计（因为共用一个client）
    atomizer_v1.client.total_calls = 0
    atomizer_v1.client.total_input_tokens = 0
    atomizer_v1.client.total_output_tokens = 0

    # Step 3: 测试v2
    print("\n[3/3] 测试 atomize_v2...")
    print("-" * 70)
    v2_start = time.time()
    atomizer_v2 = Atomizer(CLAUDE_API_KEY, batch_size=50, prompt_version='v2')
    atoms_v2 = atomizer_v2.atomize(utterances_30min)
    v2_time = time.time() - v2_start

    report_v2 = validator.validate(atoms_v2, utterances_30min)
    stats_v2 = atomizer_v2.client.get_stats()

    print(f"  [OK] 完成 - 耗时 {v2_time:.1f}秒")
    print(f"    原子数: {len(atoms_v2)}个")
    print(f"    质量评分: {report_v2['quality_score']}")
    print(f"    时间覆盖率: {report_v2['coverage_rate']*100:.1f}%")
    print(f"    问题数: {len(report_v2['issues'])}")
    print(f"    预估成本: {stats_v2['estimated_cost']}")

    results['v2'] = {
        'atoms_count': len(atoms_v2),
        'quality_score': report_v2['quality_score'],
        'coverage_rate': report_v2['coverage_rate'],
        'issues': report_v2['issues'],
        'warnings': report_v2['warnings'],
        'time_seconds': v2_time,
        'cost': stats_v2['estimated_cost'],
        'type_distribution': report_v2['type_distribution']
    }

    # 对比分析
    print("\n" + "="*70)
    print("对比分析")
    print("="*70)

    print("\n质量对比:")
    print(f"  v1: {results['v1']['quality_score']:8s} | 覆盖率 {results['v1']['coverage_rate']*100:.1f}% | {len(results['v1']['issues'])}个问题")
    print(f"  v2: {results['v2']['quality_score']:8s} | 覆盖率 {results['v2']['coverage_rate']*100:.1f}% | {len(results['v2']['issues'])}个问题")

    print("\n效率对比:")
    print(f"  v1: {results['v1']['time_seconds']:.1f}秒 | {results['v1']['cost']}")
    print(f"  v2: {results['v2']['time_seconds']:.1f}秒 | {results['v2']['cost']}")

    print("\n原子数对比:")
    print(f"  v1: {results['v1']['atoms_count']}个原子")
    print(f"  v2: {results['v2']['atoms_count']}个原子")

    # 判断胜者
    def get_quality_rank(score):
        if 'A' in score: return 4
        if 'B' in score: return 3
        if 'C' in score: return 2
        return 1

    v1_rank = get_quality_rank(results['v1']['quality_score'])
    v2_rank = get_quality_rank(results['v2']['quality_score'])

    print("\n推荐结果:")
    if v2_rank > v1_rank:
        print("  [RECOMMEND] 推荐使用 atomize_v2（质量更高）")
        winner = 'v2'
    elif v2_rank == v1_rank:
        if len(results['v2']['issues']) < len(results['v1']['issues']):
            print("  [RECOMMEND] 推荐使用 atomize_v2（问题更少）")
            winner = 'v2'
        elif results['v2']['coverage_rate'] > results['v1']['coverage_rate']:
            print("  [RECOMMEND] 推荐使用 atomize_v2（覆盖率更高）")
            winner = 'v2'
        else:
            print("  [WARN] 两个版本质量相近，可继续使用 v1")
            winner = 'v1'
    else:
        print("  [WARN] v2质量下降，建议继续使用 v1")
        winner = 'v1'

    results['winner'] = winner
    results['comparison'] = {
        'quality_improved': v2_rank > v1_rank,
        'issues_reduced': len(results['v2']['issues']) < len(results['v1']['issues']),
        'coverage_improved': results['v2']['coverage_rate'] > results['v1']['coverage_rate']
    }

    # 保存结果
    print("\n保存A/B测试结果...")
    save_json(results, "data/output/ab_test_results.json")
    print(f"  结果保存到: data/output/ab_test_results.json")

    print("\n" + "="*70)
    print("A/B测试完成！")
    print("="*70)

    return results


if __name__ == "__main__":
    run_ab_test()
