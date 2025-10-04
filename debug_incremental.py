#!/usr/bin/env python3
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "video_understanding_engine"))

# Test the exact logic from incremental_analysis_service
data_dir = Path("video_understanding_engine/data/output_pipeline_v3")

# Load atoms and segments exactly as the service does
from api.segment_manager import SegmentManager
manager = SegmentManager(data_dir, segment_duration_minutes=20)

atoms = manager.load_atoms()
segments = manager.load_segments_state()

print(f"Total atoms loaded: {len(atoms)}")
print(f"Total segments: {len(segments)}")

# Build atoms_dict as the service does
atoms_dict = {atom['atom_id']: atom for atom in atoms}
print(f"Atoms dict keys (first 5): {list(atoms_dict.keys())[:5]}")

# Test SEG_001 specifically
if segments:
    seg001 = segments[0]  # This should be SEG_001
    print(f"\nTesting {seg001.segment_id}")
    print(f"Atom IDs count: {len(seg001.atom_ids)}")
    print(f"First 5 atom IDs: {seg001.atom_ids[:5]}")

    # Test OLD logic (what's still running)
    print("\n=== OLD LOGIC (current server) ===")
    old_segment_atoms = [atoms_dict[aid] for aid in seg001.atom_ids if aid in atoms_dict]
    print(f"OLD: Found {len(old_segment_atoms)} atoms")

    # Test NEW logic (my fixed code)
    print("\n=== NEW LOGIC (fixed code) ===")
    new_segment_atoms = []
    for compound_id in seg001.atom_ids:
        if '_' in compound_id:
            try:
                atom_index = int(compound_id.split('_')[1])
                if 0 <= atom_index < len(atoms):
                    new_segment_atoms.append(atoms[atom_index])
            except (ValueError, IndexError):
                print(f"Invalid compound ID: {compound_id}")
        else:
            if compound_id in atoms_dict:
                new_segment_atoms.append(atoms_dict[compound_id])

    print(f"NEW: Found {len(new_segment_atoms)} atoms")

    if new_segment_atoms:
        print("First few resolved atoms:")
        for i, atom in enumerate(new_segment_atoms[:3]):
            print(f"  {i}: {atom['atom_id']} (start: {atom.get('start_ms', 0)}ms)")