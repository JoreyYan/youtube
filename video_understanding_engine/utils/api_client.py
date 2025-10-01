"""
API客户端封装
"""

import anthropic
import openai
import time
from typing import Optional, Dict, Any
from anthropic import APIError, RateLimitError


class ClaudeClient:
    """Claude API客户端（带重试机制）"""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.total_calls = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def call(
        self,
        prompt: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4000,
        max_retries: int = 3
    ) -> str:
        """
        调用Claude API（带重试）

        Args:
            prompt: 提示词
            model: 模型名称
            max_tokens: 最大输出token数
            max_retries: 最大重试次数

        Returns:
            API返回的文本

        Raises:
            Exception: 重试次数用尽后抛出
        """
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                # 统计
                self.total_calls += 1
                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens

                return response.content[0].text

            except RateLimitError:
                # 限流：指数退避
                wait_time = 2 ** attempt
                print(f"WARNING Rate limit hit, waiting {wait_time}s before retry...")
                time.sleep(wait_time)

            except APIError as e:
                # API错误：重试
                print(f"WARNING API error: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)

        raise Exception("重试次数用尽")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        # 价格（Sonnet 3.5价格）
        input_price_per_m = 3.00  # $3/M tokens
        output_price_per_m = 15.00  # $15/M tokens

        input_cost = (self.total_input_tokens / 1_000_000) * input_price_per_m
        output_cost = (self.total_output_tokens / 1_000_000) * output_price_per_m
        total_cost = input_cost + output_cost

        return {
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "estimated_cost": f"${total_cost:.2f}"
        }


class OpenAIClient:
    """OpenAI API客户端"""

    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    def generate_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-large"
    ) -> list:
        """生成单个文本的embedding"""
        response = self.client.embeddings.create(
            model=model,
            input=[text]
        )
        return response.data[0].embedding

    def generate_embeddings_batch(
        self,
        texts: list,
        model: str = "text-embedding-3-large"
    ) -> list:
        """批量生成embedding"""
        response = self.client.embeddings.create(
            model=model,
            input=texts
        )
        return [item.embedding for item in response.data]
