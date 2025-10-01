"""
EmbeddingGenerator - 向量嵌入生成器

支持多种 embedding 服务：
- OpenAI (text-embedding-3-small, text-embedding-3-large)
- 可扩展支持其他服务
"""

from typing import List, Dict, Any
from openai import OpenAI
import tiktoken
import time


class EmbeddingGenerator:
    """向量嵌入生成器"""

    # 支持的模型配置
    MODELS = {
        'openai:text-embedding-3-small': {
            'dimension': 1536,
            'cost_per_1m_tokens': 0.02,
            'max_tokens': 8191
        },
        'openai:text-embedding-3-large': {
            'dimension': 3072,
            'cost_per_1m_tokens': 0.13,
            'max_tokens': 8191
        },
        'openai:text-embedding-ada-002': {
            'dimension': 1536,
            'cost_per_1m_tokens': 0.10,
            'max_tokens': 8191
        }
    }

    def __init__(
        self,
        api_key: str,
        model: str = 'text-embedding-3-small',
        provider: str = 'openai'
    ):
        """
        初始化生成器

        Args:
            api_key: API密钥
            model: 模型名称
            provider: 服务提供商（目前只支持'openai'）
        """
        self.provider = provider
        self.model = model
        self.full_model_key = f"{provider}:{model}"

        if self.full_model_key not in self.MODELS:
            raise ValueError(f"不支持的模型: {self.full_model_key}")

        self.model_config = self.MODELS[self.full_model_key]

        # 初始化客户端
        if provider == 'openai':
            self.client = OpenAI(api_key=api_key)
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        else:
            raise ValueError(f"不支持的provider: {provider}")

        # 统计信息
        self.stats = {
            'total_calls': 0,
            'total_tokens': 0,
            'total_texts': 0,
            'estimated_cost': 0.0
        }

    def generate_embedding(self, text: str) -> List[float]:
        """
        生成单个文本的向量

        Args:
            text: 输入文本

        Returns:
            向量（浮点数列表）
        """
        if not text or not text.strip():
            raise ValueError("输入文本不能为空")

        # 调用API
        response = self.client.embeddings.create(
            input=[text],
            model=self.model
        )

        # 提取向量
        embedding = response.data[0].embedding

        # 更新统计
        tokens_used = response.usage.total_tokens
        self._update_stats(1, tokens_used, 1)

        return embedding

    def generate_batch(
        self,
        texts: List[str],
        batch_size: int = 100,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        批量生成向量

        Args:
            texts: 文本列表
            batch_size: 批处理大小（OpenAI限制：最多2048个输入）
            show_progress: 是否显示进度

        Returns:
            向量列表
        """
        if not texts:
            return []

        # 过滤空文本
        valid_texts = [t for t in texts if t and t.strip()]
        if len(valid_texts) != len(texts):
            print(f"[WARNING] 过滤掉 {len(texts) - len(valid_texts)} 个空文本")

        if not valid_texts:
            raise ValueError("没有有效的输入文本")

        embeddings = []
        total_batches = (len(valid_texts) + batch_size - 1) // batch_size

        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]

            if show_progress:
                batch_num = i // batch_size + 1
                print(f"  [Batch {batch_num}/{total_batches}] 处理 {len(batch)} 个文本...")

            # 调用API
            response = self.client.embeddings.create(
                input=batch,
                model=self.model
            )

            # 提取向量
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)

            # 更新统计
            tokens_used = response.usage.total_tokens
            self._update_stats(1, tokens_used, len(batch))

            # 避免频率限制
            if i + batch_size < len(valid_texts):
                time.sleep(0.1)

        return embeddings

    def count_tokens(self, text: str) -> int:
        """
        估算文本的token数量

        Args:
            text: 输入文本

        Returns:
            token数量
        """
        if self.provider == 'openai':
            return len(self.tokenizer.encode(text))
        else:
            # 粗略估算：1 token ≈ 4 字符（英文）或 1.5 字符（中文）
            return len(text) // 2

    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.model_config['dimension']

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计字典
        """
        return {
            'provider': self.provider,
            'model': self.model,
            'dimension': self.get_dimension(),
            'total_calls': self.stats['total_calls'],
            'total_tokens': self.stats['total_tokens'],
            'total_texts': self.stats['total_texts'],
            'estimated_cost': f"${self.stats['estimated_cost']:.6f}"
        }

    def _update_stats(self, calls: int, tokens: int, texts: int):
        """更新统计信息"""
        self.stats['total_calls'] += calls
        self.stats['total_tokens'] += tokens
        self.stats['total_texts'] += texts

        # 计算成本
        cost_per_token = self.model_config['cost_per_1m_tokens'] / 1_000_000
        self.stats['estimated_cost'] += tokens * cost_per_token

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_calls': 0,
            'total_tokens': 0,
            'total_texts': 0,
            'estimated_cost': 0.0
        }
