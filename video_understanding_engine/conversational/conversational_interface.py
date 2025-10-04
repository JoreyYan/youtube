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
