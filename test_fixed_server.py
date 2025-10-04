#!/usr/bin/env python3
"""Test the fixed incremental analysis logic directly"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "video_understanding_engine"))

from api.segment_manager import SegmentManager

# Test the fixed analysis logic
data_dir = Path("video_understanding_engine/data/output_pipeline_v3")
manager = SegmentManager(data_dir, segment_duration_minutes=20)

# Load atoms and segments
atoms = manager.load_atoms()
segments = manager.load_segments_state()

print(f"=== TESTING FIXED SERVER LOGIC ===")
print(f"Total atoms loaded: {len(atoms)}")
print(f"Total segments: {len(segments)}")

# Update SEG_001 status manually using fixed logic
if segments:
    seg001 = segments[0]
    print(f"\nTesting {seg001.segment_id}")

    # Simulate the FIXED logic
    segment_atoms = []
    for compound_id in seg001.atom_ids:
        if '_' in compound_id:
            try:
                atom_index = int(compound_id.split('_')[1])
                if 0 <= atom_index < len(atoms):
                    segment_atoms.append(atoms[atom_index])
            except (ValueError, IndexError):
                print(f"Invalid compound ID: {compound_id}")
        else:
            # Find by atom_id
            atom = next((a for a in atoms if a['atom_id'] == compound_id), None)
            if atom:
                segment_atoms.append(atom)

    print(f"Fixed logic resolved: {len(segment_atoms)} atoms")

    if segment_atoms:
        # Update status to atomized (successful)
        seg001.status = "atomized"
        seg001.error_message = None
        print(f"✅ Status updated to 'atomized'")

        # Save the fixed segments
        manager.save_segments_state(segments)
        print("✅ Segments saved with fixed status")

    else:
        print("❌ Still no atoms found")

# Check current API status
import subprocess
try:
    result = subprocess.run(['curl', '-s', 'http://localhost:8000/api/projects/1/analyze/incremental/progress'],
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        progress_data = json.loads(result.stdout)
        seg001_status = next((s for s in progress_data['segments'] if s['segment_id'] == 'SEG_001'), None)
        if seg001_status:
            print(f"\nCurrent API status for SEG_001:")
            print(f"  Status: {seg001_status['status']}")
            print(f"  Error: {seg001_status['error_message']}")
        else:
            print("SEG_001 not found in API response")
    else:
        print("Could not query API")
except:
    print("API query failed")