# -*- coding: utf-8 -*-
"""Setup Day 3 Modules - ResponseGenerator, ConversationalInterface, CLI"""

import os

# ResponseGenerator module
response_generator_code = '''# -*- coding: utf-8 -*-
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
            content_items.append(f"[{i}] {time_str}\\n{excerpt}")

        content_str = "\\n\\n".join(content_items)

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
'''

# ConversationalInterface module
conversational_interface_code = '''# -*- coding: utf-8 -*-
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
'''

# CLI module
cli_code = '''# -*- coding: utf-8 -*-
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

        print("System ready!\\n")

    def run(self):
        """Run interactive CLI"""
        self.print_banner()

        while True:
            try:
                query = input("\\n> ").strip()

                if not query:
                    continue

                # Handle commands
                if query.startswith('/'):
                    self.handle_command(query)
                    continue

                # Process query
                print("\\n[Thinking...]")
                response = self.interface.ask(query, self.session_id, self.mode)

                # Update session_id
                if not self.session_id:
                    self.session_id = response.metadata.get('session_id')

                # Display response
                self.display_response(response)

            except KeyboardInterrupt:
                print("\\n\\nGoodbye!")
                break
            except Exception as e:
                print(f"\\n[ERROR] {e}")
                logger.error(f"Error: {e}", exc_info=True)

    def print_banner(self):
        """Print welcome banner"""
        print("=" * 60)
        print("Video Understanding - Conversational Interface")
        print("=" * 60)
        print(f"\\nMode: {self.mode.value if hasattr(self.mode, 'value') else self.mode}")
        print("\\nCommands: /help /mode /history /clear /exit")
        print("-" * 60)

    def display_response(self, response):
        """Display formatted response"""
        print(f"\\nAnswer:\\n{response.answer}\\n")

        if response.sources:
            print("Sources:")
            for i, source in enumerate(response.sources[:3], 1):
                time_str = self.format_time(source.start_time, source.end_time)
                print(f"  [{i}] {time_str} - {source.item_type} ({source.relevance_score:.2f})")

        print(f"\\nResponse time: {response.response_time_ms/1000:.1f}s | " +
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

        print("\\nConversation History:")
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
        print("\\n\\nGoodbye!")
    except Exception as e:
        print(f"\\n[FATAL ERROR] {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
'''

def main():
    print("Creating Day 3 modules...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    conversational_dir = os.path.join(base_dir, 'conversational')
    scripts_dir = os.path.join(base_dir, 'scripts')

    # Create response_generator.py
    response_gen_path = os.path.join(conversational_dir, 'response_generator.py')
    with open(response_gen_path, 'w', encoding='utf-8') as f:
        f.write(response_generator_code)
    print(f"  Created: {response_gen_path}")

    # Create conversational_interface.py
    interface_path = os.path.join(conversational_dir, 'conversational_interface.py')
    with open(interface_path, 'w', encoding='utf-8') as f:
        f.write(conversational_interface_code)
    print(f"  Created: {interface_path}")

    # Create cli.py
    cli_path = os.path.join(scripts_dir, 'cli.py')
    with open(cli_path, 'w', encoding='utf-8') as f:
        f.write(cli_code)
    print(f"  Created: {cli_path}")

    print("\\nDay 3 modules created successfully!")
    print("\\nNext: Update __init__.py to export new modules")

if __name__ == "__main__":
    main()
