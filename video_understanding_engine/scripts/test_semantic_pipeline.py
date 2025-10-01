"""
测试语义分析Pipeline
处理视频的前10分钟，测试新的叙事片段识别和深度分析功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.video_processor_v2 import VideoProcessorV2, PipelineConfig
import config

def main():
    # 使用config模块

    # 创建Pipeline配置
    pipeline_config = PipelineConfig(
        # 输入
        input_srt_path="data/raw/test.srt",
        # 原子化
        batch_size=50,
        prompt_version='v2',
        use_cache=True,
        use_checkpoint=True,
        # 后处理
        fix_overlap=True,
        overlap_strategy='proportional_split',
        # 语义分析（新增）
        enable_semantic_analysis=True,
        identify_narrative_segments=True,
        deep_analyze_segments=True,
        # 输出
        output_dir="data/output_semantic_test",
        save_segments=False,
        save_frontend_data=True,
        save_narrative_segments=True
    )

    # 创建处理器
    processor = VideoProcessorV2(
        api_key=config.CLAUDE_API_KEY,
        config=pipeline_config
    )

    # 处理前10分钟
    print("\n开始测试：处理视频前10分钟")
    print("启用功能：")
    print("  [x] 原子化")
    print("  [x] 叙事片段识别")
    print("  [x] 深度语义分析")
    print()

    time_limit_ms = 10 * 60 * 1000  # 10分钟

    result = processor.process(time_limit_ms=time_limit_ms)

    # 输出详细结果
    print("\n" + "="*70)
    print("测试完成")
    print("="*70)
    print(f"\n原子数量: {len(result['atoms'])}")
    print(f"叙事片段: {len(result['narrative_segments'])}")
    print(f"总耗时: {result['elapsed_time']:.1f}秒")

    if result['narrative_segments']:
        print(f"\n叙事片段详情：")
        for seg in result['narrative_segments']:
            print(f"\n{seg.segment_id}: {seg.title}")
            print(f"  时长: {seg.duration_minutes:.1f}分钟")
            print(f"  包含原子: {len(seg.atoms)}个")
            print(f"  主题: {seg.topics.primary_topic}")
            print(f"  重要性: {seg.importance_score:.2f}")
            print(f"  质量: {seg.quality_score:.2f}")
            print(f"  核心论点: {seg.ai_analysis.core_argument}")
            print(f"  标签: {', '.join(seg.topics.free_tags[:8])}")

            if seg.entities.persons:
                print(f"  人物: {', '.join(seg.entities.persons)}")
            if seg.entities.events:
                print(f"  事件: {', '.join(seg.entities.events)}")

    print("\n输出文件:")
    output_dir = Path(pipeline_config.output_dir)
    for file in output_dir.glob("*.json*"):
        print(f"  {file.name}")

if __name__ == "__main__":
    main()
