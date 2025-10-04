# Day 3 模块设计规范

**日期**: 2025-01-XX
**目标**: 实现ResponseGenerator、ConversationalInterface、CLI

---

## 一、总览

Day 3 完成对话系统的最后3个模块，实现从查询到响应的完整闭环：

- **ResponseGenerator**: 生成自然语言回答 + 引用来源
- **ConversationalInterface**: 主控制器，协调所有模块
- **CLI**: 命令行交互界面

完成后整个对话系统可独立运行。

---

## 二、ResponseGenerator 设计

### 2.1 职责

将检索结果转化为自然语言回答，添加来源引用和时间戳。

### 2.2 核心功能

```python
class ResponseGenerator:
    """响应生成器 - 将检索结果转为自然语言"""

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.answer_prompt = self._load_answer_prompt()

    def generate(
        self,
        query: str,
        query_result: QueryResult,
        retrieval_results: List[RetrievalResult],
        context: Optional[ConversationContext] = None
    ) -> Response:
        """生成最终回答"""
```

### 2.3 Response结构

```python
@dataclass
class Response:
    """对话响应"""
    answer: str                      # 自然语言回答
    sources: List[Source]            # 引用来源
    confidence: float                # 置信度
    retrieved_count: int             # 检索到的内容数量
    response_time_ms: float          # 响应时间
    metadata: Dict                   # 额外信息
```

### 2.4 生成策略

**根据Intent选择不同的生成模板**:

| Intent | 生成策略 |
|--------|---------|
| SEARCH_SEMANTIC | 综合多个atoms，生成连贯回答 |
| SEARCH_ENTITY | 介绍实体，列出关键信息 |
| SEARCH_RELATION | 解释关系，引用graph数据 |
| SUMMARY | 提取segments，生成摘要 |
| RECOMMEND_CLIP | 列出推荐片段，说明理由 |

### 2.5 引用格式

```python
@dataclass
class Source:
    """回答来源"""
    item_id: str                     # atom_id/segment_id
    item_type: str                   # 'atom'/'segment'
    start_time: float                # 开始时间(秒)
    end_time: float                  # 结束时间(秒)
    excerpt: str                     # 内容摘录
    relevance_score: float           # 相关度
```

在回答中添加标记：`[Source 1: 00:15-00:45]`

### 2.6 完整实现

```python
# -*- coding: utf-8 -*-
"""Response Generator - Natural Language Answer Generation"""

import logging
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Source:
    """Answer source reference"""
    item_id: str
    item_type: str
    start_time: float
    end_time: float
    excerpt: str
    relevance_score: float

@dataclass
class Response:
    """Conversation response"""
    answer: str
    sources: List[Source]
    confidence: float
    retrieved_count: int
    response_time_ms: float
    metadata: Dict

class ResponseGenerator:
    """Natural language response generator"""

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.answer_prompt = self._load_answer_prompt()
        logger.info("ResponseGenerator initialized")

    def generate(
        self,
        query: str,
        query_result,
        retrieval_results: List,
        context = None
    ) -> Response:
        """Generate final answer"""
        start_time = time.time()

        # Build prompt
        prompt = self._build_prompt(query, query_result, retrieval_results, context)

        # Call LLM
        try:
            answer_text = self.llm_client.call(prompt, max_tokens=800, temperature=0.3)
            confidence = 0.8
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            answer_text = self._generate_fallback_answer(query_result, retrieval_results)
            confidence = 0.4

        # Extract sources
        sources = self._extract_sources(retrieval_results)

        # Build response
        response = Response(
            answer=answer_text,
            sources=sources,
            confidence=confidence,
            retrieved_count=len(retrieval_results),
            response_time_ms=(time.time() - start_time) * 1000,
            metadata={'intent': query_result.intent.value if hasattr(query_result.intent, 'value') else str(query_result.intent)}
        )

        logger.info(f"Generated response in {response.response_time_ms:.0f}ms")
        return response

    def _build_prompt(self, query: str, query_result, retrieval_results: List, context) -> str:
        """Build LLM prompt"""
        intent_str = query_result.intent.value if hasattr(query_result.intent, 'value') else str(query_result.intent)

        # Format retrieved content
        content_items = []
        for i, result in enumerate(retrieval_results[:5], 1):
            item = result.content
            excerpt = self._get_excerpt(item)
            time_str = self._format_time(item.get('start_time', 0), item.get('end_time', 0))
            content_items.append(f"[{i}] {time_str}\n{excerpt}")

        content_str = "\n\n".join(content_items)

        # Build prompt
        prompt = f"""You are answering questions about a video based on retrieved content.

User Query: {query}
Query Intent: {intent_str}

Retrieved Content:
{content_str}

Instructions:
- Answer the question directly based on the retrieved content
- Cite sources using [Source N: MM:SS-MM:SS] format
- If content is insufficient, say so honestly
- Keep answer concise (2-3 paragraphs max)

Answer:"""

        return prompt

    def _generate_fallback_answer(self, query_result, retrieval_results: List) -> str:
        """Generate fallback answer when LLM fails"""
        if not retrieval_results:
            return "I couldn't find relevant information to answer your question."

        # Simple concatenation
        excerpts = []
        for result in retrieval_results[:3]:
            excerpt = self._get_excerpt(result.content)
            excerpts.append(excerpt)

        return " ".join(excerpts)

    def _extract_sources(self, retrieval_results: List) -> List[Source]:
        """Extract sources from retrieval results"""
        sources = []

        for result in retrieval_results[:5]:
            item = result.content
            sources.append(Source(
                item_id=result.item_id,
                item_type=result.item_type,
                start_time=item.get('start_time', 0.0),
                end_time=item.get('end_time', 0.0),
                excerpt=self._get_excerpt(item),
                relevance_score=result.score
            ))

        return sources

    def _get_excerpt(self, item: Dict) -> str:
        """Get text excerpt from item"""
        if 'text' in item:
            return item['text'][:200]
        elif 'content' in item:
            return item['content'][:200]
        elif 'summary' in item:
            return item['summary'][:200]
        else:
            return str(item)[:200]

    def _format_time(self, start: float, end: float) -> str:
        """Format timestamp"""
        def seconds_to_mmss(seconds):
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins:02d}:{secs:02d}"

        if start == 0 and end == 0:
            return "[Time N/A]"

        return f"[{seconds_to_mmss(start)}-{seconds_to_mmss(end)}]"

    def _load_answer_prompt(self) -> str:
        """Load answer generation prompt"""
        return ""  # Prompt built dynamically in _build_prompt

    def __repr__(self) -> str:
        return f"ResponseGenerator(llm={self.llm_client.provider})"
```

**代码量**: ~250行

---

## 三、ConversationalInterface 设计

### 3.1 职责

主控制器，协调所有模块完成一次对话交互。

### 3.2 完整流程

```
用户输入 query
    ↓
1. ContextManager: 获取会话上下文
    ↓
2. QueryUnderstanding: 解析意图 → QueryResult
    ↓
3. HybridRetriever: 检索内容 → RetrievalResult[]
    ↓
4. ResponseGenerator: 生成回答 → Response
    ↓
5. ContextManager: 更新上下文
    ↓
返回 Response
```

### 3.3 核心接口

```python
class ConversationalInterface:
    """对话系统主控制器"""

    def __init__(
        self,
        data_loader: DataLoader,
        context_manager: ContextManager,
        query_engine: QueryUnderstanding,
        retriever: HybridRetriever,
        response_gen: ResponseGenerator
    ):
        # 初始化所有模块

    def ask(
        self,
        query: str,
        session_id: Optional[str] = None,
        mode: SessionMode = SessionMode.EXPLORATION
    ) -> Response:
        """处理一次对话交互"""
```

### 3.4 完整实现

```python
# -*- coding: utf-8 -*-
"""Conversational Interface - Main Orchestration"""

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

class ConversationalInterface:
    """Main conversational interface orchestrator"""

    def __init__(
        self,
        data_loader,
        context_manager,
        query_engine,
        retriever,
        response_gen
    ):
        self.data_loader = data_loader
        self.context_manager = context_manager
        self.query_engine = query_engine
        self.retriever = retriever
        self.response_gen = response_gen
        logger.info("ConversationalInterface initialized")

    def ask(
        self,
        query: str,
        session_id: Optional[str] = None,
        mode = None
    ):
        """Process one conversation turn"""
        start_time = time.time()

        try:
            # Step 1: Get or create session
            if not session_id:
                from .context_manager import SessionMode
                mode = mode or SessionMode.EXPLORATION
                session_id = self.context_manager.create_session(
                    video_id="default_video",
                    mode=mode
                )
                logger.info(f"Created new session: {session_id}")

            # Step 2: Parse query
            logger.debug("Parsing query...")
            query_result = self.query_engine.parse(query, session_id)
            logger.info(f"Intent: {query_result.intent.value if hasattr(query_result.intent, 'value') else query_result.intent}")

            # Step 3: Retrieve content
            logger.debug("Retrieving content...")
            retrieval_results = self.retriever.retrieve(query_result, top_k=5)
            logger.info(f"Retrieved {len(retrieval_results)} results")

            # Step 4: Generate response
            logger.debug("Generating response...")
            context = self.context_manager.get_session(session_id)
            response = self.response_gen.generate(
                query, query_result, retrieval_results, context
            )

            # Step 5: Update context
            self.context_manager.add_turn(session_id, "user", query)
            self.context_manager.add_turn(session_id, "assistant", response.answer)
            self.context_manager.update_focus_entities(session_id, query_result.entities)

            # Add session_id to metadata
            response.metadata['session_id'] = session_id

            elapsed = (time.time() - start_time) * 1000
            logger.info(f"Total time: {elapsed:.0f}ms")

            return response

        except Exception as e:
            logger.error(f"Conversation failed: {e}", exc_info=True)
            raise

    def get_session_history(self, session_id: str):
        """Get session conversation history"""
        session = self.context_manager.get_session(session_id)
        if not session:
            return []
        return session.history

    def list_sessions(self):
        """List all active sessions"""
        return list(self.context_manager.sessions.keys())

    def __repr__(self) -> str:
        return "ConversationalInterface(modules=5)"
```

**代码量**: ~150行

---

## 四、CLI 设计

### 4.1 职责

提供命令行交互界面，方便测试和演示。

### 4.2 功能需求

1. **交互模式**: 循环接收用户输入
2. **命令支持**:
   - `/help`: 显示帮助
   - `/mode <mode>`: 切换模式
   - `/history`: 查看历史
   - `/clear`: 清空会话
   - `/exit`: 退出
3. **格式化输出**: 美化显示回答和来源
4. **错误处理**: 友好的错误提示

### 4.3 界面设计

```
=================================================
📹 Video Understanding - Conversational Interface
=================================================

Video: test_video.mp4
Mode: EXPLORATION

> What is this video about?

[Thinking...]

Answer:
This video discusses the history of the Golden Triangle
region in Myanmar, focusing on the era of the "Twin Heroes"...
[Source 1: 00:15-01:23] [Source 2: 02:45-03:10]

Response time: 1.2s | Confidence: 0.85

> /history

Conversation History:
1. [User] What is this video about?
2. [Assistant] This video discusses...

>
```

### 4.4 完整实现

```python
# -*- coding: utf-8 -*-
"""CLI - Command Line Interface for Conversational System"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from conversational import (
    DataLoader, ContextManager, QueryUnderstanding,
    HybridRetriever, ConversationalInterface, SessionMode
)
from conversational.response_generator import ResponseGenerator
from core.llm_client import LLMClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CLI:
    """Command-line interface for conversational system"""

    def __init__(self, data_path: str, llm_provider: str = "openai"):
        """Initialize CLI"""
        print("Initializing conversational system...")

        # Initialize all components
        self.data_loader = DataLoader(data_path)
        self.context_manager = ContextManager()

        llm_client = LLMClient(provider=llm_provider, model="gpt-4o-mini")
        self.query_engine = QueryUnderstanding(llm_client, self.context_manager)
        self.retriever = HybridRetriever(self.data_loader)
        self.response_gen = ResponseGenerator(llm_client)

        self.interface = ConversationalInterface(
            self.data_loader,
            self.context_manager,
            self.query_engine,
            self.retriever,
            self.response_gen
        )

        self.session_id = None
        self.mode = SessionMode.EXPLORATION

        print("System ready!\n")

    def run(self):
        """Run interactive CLI"""
        self.print_banner()

        while True:
            try:
                query = input("\n> ").strip()

                if not query:
                    continue

                # Handle commands
                if query.startswith('/'):
                    self.handle_command(query)
                    continue

                # Process query
                print("\n[Thinking...]")
                response = self.interface.ask(query, self.session_id, self.mode)

                # Update session_id
                if not self.session_id:
                    self.session_id = response.metadata.get('session_id')

                # Display response
                self.display_response(response)

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n[ERROR] {e}")
                logger.error(f"Error: {e}", exc_info=True)

    def print_banner(self):
        """Print welcome banner"""
        print("=" * 60)
        print("Video Understanding - Conversational Interface")
        print("=" * 60)
        print(f"\nMode: {self.mode.value if hasattr(self.mode, 'value') else self.mode}")
        print("\nCommands: /help /mode /history /clear /exit")
        print("-" * 60)

    def display_response(self, response):
        """Display formatted response"""
        print(f"\nAnswer:\n{response.answer}\n")

        if response.sources:
            print("Sources:")
            for i, source in enumerate(response.sources[:3], 1):
                time_str = self.format_time(source.start_time, source.end_time)
                print(f"  [{i}] {time_str} - {source.item_type} ({source.relevance_score:.2f})")

        print(f"\nResponse time: {response.response_time_ms/1000:.1f}s | " +
              f"Confidence: {response.confidence:.2f} | " +
              f"Retrieved: {response.retrieved_count} items")

    def handle_command(self, command: str):
        """Handle CLI commands"""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == '/help':
            self.print_help()
        elif cmd == '/mode':
            if len(parts) > 1:
                self.change_mode(parts[1])
            else:
                print(f"Current mode: {self.mode.value if hasattr(self.mode, 'value') else self.mode}")
        elif cmd == '/history':
            self.show_history()
        elif cmd == '/clear':
            self.clear_session()
        elif cmd == '/exit':
            print("Goodbye!")
            sys.exit(0)
        else:
            print(f"Unknown command: {cmd}. Type /help for help.")

    def print_help(self):
        """Print help information"""
        print("""
Available Commands:
  /help              Show this help message
  /mode <mode>       Change conversation mode (exploration/creation/learning)
  /history           Show conversation history
  /clear             Clear current session
  /exit              Exit the program

Examples:
  > What is this video about?
  > Who is mentioned in the first 5 minutes?
  > Find clips suitable for TikTok
        """)

    def change_mode(self, mode_str: str):
        """Change conversation mode"""
        mode_str = mode_str.upper()
        try:
            self.mode = SessionMode[mode_str]
            print(f"Mode changed to: {self.mode.value}")
            self.clear_session()  # Start new session with new mode
        except KeyError:
            print(f"Invalid mode: {mode_str}")
            print("Valid modes: EXPLORATION, CREATION, LEARNING")

    def show_history(self):
        """Show conversation history"""
        if not self.session_id:
            print("No conversation history yet.")
            return

        history = self.interface.get_session_history(self.session_id)
        if not history:
            print("No conversation history yet.")
            return

        print("\nConversation History:")
        for i, msg in enumerate(history, 1):
            role_str = msg.role.capitalize() if hasattr(msg, 'role') else str(msg.get('role', 'Unknown'))
            content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
            print(f"{i}. [{role_str}] {content[:100]}{'...' if len(content) > 100 else ''}")

    def clear_session(self):
        """Clear current session"""
        self.session_id = None
        print("Session cleared. Starting fresh conversation.")

    def format_time(self, start: float, end: float) -> str:
        """Format timestamp"""
        def seconds_to_mmss(seconds):
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins:02d}:{secs:02d}"

        if start == 0 and end == 0:
            return "[Time N/A]"

        return f"{seconds_to_mmss(start)}-{seconds_to_mmss(end)}"

def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    else:
        data_path = "data/output_pipeline_v3"

    try:
        cli = CLI(data_path)
        cli.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
```

**代码量**: ~200行

---

## 五、实施计划

### 5.1 创建顺序

1. **ResponseGenerator** (~1小时)
   - 创建response_generator.py
   - 测试基本生成功能

2. **ConversationalInterface** (~1小时)
   - 创建conversational_interface.py
   - 更新__init__.py导出
   - 测试端到端流程

3. **CLI** (~1小时)
   - 创建cli.py
   - 测试交互体验
   - 优化输出格式

### 5.2 测试策略

1. **单元测试**: 每个模块独立测试
2. **集成测试**: 完整对话流程测试
3. **交互测试**: CLI实际使用体验

---

## 六、预期成果

完成后可实现：

1. ✅ 完整的对话系统闭环
2. ✅ 支持7种查询意图
3. ✅ 多会话管理
4. ✅ 来源引用和时间戳
5. ✅ 友好的CLI交互界面

**总代码量**: ~600行
**完成时间**: 3-4小时

---

## 七、下一步

1. 按顺序创建3个模块
2. 运行完整的端到端测试
3. 调优体验和性能
4. 准备演示视频

