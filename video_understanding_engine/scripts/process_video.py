"""
使用标准化Pipeline处理视频
支持自动切分、缓存、断点续传、时间重叠修复
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import VideoProcessor, PipelineConfig
from config import CLAUDE_API_KEY


def main():
    """主函数"""
    if not CLAUDE_API_KEY:
        print("ERROR: 未配置CLAUDE_API_KEY")
        return

    # 配置Pipeline
    config = PipelineConfig(
        # 输入
        input_srt_path="data/raw/test.srt",

        # 自动切分配置
        auto_segment=True,              # 开启自动切分
        segment_duration_minutes=10,    # 每10分钟一个片段
        segment_threshold_minutes=15,   # 超过15分钟才切分

        # 原子化配置
        batch_size=50,
        use_cache=True,                 # 使用缓存
        use_checkpoint=True,            # 使用断点续传

        # 后处理
        fix_overlap=True,               # 修复时间重叠
        overlap_strategy='proportional_split',

        # 输出
        output_dir="data/output",
        save_segments=True,             # 保存各片段结果
        save_frontend_data=True
    )

    # 创建处理器
    processor = VideoProcessor(CLAUDE_API_KEY, config)

    # 执行处理
    # 可选：添加时间限制，例如只处理前30分钟
    # result = processor.process(time_limit_ms=30*60*1000)

    result = processor.process()  # 处理完整视频

    return result


if __name__ == "__main__":
    main()
