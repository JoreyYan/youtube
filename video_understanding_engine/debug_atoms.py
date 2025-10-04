#!/usr/bin/env python3
import json
from pathlib import Path

# Load atoms and check timestamps
atoms_file = Path("data/output_pipeline_v3/atoms.jsonl")
atoms = []

with open(atoms_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            atoms.append(json.loads(line))

print(f"Total atoms: {len(atoms)}")

# Check first 10 atoms
print("\nFirst 10 atoms:")
for i, atom in enumerate(atoms[:10]):
    start_ms = atom.get('start_ms', 'N/A')
    end_ms = atom.get('end_ms', 'N/A')
    print(f"{atom['atom_id']}: {start_ms}ms - {end_ms}ms")

# Check atoms around 20 minutes (1200000ms)
print(f"\nAtoms around 20 minutes (1200000ms):")
for atom in atoms:
    start_ms = atom.get('start_ms', 0)
    if 1180000 <= start_ms <= 1220000:
        print(f"{atom['atom_id']}: {start_ms}ms - {atom.get('end_ms', 'N/A')}ms")

# Find max timestamp
max_ms = max(atom.get('end_ms', 0) for atom in atoms)
print(f"\nMax timestamp: {max_ms}ms ({max_ms/1000/60:.1f} minutes)")

# Check different time ranges
ranges = [(0, 1200000), (1200000, 2400000), (2400000, 3600000)]
for start, end in ranges:
    count = len([a for a in atoms if start <= a.get('start_ms', 0) < end])
    print(f"Range {start/1000/60:.0f}-{end/1000/60:.0f} minutes: {count} atoms")