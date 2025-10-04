# -*- coding: utf-8 -*-
"""Context Manager - Manage conversation state"""

import time
import uuid
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter

logger = logging.getLogger(__name__)

class SessionMode(Enum):
    """Session modes"""
    EXPLORATION = "exploration"
    CREATION = "creation"
    LEARNING = "learning"

@dataclass
class Message:
    """Conversation message"""
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)

@dataclass
class ConversationContext:
    """Conversation context"""
    session_id: str
    video_id: str
    mode: SessionMode = SessionMode.EXPLORATION
    history: List[Message] = field(default_factory=list)
    focus_entities: Counter = field(default_factory=Counter)
    retrieved_items: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)

class ContextManager:
    """Conversation context manager"""

    def __init__(self, max_history_turns: int = 10):
        self.max_history_turns = max_history_turns
        self._sessions: Dict[str, ConversationContext] = {}
        logger.info(f"ContextManager initialized (max_history={max_history_turns})")

    def create_session(
        self,
        video_id: str,
        mode: SessionMode = SessionMode.EXPLORATION,
        session_id: Optional[str] = None
    ) -> str:
        """Create new session"""
        if session_id is None:
            session_id = f"sess_{uuid.uuid4().hex[:12]}"

        context = ConversationContext(
            session_id=session_id,
            video_id=video_id,
            mode=mode
        )

        self._sessions[session_id] = context
        logger.info(f"Created session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[ConversationContext]:
        """Get session by ID"""
        return self._sessions.get(session_id)

    def add_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str
    ) -> bool:
        """Add conversation turn"""
        context = self.get_session(session_id)
        if not context:
            return False

        context.history.append(Message(role="user", content=user_message))
        context.history.append(Message(role="assistant", content=assistant_response))

        max_messages = self.max_history_turns * 2
        if len(context.history) > max_messages:
            context.history = context.history[-max_messages:]

        context.updated_at = time.time()
        return True

    def update_focus_entities(self, session_id: str, entities: List[str]) -> bool:
        """Update focus entities"""
        context = self.get_session(session_id)
        if not context:
            return False

        context.focus_entities.update(entities)
        context.updated_at = time.time()
        return True

    def get_recent_entities(self, session_id: str, top_n: int = 3) -> List[str]:
        """Get recently mentioned entities"""
        context = self.get_session(session_id)
        if not context:
            return []

        return [entity for entity, count in context.focus_entities.most_common(top_n)]

    def __len__(self) -> int:
        return len(self._sessions)

    def __repr__(self) -> str:
        return f"ContextManager(sessions={len(self._sessions)})"
