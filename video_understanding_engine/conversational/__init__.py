# -*- coding: utf-8 -*-
"""Conversational Interface Package"""

from .data_loader import DataLoader, VideoMetadata
from .context_manager import ContextManager, ConversationContext, SessionMode, Message
from .query_understanding import QueryUnderstanding, QueryIntent, QueryResult
from .hybrid_retriever import HybridRetriever, RetrievalResult
from .response_generator import ResponseGenerator, Response, Source
from .conversational_interface import ConversationalInterface

__all__ = [
    'DataLoader', 'VideoMetadata',
    'ContextManager', 'ConversationContext', 'SessionMode', 'Message',
    'QueryUnderstanding', 'QueryIntent', 'QueryResult',
    'HybridRetriever', 'RetrievalResult',
    'ResponseGenerator', 'Response', 'Source',
    'ConversationalInterface'
]
__version__ = '0.1.0'