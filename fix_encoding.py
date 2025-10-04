#!/usr/bin/env python3
"""Fix character encoding in atoms.jsonl by copying from correct source"""

import json
import shutil
from pathlib import Path

def main():
    # Paths
    source_file = Path("video_understanding_engine/data/output/atoms_full.jsonl")
    target_file = Path("video_understanding_engine/data/output_pipeline_v3/atoms.jsonl")
    backup_file = Path("video_understanding_engine/data/output_pipeline_v3/atoms_backup.jsonl")

    print("=== CHARACTER ENCODING FIX ===")

    # Backup current file
    if target_file.exists():
        shutil.copy2(target_file, backup_file)
        print(f"✅ Backed up current atoms.jsonl to atoms_backup.jsonl")

    if not source_file.exists():
        print(f"❌ Source file not found: {source_file}")
        return

    # Read source and verify encoding
    with open(source_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"📖 Source file has {len(lines)} lines")

    # Test first few lines to verify Chinese characters
    for i, line in enumerate(lines[:3]):
        if line.strip():
            atom = json.loads(line)
            text = atom.get('merged_text', '')
            print(f"Line {i+1}: {text[:50]}...")

            # Check if Chinese characters are properly displayed
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
            print(f"  Chinese characters detected: {has_chinese}")

    # Copy the corrected file
    shutil.copy2(source_file, target_file)
    print(f"✅ Copied correctly encoded atoms from {source_file}")
    print(f"   to {target_file}")

    # Verify the copy
    with open(target_file, 'r', encoding='utf-8') as f:
        test_line = f.readline()
        if test_line.strip():
            atom = json.loads(test_line)
            text = atom.get('merged_text', '')
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
            print(f"✅ Verification: Chinese characters in target: {has_chinese}")
            print(f"   Sample text: {text[:50]}...")

if __name__ == "__main__":
    main()