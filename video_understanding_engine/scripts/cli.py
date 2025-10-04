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
