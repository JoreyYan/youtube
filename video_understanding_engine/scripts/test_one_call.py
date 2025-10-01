"""
测试单次AI调用，查看实际返回
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import ClaudeClient
import json

# 构建测试提示词
prompt_path = Path(__file__).parent.parent / 'prompts' / 'analyze_comprehensive.txt'
with open(prompt_path, 'r', encoding='utf-8') as f:
    prompt_template = f.read()

context = {
    "segment_num": 1,
    "duration_minutes": 10.0,
    "start_time": "00:00:00",
    "end_time": "00:10:00"
}

full_text = """
【测试文本】
这是一段测试内容，讲述了布雷顿森林体系的崩溃。
1971年尼克松宣布关闭黄金窗口，标志着美元与黄金脱钩。
这一决策对全球金融体系产生了深远影响。
"""

prompt = prompt_template.format(
    CONTEXT=json.dumps(context, ensure_ascii=False),
    FULL_TEXT=full_text
)

# 调用API
print("正在调用API...")
api_key = "your_api_key_here"  # 这里需要从环境变量获取
client = ClaudeClient(api_key)
response = client.call(prompt, max_tokens=4000)

# 输出原始响应
print("\n" + "="*70)
print("原始响应:")
print("="*70)
print(response)
print("\n" + "="*70)
print(f"响应长度: {len(response)}字符")
print("="*70)

# 尝试解析
import re
json_block_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
if json_block_match:
    print("\n找到```json代码块")
    json_str = json_block_match.group(1)
else:
    print("\n未找到```json代码块，尝试提取{...}")
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
    else:
        print("ERROR: 未找到JSON对象")
        sys.exit(1)

print(f"\n提取的JSON（前500字符）:")
print(json_str[:500])

# 尝试解析
try:
    data = json.loads(json_str)
    print("\nJSON解析成功！")
    print(f"标题: {data.get('title', 'N/A')}")
except Exception as e:
    print(f"\nJSON解析失败: {e}")
    print(f"错误类型: {type(e).__name__}")
