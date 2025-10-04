"""
测试 VideoProcessorV3 - 完整的向量化 Pipeline

测试流程：
1. 处理视频字幕
2. 生成原子和片段
3. 向量化并存储
4. 执行语义搜索测试
"""

import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.video_processor_v3 import VideoProcessorV3, PipelineConfig
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def main():
    """测试 v3 Pipeline"""

    print("="*70)
    print("测试 VideoProcessorV3 - 向量化Pipeline")
    print("="*70)

    # 获取 API Keys
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')

    if not claude_api_key:
        print("[X] 缺少 CLAUDE_API_KEY")
        return

    if not openai_api_key:
        print("[X] 缺少 OPENAI_API_KEY")
        return

    print("[OK] API Keys 已加载")

    # 配置 Pipeline
    config = PipelineConfig(
        input_srt_path="data/raw/test.srt",
        # 原子化配置
        batch_size=50,
        prompt_version='v2',
        use_cache=True,
        use_checkpoint=True,
        # 语义分析配置
        enable_semantic_analysis=True,
        identify_narrative_segments=True,
        deep_analyze_segments=True,
        # 原子标注配置
        enable_atom_annotation=True,
        annotation_batch_size=10,
        # 向量化配置
        enable_vectorization=True,
        embedding_model='text-embedding-3-small',
        vector_store_path=None,  # 使用内存模式测试
        vectorize_atoms=True,
        vectorize_segments=True,
        # 输出配置
        output_dir="data/output_pipeline_v3"
    )

    # 创建处理器
    processor = VideoProcessorV3(
        api_key=claude_api_key,
        openai_api_key=openai_api_key,
        config=config
    )

    # 执行处理（限制前5分钟以节省成本）
    print("\n[!] 测试模式：仅处理前5分钟")
    result = processor.process(time_limit_ms=5 * 60 * 1000)

    print("\n" + "="*70)
    print("Pipeline 处理完成！")
    print("="*70)

    # 测试语义搜索
    if result.get('search_engine'):
        print("\n" + "="*70)
        print("测试语义搜索功能")
        print("="*70)

        search_engine = result['search_engine']

        # 测试查询
        test_queries = [
            "尼克松的历史",
            "双轨制改革",
            "教科书的内容"
        ]

        for query in test_queries:
            print(f"\n查询: \"{query}\"")
            print("-" * 70)

            # 搜索原子（降低阈值）
            atom_results = search_engine.search_atoms(
                query=query,
                limit=3,
                score_threshold=0.3  # 降低阈值
            )

            print(f"找到 {len(atom_results)} 个相关原子：")
            for i, result in enumerate(atom_results, 1):
                print(f"\n  [{i}] {result['atom_id']} (相似度: {result['score']:.3f})")
                print(f"      时间: {result['start_time']} - {result['end_time']}")
                print(f"      类型: {result['type']}")
                print(f"      内容: {result['text'][:100]}...")

            # 搜索片段
            segment_results = search_engine.search_segments(
                query=query,
                limit=2,
                score_threshold=0.3  # 降低阈值
            )

            if segment_results:
                print(f"\n找到 {len(segment_results)} 个相关片段：")
                for i, result in enumerate(segment_results, 1):
                    print(f"\n  [{i}] {result['segment_id']} (相似度: {result['score']:.3f})")
                    print(f"      标题: {result['title']}")
                    print(f"      时长: {result['duration_minutes']:.1f}分钟")
                    print(f"      摘要: {result['summary'][:100]}...")

    print("\n" + "="*70)
    print("测试完成！")
    print("="*70)

    # 打印统计
    stats = result.get('stats', {})
    print(f"\n【处理统计】")
    print(f"  原子数量: {stats.get('atom_count', 0)}")
    print(f"  片段数量: {stats.get('narrative_segment_count', 0)}")

    if 'vector' in stats:
        vector_stats = stats['vector']
        print(f"\n【向量化统计】")
        print(f"  原子向量: {vector_stats.get('atoms_vectorized', 0)}")
        print(f"  片段向量: {vector_stats.get('segments_vectorized', 0)}")
        print(f"  Embedding 成本: ${vector_stats.get('embedding_cost', 0):.6f}")

    print(f"\n【总耗时】: {result.get('elapsed_time', 0):.1f}秒")
    print(f"\n[OK] 结果已保存到: {config.output_dir}")


if __name__ == "__main__":
    main()
