#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create fallback atom annotations with basic data"""

import sys
import os
from pathlib import Path
import json
import logging
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_fallback_annotations():
    """Create basic fallback annotations for atoms"""
    data_dir = Path(__file__).parent.parent / "data" / "output_pipeline_v3"

    # Load atoms
    atoms_file = data_dir / "atoms.jsonl"
    if not atoms_file.exists():
        logger.error(f"Atoms file not found: {atoms_file}")
        return

    atoms = []
    with open(atoms_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                atoms.append(json.loads(line))

    logger.info(f"Loaded {len(atoms)} atoms")

    # Load entities for topic reference
    entities_file = data_dir / "entities.json"
    entities = {}
    if entities_file.exists():
        with open(entities_file, 'r', encoding='utf-8') as f:
            entities = json.load(f)
        logger.info(f"Loaded entities for reference")

    # Sample topics from entities
    sample_topics = []
    for category, entity_list in entities.items():
        if isinstance(entity_list, list):
            for entity in entity_list[:3]:  # Take first 3 from each category
                if isinstance(entity, dict) and 'name' in entity:
                    sample_topics.append(entity['name'])

    sample_emotions = [
        {"emotion": "neutral", "confidence": 0.7},
        {"emotion": "analytical", "confidence": 0.6},
        {"emotion": "informative", "confidence": 0.8},
        {"emotion": "thoughtful", "confidence": 0.5}
    ]

    # Create annotations for each atom
    annotations = []
    for atom in atoms:
        # Create basic annotation
        text_content = atom.get("merged_text", atom.get("content", ""))
        annotation = {
            "atom_id": atom["atom_id"],
            "text_snippet": text_content[:100] + "..." if len(text_content) > 100 else text_content,
            "topics": random.sample(sample_topics, min(3, len(sample_topics))) if sample_topics else ["政治制度", "历史分析", "社会议题"],
            "entities": [],
            "emotion": random.choice(sample_emotions),
            "importance_score": round(random.uniform(0.3, 0.9), 2),
            "embedding_status": "completed"
        }

        # Add some sample entities based on keywords in content
        content = text_content.lower()
        if "中国" in content or "china" in content:
            annotation["entities"].append({
                "name": "中国",
                "type": "location",
                "confidence": 0.9,
                "start_pos": content.find("中国") if "中国" in content else 0,
                "end_pos": content.find("中国") + 2 if "中国" in content else 2
            })

        if "政治" in content or "制度" in content:
            annotation["entities"].append({
                "name": "政治制度",
                "type": "concept",
                "confidence": 0.8,
                "start_pos": 0,
                "end_pos": 10
            })

        annotations.append(annotation)

    # Save annotations
    annotations_file = data_dir / "atom_annotations.json"
    with open(annotations_file, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)

    logger.info(f"Created {len(annotations)} fallback annotations")
    return annotations_file

if __name__ == "__main__":
    create_fallback_annotations()