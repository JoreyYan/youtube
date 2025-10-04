#!/usr/bin/env python3
"""Fix atom ID duplication by creating truly unique IDs"""

import json
import shutil
from pathlib import Path

def main():
    # Paths
    atoms_file = Path("video_understanding_engine/data/output_pipeline_v3/atoms.jsonl")
    backup_file = Path("video_understanding_engine/data/output_pipeline_v3/atoms_backup_duplicates.jsonl")

    print("=== FIXING ATOM ID DUPLICATION ===")

    # Backup current file
    if atoms_file.exists():
        shutil.copy2(atoms_file, backup_file)
        print(f"Backed up atoms.jsonl to atoms_backup_duplicates.jsonl")

    # Load all atoms
    atoms = []
    with open(atoms_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                atoms.append(json.loads(line))

    print(f"Loaded {len(atoms)} atoms")

    # Create mapping from old compound IDs to new unique IDs
    compound_id_mapping = {}

    # Generate new unique atom IDs
    for i, atom in enumerate(atoms):
        old_id = atom['atom_id']
        new_unique_id = f"ATOM_{i+1:04d}"  # ATOM_0001, ATOM_0002, etc.

        # Create compound ID mapping for segment reference updates
        compound_id = f"{old_id}_{i}"
        compound_id_mapping[compound_id] = new_unique_id

        # Update the atom with new unique ID
        atom['atom_id'] = new_unique_id
        atom['original_atom_id'] = old_id  # Keep reference to original for debugging
        atom['compound_id'] = compound_id  # Keep compound ID for reference

    print(f"Generated {len(set(atom['atom_id'] for atom in atoms))} unique atom IDs")

    # Write updated atoms file
    with open(atoms_file, 'w', encoding='utf-8') as f:
        for atom in atoms:
            f.write(json.dumps(atom, ensure_ascii=False) + '\n')

    print("Updated atoms.jsonl with unique IDs")

    # Create compound ID mapping file for segment updates
    mapping_file = Path("video_understanding_engine/data/output_pipeline_v3/compound_id_mapping.json")
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(compound_id_mapping, f, ensure_ascii=False, indent=2)

    print(f"Created compound ID mapping: {mapping_file}")

    # Show sample of changes
    print("\\nSample ID changes:")
    for i in range(min(10, len(atoms))):
        atom = atoms[i]
        print(f"  {atom['original_atom_id']} ({atom['compound_id']}) -> {atom['atom_id']}")

if __name__ == "__main__":
    main()