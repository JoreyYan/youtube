# -*- coding: utf-8 -*-
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

        # Handle both list and dict formats
        if isinstance(data, list):
            segments = data
        else:
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
