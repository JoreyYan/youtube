"""
批次大小优化测试：对比不同batch_size的速度和质量
使用前5分钟数据（约165条字幕）进行快速测试
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


def test_batch_size(batch_size: int, test_name: str):
    """测试特定batch_size"""
    print(f"\n{'='*70}")
    print(f"测试: {test_name} (batch_size={batch_size})")
    print(f"{'='*70}")

    # 准备数据（前5分钟）
    parser = SRTParser()
    utterances = parser.parse("data/raw/test.srt")
    cleaner = Cleaner()
    utterances_clean = cleaner.clean(utterances)
    utterances_5min = [u for u in utterances_clean if u.start_ms < 300000]

    print(f"测试数据: {len(utterances_5min)}条字幕（前5分钟）")

    # 计算批次数
    total_batches = (len(utterances_5min) + batch_size - 1) // batch_size
    print(f"批次数: {total_batches}批")

    # 开始测试
    start_time = time.time()

    atomizer = Atomizer(CLAUDE_API_KEY, batch_size=batch_size, prompt_version='v1')
    atoms = atomizer.atomize(utterances_5min)

    elapsed_time = time.time() - start_time

    # 验证质量
    validator = AtomValidator()
    report = validator.validate(atoms, utterances_5min)
    stats = atomizer.client.get_stats()

    # 输出结果
    print(f"\n结果:")
    print(f"  耗时: {elapsed_time:.1f}秒")
    print(f"  平均每批: {elapsed_time/total_batches:.1f}秒")
    print(f"  原子数: {len(atoms)}个")
    print(f"  质量评分: {report['quality_score']}")
    print(f"  时间覆盖率: {report['coverage_rate']*100:.1f}%")
    print(f"  问题数: {len(report['issues'])}")
    if report['issues']:
        print(f"  问题列表:")
        for issue in report['issues']:
            print(f"    - {issue}")
    print(f"  API调用: {stats['total_calls']}次")
    print(f"  预估成本: {stats['estimated_cost']}")

    return {
        'batch_size': batch_size,
        'test_name': test_name,
        'utterances_count': len(utterances_5min),
        'total_batches': total_batches,
        'time_seconds': elapsed_time,
        'time_per_batch': elapsed_time / total_batches,
        'atoms_count': len(atoms),
        'quality_score': report['quality_score'],
        'coverage_rate': report['coverage_rate'],
        'issues_count': len(report['issues']),
        'issues': report['issues'],
        'warnings': report['warnings'],
        'api_calls': stats['total_calls'],
        'cost': stats['estimated_cost'],
        'type_distribution': report['type_distribution']
    }


def run_optimization_test():
    """运行完整的batch_size优化测试"""
    print("\n" + "="*70)
    print("Batch Size 优化测试")
    print("="*70)
    print("\n目标: 找到速度和质量的最佳平衡点")
    print("测试数据: 前5分钟字幕（约165条）")
    print("测试版本: atomize_v1.txt")

    if not CLAUDE_API_KEY:
        print("\nERROR: 未配置CLAUDE_API_KEY")
        return

    results = {}

    # 测试1: batch_size=50 (当前默认值)
    try:
        results['batch_50'] = test_batch_size(50, "当前默认值")
    except Exception as e:
        print(f"\n[ERROR] batch_size=50 测试失败: {e}")
        results['batch_50'] = None

    # 测试2: batch_size=100
    try:
        results['batch_100'] = test_batch_size(100, "2倍批次大小")
    except Exception as e:
        print(f"\n[ERROR] batch_size=100 测试失败: {e}")
        results['batch_100'] = None

    # 测试3: batch_size=200
    try:
        results['batch_200'] = test_batch_size(200, "4倍批次大小")
    except Exception as e:
        print(f"\n[ERROR] batch_size=200 测试失败: {e}")
        results['batch_200'] = None

    # 对比分析
    print("\n" + "="*70)
    print("对比分析")
    print("="*70)

    valid_results = {k: v for k, v in results.items() if v is not None}

    if len(valid_results) < 2:
        print("\n测试结果不足，无法对比")
        return

    # 表格对比
    print("\n速度对比:")
    print(f"{'配置':<15} {'总耗时':<12} {'批次数':<10} {'每批耗时':<12} {'加速比'}")
    print("-" * 70)

    baseline_time = valid_results.get('batch_50', {}).get('time_seconds', 1)

    for key in ['batch_50', 'batch_100', 'batch_200']:
        if key in valid_results:
            r = valid_results[key]
            speedup = baseline_time / r['time_seconds']
            print(f"{r['test_name']:<15} {r['time_seconds']:>8.1f}秒   {r['total_batches']:>6}批   {r['time_per_batch']:>8.1f}秒    {speedup:>5.2f}x")

    print("\n质量对比:")
    print(f"{'配置':<15} {'质量评分':<12} {'问题数':<10} {'覆盖率':<12} {'原子数'}")
    print("-" * 70)

    for key in ['batch_50', 'batch_100', 'batch_200']:
        if key in valid_results:
            r = valid_results[key]
            print(f"{r['test_name']:<15} {r['quality_score']:<12} {r['issues_count']:>6}个   {r['coverage_rate']*100:>8.1f}%    {r['atoms_count']:>5}个")

    print("\n成本对比:")
    print(f"{'配置':<15} {'API调用':<12} {'预估成本'}")
    print("-" * 70)

    for key in ['batch_50', 'batch_100', 'batch_200']:
        if key in valid_results:
            r = valid_results[key]
            print(f"{r['test_name']:<15} {r['api_calls']:>6}次      {r['cost']}")

    # 推荐
    print("\n推荐:")

    # 找到质量最好的
    def get_quality_rank(score):
        if 'A' in score: return 4
        if 'B' in score: return 3
        if 'C' in score: return 2
        if 'D' in score: return 1
        return 0

    best_quality = max(valid_results.values(), key=lambda r: (get_quality_rank(r['quality_score']), -r['issues_count']))
    fastest = min(valid_results.values(), key=lambda r: r['time_seconds'])

    print(f"  质量最佳: {best_quality['test_name']} (batch_size={best_quality['batch_size']})")
    print(f"    - {best_quality['quality_score']}, {best_quality['issues_count']}个问题, 覆盖率{best_quality['coverage_rate']*100:.1f}%")

    print(f"\n  速度最快: {fastest['test_name']} (batch_size={fastest['batch_size']})")
    print(f"    - {fastest['time_seconds']:.1f}秒, 比baseline快{baseline_time/fastest['time_seconds']:.2f}倍")

    # 综合推荐
    if best_quality['batch_size'] == fastest['batch_size']:
        print(f"\n  [RECOMMEND] 推荐使用 batch_size={best_quality['batch_size']}")
        print(f"    理由: 速度最快且质量最好")
    else:
        # 检查最快的版本质量是否可接受
        fastest_quality_rank = get_quality_rank(fastest['quality_score'])
        best_quality_rank = get_quality_rank(best_quality['quality_score'])

        if fastest_quality_rank >= best_quality_rank - 1:  # 质量差距不超过1级
            print(f"\n  [RECOMMEND] 推荐使用 batch_size={fastest['batch_size']}")
            print(f"    理由: 速度显著提升，质量差距可接受")
        else:
            print(f"\n  [RECOMMEND] 推荐使用 batch_size={best_quality['batch_size']}")
            print(f"    理由: 质量优先，速度提升不值得质量下降")

    # 预测完整30分钟处理时间
    print(f"\n预测完整30分钟视频处理时间 (989条字幕):")
    for key in ['batch_50', 'batch_100', 'batch_200']:
        if key in valid_results:
            r = valid_results[key]
            # 使用实测的每批耗时
            full_batches = (989 + r['batch_size'] - 1) // r['batch_size']
            predicted_time = r['time_per_batch'] * full_batches
            print(f"  batch_size={r['batch_size']:>3}: 约 {predicted_time/60:.1f}分钟 ({full_batches}批)")

    # 保存结果
    save_json(results, "data/output/batch_size_test_results.json")
    print(f"\n结果已保存: data/output/batch_size_test_results.json")

    print("\n" + "="*70)
    print("测试完成！")
    print("="*70)

    return results


if __name__ == "__main__":
    run_optimization_test()
