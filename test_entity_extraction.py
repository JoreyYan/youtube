#!/usr/bin/env python3
"""测试实体边界识别修复"""

import sys
import os
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / 'video_understanding_engine'))

from analyzers.deep_analyzer import DeepAnalyzer
from utils import ClaudeClient, setup_logger

def main():
    print("=== 测试实体边界识别修复 ===")

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

    # 创建分析器
    analyzer = DeepAnalyzer(api_key)

    # 测试文本 - 来自原子 #5
    test_text = "然后呢 你们到了温哥华跟我面基的时候呢 你们就可以当面听到我这样的呃 祝福了啊"

    print(f"[测试文本] {test_text}")
    print()

    # 测试新的实体提取方法
    print("正在调用AI进行实体提取...")
    result = analyzer.analyze_segment_entities(test_text)

    print("\n[提取结果]")
    entities = result.get('entities', {})

    for entity_type, entity_list in entities.items():
        if entity_list:
            print(f"  {entity_type}: {entity_list}")

    # 检查是否正确提取了"温哥华"而不是"温哥华跟"
    countries = entities.get('countries', [])
    if '温哥华' in countries:
        print("\n[OK] 成功提取'温哥华'，边界识别正确")
    elif any('温哥华' in country for country in countries):
        print(f"\n[WARNING] 发现包含'温哥华'的实体: {[c for c in countries if '温哥华' in c]}")
    else:
        print("\n[INFO] 未提取到'温哥华'实体")

if __name__ == "__main__":
    main()