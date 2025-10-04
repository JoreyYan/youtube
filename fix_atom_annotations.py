#!/usr/bin/env python3
"""Fix atom annotations to use new unique atom IDs"""

import json
import shutil
from pathlib import Path

def main():
    # Paths
    annotations_file = Path("video_understanding_engine/data/output_pipeline_v3/atom_annotations.json")
    mapping_file = Path("video_understanding_engine/data/output_pipeline_v3/compound_id_mapping.json")
    backup_file = Path("video_understanding_engine/data/output_pipeline_v3/atom_annotations_backup.json")

    print("=== FIXING ATOM ANNOTATIONS WITH NEW IDs ===")

    # Backup current file
    if annotations_file.exists():
        shutil.copy2(annotations_file, backup_file)
        print(f"[OK] Backed up atom_annotations.json to atom_annotations_backup.json")

    # Load mapping
    if not mapping_file.exists():
        print(f"[ERROR] Mapping file not found: {mapping_file}")
        return

    with open(mapping_file, 'r', encoding='utf-8') as f:
        compound_mapping = json.load(f)

    print(f"[OK] Loaded {len(compound_mapping)} compound ID mappings")

    # Load annotations
    with open(annotations_file, 'r', encoding='utf-8') as f:
        annotations = json.load(f)

    print(f"[OK] Loaded {len(annotations)} atom annotations")

    # Update atom IDs in annotations
    updated_count = 0
    not_found_count = 0

    for annotation in annotations:
        old_atom_id = annotation['atom_id']

        # Find the compound ID that starts with this atom ID
        # We need to find which compound ID corresponds to this annotation
        matching_compound_ids = [cid for cid in compound_mapping.keys() if cid.startswith(old_atom_id + "_")]

        if matching_compound_ids:
            # For now, take the first matching compound ID
            # This is a simplification - in reality we might need more sophisticated mapping
            compound_id = matching_compound_ids[0]
            new_atom_id = compound_mapping[compound_id]

            annotation['atom_id'] = new_atom_id
            annotation['original_atom_id'] = old_atom_id  # Keep reference to original
            annotation['compound_id'] = compound_id  # Keep compound ID for reference
            updated_count += 1

            if updated_count <= 5:  # Show first 5 examples
                print(f"  {old_atom_id} ({compound_id}) -> {new_atom_id}")
        else:
            not_found_count += 1
            if not_found_count <= 3:  # Show first 3 examples of not found
                print(f"  [WARNING] No mapping found for: {old_atom_id}")

    print(f"\n[OK] Updated {updated_count} atom annotations")
    if not_found_count > 0:
        print(f"[WARNING] {not_found_count} annotations could not be mapped")

    # Write updated annotations
    with open(annotations_file, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)

    print(f"[OK] Saved updated annotations to: {annotations_file}")

if __name__ == "__main__":
    main()