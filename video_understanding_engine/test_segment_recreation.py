#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from api.segment_manager import SegmentManager

# Test the segment manager locally
data_dir = Path("data/output_pipeline_v3")
manager = SegmentManager(data_dir, segment_duration_minutes=20)

# Load atoms and see what we get
atoms = manager.load_atoms()
print(f"Loaded {len(atoms)} atoms")

# Test the create_time_segments method
segments = manager.create_time_segments(atoms)
print(f"Created {len(segments)} segments")

# Check first segment's atom IDs
if segments:
    print(f"\nFirst segment atom_ids: {segments[0].atom_ids[:10]}")
    print(f"First segment duration: {segments[0].duration_ms}ms")
    print(f"Time range: {segments[0].start_time_str} - {segments[0].end_time_str}")

    if len(segments) > 1:
        print(f"\nSecond segment atom_ids: {segments[1].atom_ids[:10]}")
        print(f"Second segment duration: {segments[1].duration_ms}ms")
        print(f"Time range: {segments[1].start_time_str} - {segments[1].end_time_str}")