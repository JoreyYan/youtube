#!/usr/bin/env python3
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "video_understanding_engine"))

from api.segment_manager import SegmentManager

# Test compound ID handling
data_dir = Path("video_understanding_engine/data/output_pipeline_v3")
manager = SegmentManager(data_dir, segment_duration_minutes=20)

# Load atoms and segments
atoms = manager.load_atoms()
segments = manager.load_segments_state()

print(f"Total atoms loaded: {len(atoms)}")
print(f"Total segments: {len(segments)}")

# Test first segment
if segments:
    first_segment = segments[0]
    print(f"\nFirst segment: {first_segment.segment_id}")
    print(f"Atom IDs count: {len(first_segment.atom_ids)}")
    print(f"First 5 atom IDs: {first_segment.atom_ids[:5]}")

    # Test compound ID resolution
    found_atoms = 0
    for compound_id in first_segment.atom_ids[:5]:
        if '_' in compound_id:
            try:
                atom_index = int(compound_id.split('_')[1])
                if 0 <= atom_index < len(atoms):
                    atom = atoms[atom_index]
                    print(f"  {compound_id} -> Index {atom_index} -> {atom['atom_id']} (start: {atom.get('start_ms', 0)}ms)")
                    found_atoms += 1
            except (ValueError, IndexError):
                print(f"  {compound_id} -> FAILED to resolve")

    print(f"Successfully resolved: {found_atoms}/{len(first_segment.atom_ids[:5])}")