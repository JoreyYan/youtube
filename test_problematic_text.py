#!/usr/bin/env python3
"""测试问题文本的实体提取"""

import sys
import os
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / 'video_understanding_engine'))

from analyzers.deep_analyzer import DeepAnalyzer

def main():
    print("=== 测试问题文本的实体提取 ===")

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

    # 你提到的问题文本
    problematic_text = """有的傻逼说那不对，因为他们俩肆虐的时候啊60年代中国人穷啊，中国人连饭都吃不起，怎么买毒品，不是他俩不卖，肯定是中国人不买，放屁那他妈的罗兴汉如果这么说有点道理那昆沙起来，罗兴汉灭了，昆沙起来的时候，二双雄老二起来的时候，那都已经改革开放10年了，改革开放20年了，那咱们没钱买毒品吗，所以昆沙和罗星汉是真爱国，他真不卖给中国人毒品啊"""

    print(f"[测试文本]")
    print(problematic_text)
    print()

    # 使用新的AI方法提取实体
    print("正在使用修复后的AI方法进行实体提取...")
    result = analyzer.analyze_segment_entities(problematic_text)

    print("\n[修复后的提取结果]")
    entities = result.get('entities', {})

    for entity_type, entity_list in entities.items():
        if entity_list:
            print(f"  {entity_type}: {entity_list}")

    # 检查是否存在边界错误
    all_entities = []
    for entity_list in entities.values():
        all_entities.extend(entity_list)

    print(f"\n[边界检查]")
    boundary_issues = []
    for entity in all_entities:
        if any(suffix in entity for suffix in ['如', '灭', '是', '跟', '单', '马']):
            boundary_issues.append(entity)

    if boundary_issues:
        print(f"❌ 发现边界问题: {boundary_issues}")
    else:
        print("✅ 未发现边界识别问题")

    print(f"\n[正确的实体应该是]:")
    print("  persons: ['罗兴汉', '昆沙', '罗星汉']")
    print("  countries: ['中国']")
    print("  time_points: ['60年代', '改革开放10年', '改革开放20年']")

if __name__ == "__main__":
    main()