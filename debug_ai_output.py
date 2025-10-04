#!/usr/bin/env python3
"""详细展示AI的真实输出"""

import sys
import os
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / 'video_understanding_engine'))

from analyzers.deep_analyzer import DeepAnalyzer
from utils.api_client import ClaudeClient
import logging

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)

def main():
    print("=== AI 输出详细分析 ===")

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

    # 直接使用ClaudeClient来展示真实的AI交互
    client = ClaudeClient(api_key)

    # 测试提示词
    test_prompt = """你是一个专业的中文实体识别专家。请从以下文本中准确提取实体，注意实体边界的准确性。

【文本】
然后呢 你们到了温哥华跟我面基的时候呢 你们就可以当面听到我这样的呃 祝福了啊

【任务】
请提取以下类型的实体，注意：
1. **实体边界必须准确**，不要包含多余的字符
2. **人名**：如"温哥华"应该是地名，"罗星汉"应该准确识别边界
3. **地名**：城市、国家、地区名称
4. **组织机构**：公司、政府部门、团体等
5. **时间点**：具体时间、年份、日期等
6. **事件**：历史事件、新闻事件等
7. **概念术语**：专业术语、概念等

【输出格式】
请以JSON格式输出：
```json
{
  "entities": {
    "persons": ["人名1", "人名2"],
    "countries": ["国家1", "地区1"],
    "organizations": ["组织1", "机构1"],
    "time_points": ["时间1", "时间2"],
    "events": ["事件1", "事件2"],
    "concepts": ["概念1", "术语1"]
  }
}
```

【输出】"""

    print("[发送给AI的提示词]")
    print("=" * 50)
    print(test_prompt)
    print("=" * 50)

    print("\n[调用 Claude API...]")

    try:
        # 直接调用Claude API
        response = client.call(test_prompt, max_tokens=1000)

        print("\n[Claude AI 的完整原始响应]")
        print("=" * 50)
        print(response)
        print("=" * 50)

        # 展示token使用情况
        stats = client.get_stats()
        print(f"\n[API 统计信息]")
        print(f"调用次数: {stats['total_calls']}")
        print(f"输入tokens: {stats['total_input_tokens']}")
        print(f"输出tokens: {stats['total_output_tokens']}")
        print(f"预估费用: {stats['estimated_cost']}")

    except Exception as e:
        print(f"[ERROR] API调用失败: {e}")

if __name__ == "__main__":
    main()