#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate atom annotations for analyzed segments"""

import sys
import os
from pathlib import Path
import json
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers.atom_annotator import AtomAnnotator
from api.segment_manager import SegmentManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Generate atom annotations for all analyzed segments"""
    data_dir = Path(__file__).parent.parent / "data" / "output_pipeline_v3"

    # Load segments state
    segment_manager = SegmentManager(data_dir, segment_duration_minutes=20)
    segments = segment_manager.load_segments_state()

    # Filter analyzed segments
    analyzed_segments = [seg for seg in segments if seg.analysis_complete]
    logger.info(f"Found {len(analyzed_segments)} analyzed segments")

    if not analyzed_segments:
        logger.warning("No analyzed segments found. Please analyze segments first.")
        return

    # Initialize atom annotator
    annotator = AtomAnnotator(data_dir)

    # Load all atoms
    atoms_file = data_dir / "atoms.jsonl"
    if not atoms_file.exists():
        logger.error(f"Atoms file not found: {atoms_file}")
        return

    atoms = []
    with open(atoms_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                atoms.append(json.loads(line))

    logger.info(f"Loaded {len(atoms)} total atoms")

    # Process each analyzed segment
    all_annotations = []

    for segment in analyzed_segments:
        logger.info(f"Annotating segment {segment.segment_id}")

        # Get atoms for this segment
        segment_atoms = [atom for atom in atoms if atom['atom_id'] in segment.atom_ids]
        logger.info(f"  Found {len(segment_atoms)} atoms in segment")

        # Annotate atoms for this segment
        try:
            annotations = annotator.annotate_atoms_batch(segment_atoms, segment.segment_id, batch_size=10)
            all_annotations.extend(annotations)
            logger.info(f"  Generated {len(annotations)} annotations")
        except Exception as e:
            logger.error(f"  Failed to annotate segment {segment.segment_id}: {e}")
            continue

    # Save all annotations
    annotations_file = data_dir / "atom_annotations.json"
    with open(annotations_file, 'w', encoding='utf-8') as f:
        json.dump(all_annotations, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(all_annotations)} atom annotations to {annotations_file}")

if __name__ == "__main__":
    main()