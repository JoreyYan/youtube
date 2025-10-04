#!/usr/bin/env python3
import json
from pathlib import Path
from collections import defaultdict

# Load atoms and check for duplicates
atoms_file = Path("data/output_pipeline_v3/atoms.jsonl")
atoms = []

with open(atoms_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            atoms.append(json.loads(line))

print(f"Total atoms: {len(atoms)}")

# Check for duplicate atom_ids
id_counts = defaultdict(list)
for i, atom in enumerate(atoms):
    atom_id = atom['atom_id']
    id_counts[atom_id].append((i, atom.get('start_ms', 0)))

print("\nDuplicate atom_ids:")
duplicates_found = 0
for atom_id, instances in id_counts.items():
    if len(instances) > 1:
        duplicates_found += 1
        print(f"{atom_id}: {len(instances)} instances")
        for idx, start_ms in instances:
            print(f"  Index {idx}: start_ms={start_ms}")
        if duplicates_found > 10:  # Limit output
            break

print(f"\nTotal duplicate atom_ids: {len([k for k, v in id_counts.items() if len(v) > 1])}")

# Check unique atom_ids
unique_ids = set(atom['atom_id'] for atom in atoms)
print(f"Unique atom_ids: {len(unique_ids)}")

# Show distribution of first 50 atoms
print("\nFirst 50 atoms distribution:")
for i, atom in enumerate(atoms[:50]):
    start_ms = atom.get('start_ms', 0)
    print(f"{i+1:2d}. {atom['atom_id']}: {start_ms:>7}ms ({start_ms/1000/60:5.1f}min)")