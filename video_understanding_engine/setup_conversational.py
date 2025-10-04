#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup script to create all conversational module files in one go
This avoids encoding issues from multiple file operations
"""

import os
from pathlib import Path

# Get the conversational directory
BASE_DIR = Path(__file__).parent / 'conversational'
BASE_DIR.mkdir(exist_ok=True)

# File contents as strings
FILES = {
    '__init__.py': '''# -*- coding: utf-8 -*-
"""Conversational Interface Package"""

from .data_loader import DataLoader, VideoMetadata
from .context_manager import ContextManager, ConversationContext, SessionMode, Message

__all__ = ['DataLoader', 'VideoMetadata', 'ContextManager', 'ConversationContext', 'SessionMode', 'Message']
__version__ = '0.1.0'
''',

    'data_loader.py': '''# -*- coding: utf-8 -*-
"""Data Loader - Unified data access interface"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class VideoMetadata:
    """Video metadata"""
    video_id: str
    title: str
    duration: float
    atom_count: int
    segment_count: int
    entity_count: int
    output_dir: Path

class DataLoader:
    """Unified data loader for all 6 data sources"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        if not self.output_dir.exists():
            raise FileNotFoundError(f"Output directory not found: {self.output_dir}")

        self.data_paths = {
            'atoms': self.output_dir / 'atoms.jsonl',
            'segments': self.output_dir / 'narrative_segments.json',
            'entities': self.output_dir / 'entities.json',
            'topics': self.output_dir / 'topics.json',
            'graph': self.output_dir / 'indexes' / 'graph.json',
            'creative': self.output_dir / 'creative_angles.json',
            'validation': self.output_dir / 'validation.json'
        }

        self._cache: Dict[str, Any] = {}
        self._loaded: Dict[str, bool] = {key: False for key in self.data_paths.keys()}

        logger.info(f"DataLoader initialized: {self.output_dir}")

    def get_atoms(self, force_reload: bool = False) -> List[Dict]:
        """Get all atoms"""
        cache_key = 'atoms'
        if not force_reload and self._loaded[cache_key]:
            return self._cache[cache_key]

        atoms_path = self.data_paths['atoms']
        if not atoms_path.exists():
            logger.warning(f"Atoms file not found: {atoms_path}")
            return []

        atoms = []
        with open(atoms_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    atoms.append(json.loads(line))

        self._cache[cache_key] = atoms
        self._loaded[cache_key] = True
        logger.info(f"Loaded {len(atoms)} atoms")
        return atoms

    def get_atom_by_id(self, atom_id: str) -> Optional[Dict]:
        """Get atom by ID"""
        atoms = self.get_atoms()
        for atom in atoms:
            if atom.get('atom_id') == atom_id:
                return atom
        return None

    def get_segments(self, force_reload: bool = False) -> List[Dict]:
        """Get all narrative segments"""
        cache_key = 'segments'
        if not force_reload and self._loaded[cache_key]:
            return self._cache[cache_key]

        segments_path = self.data_paths['segments']
        if not segments_path.exists():
            logger.warning(f"Segments file not found: {segments_path}")
            return []

        with open(segments_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        segments = data.get('segments', [])
        self._cache[cache_key] = segments
        self._loaded[cache_key] = True
        logger.info(f"Loaded {len(segments)} segments")
        return segments

    def get_entities(self, force_reload: bool = False) -> Dict:
        """Get entities data"""
        return self._load_json('entities', force_reload)

    def get_entity_by_name(self, name: str) -> Optional[Dict]:
        """Get entity by name"""
        entities_data = self.get_entities()
        entities = entities_data.get('entities', {})
        return entities.get(name)

    def get_graph(self, force_reload: bool = False) -> Dict:
        """Get knowledge graph"""
        return self._load_json('graph', force_reload)

    def get_entity_relations(self, entity_name: str) -> List[Dict]:
        """Get entity relations from graph"""
        graph_data = self.get_graph()
        edges = graph_data.get('edges', [])

        relations = []
        for edge in edges:
            if edge.get('source') == entity_name:
                relations.append({
                    'target': edge.get('target'),
                    'relation_type': edge.get('relation_type'),
                    'weight': edge.get('weight'),
                    'direction': 'outgoing'
                })
            elif edge.get('target') == entity_name:
                relations.append({
                    'target': edge.get('source'),
                    'relation_type': edge.get('relation_type'),
                    'weight': edge.get('weight'),
                    'direction': 'incoming'
                })

        relations.sort(key=lambda x: x['weight'], reverse=True)
        return relations

    def get_metadata(self) -> VideoMetadata:
        """Get video metadata"""
        atoms = self.get_atoms()
        segments = self.get_segments()
        entities_data = self.get_entities()

        duration = 0.0
        if atoms:
            last_atom = atoms[-1]
            duration = last_atom.get('end_time', 0.0)

        title = "Untitled Video"
        if segments:
            title = segments[0].get('title', title)

        return VideoMetadata(
            video_id=self.output_dir.name,
            title=title,
            duration=duration,
            atom_count=len(atoms),
            segment_count=len(segments),
            entity_count=entities_data.get('statistics', {}).get('total_entities', 0),
            output_dir=self.output_dir
        )

    def search_atoms_by_text(self, query: str, case_sensitive: bool = False) -> List[Dict]:
        """Search atoms by text content"""
        atoms = self.get_atoms()
        results = []

        if not case_sensitive:
            query = query.lower()

        for atom in atoms:
            text = atom.get('merged_text', '')
            if not case_sensitive:
                text = text.lower()

            if query in text:
                results.append(atom)

        return results

    def _load_json(self, data_key: str, force_reload: bool = False) -> Dict:
        """Generic JSON loader"""
        if not force_reload and self._loaded[data_key]:
            return self._cache[data_key]

        file_path = self.data_paths[data_key]
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return {}

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self._cache[data_key] = data
        self._loaded[data_key] = True
        logger.info(f"Loaded {data_key}")
        return data

    def clear_cache(self):
        """Clear all caches"""
        self._cache.clear()
        self._loaded = {key: False for key in self.data_paths.keys()}

    def __repr__(self) -> str:
        metadata = self.get_metadata()
        return f"DataLoader(video_id='{metadata.video_id}', atoms={metadata.atom_count})"
''',

    'context_manager.py': '''# -*- coding: utf-8 -*-
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
'''
}

# Write all files
print("Creating conversational module files...")
for filename, content in FILES.items():
    filepath = BASE_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Created: {filepath}")

print("\\nAll files created successfully!")
print(f"Module location: {BASE_DIR}")
