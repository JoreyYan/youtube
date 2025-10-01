"""
配置文件
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
BASE_DIR = Path(__file__).parent

# 加载.env文件
load_dotenv(BASE_DIR / '.env')

# API密钥（从环境变量读取）
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 数据目录
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DATA_DIR = DATA_DIR / "output"

# 提示词目录
PROMPTS_DIR = BASE_DIR / "prompts"

# 日志配置
LOG_DIR = BASE_DIR / "logs"
LOG_LEVEL = "INFO"

# 缓存目录
CACHE_DIR = BASE_DIR / ".cache"

# 确保目录存在
for dir_path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR,
                 OUTPUT_DATA_DIR, PROMPTS_DIR, LOG_DIR, CACHE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
