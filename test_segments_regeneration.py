#!/usr/bin/env python3
"""Test script to trigger segments regeneration"""

import sys
from pathlib import Path

# Add video_understanding_engine to path
sys.path.insert(0, str(Path(__file__).parent / 'video_understanding_engine'))

from api.segment_manager import SegmentManager

def test_segments_regeneration():
    """Test segments regeneration with index-based atom IDs"""
    data_dir = Path("video_understanding_engine/data/output_pipeline_v3")
    segment_manager = SegmentManager(data_dir, segment_duration_minutes=20)

    print("Loading atoms...")
    atoms = segment_manager.load_atoms()
    print(f"Loaded {len(atoms)} atoms")

    if atoms:
        print(f"First 3 atoms:")
        for i, atom in enumerate(atoms[:3]):
            print(f"  Index {i}: atom_id={atom['atom_id']}, start_ms={atom['start_ms']}, text={atom['merged_text'][:50]}")

    print("\nLoading/creating segments...")
    segments = segment_manager.load_segments_state()
    print(f"Created {len(segments)} segments")

    if segments:
        print(f"\nFirst segment:")
        seg = segments[0]
        print(f"  segment_id: {seg.segment_id}")
        print(f"  start_ms: {seg.start_ms}")
        print(f"  end_ms: {seg.end_ms}")
        print(f"  atom_ids (first 5): {seg.atom_ids[:5]}")
        print(f"  atom_ids type: {type(seg.atom_ids[0]) if seg.atom_ids else 'empty'}")

    print("\nDone!")

if __name__ == "__main__":
    test_segments_regeneration()