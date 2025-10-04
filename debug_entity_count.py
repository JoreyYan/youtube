#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证罗星汉的实体计数"""

import json
from pathlib import Path

def verify_entity_count():
    atoms_file = Path("D:/code/youtube/video_understanding_engine/data/output/atoms_full.jsonl")

    if not atoms_file.exists():
        print("atoms_full.jsonl not found")
        return

    atoms = []
    with open(atoms_file, 'r', encoding='utf-8') as f:
        for line in f:
            atoms.append(json.loads(line.strip()))

    print(f"Total atoms: {len(atoms)}")

    # 罗星汉出现的原子ID列表（从API返回）
    target_atom_ids = ["A245","A164","A173","A144","A150","A036","A071","A043","A134","A169","A280","A106","A031","A224","A042","A184","A072","A076","A160","A161","A292","A118","A163","A153","A079","A155","A294","A179","A181","A207","A135","A154","A278","A293","A260","A059","A075","A145","A214","A288","A060","A162","A143","A244","A112","A018","A156","A158","A107","A168","A029","A300","A167","A218","A067","A141","A082","A061","A116","A131","A190","A121","A073","A104","A299","A147","A094","A115","A174","A267","A289","A066","A157","A038","A311","A055","A146","A052","A065","A139","A064","A125","A286","A208","A170","A113","A239","A279","A103","A120","A275","A182","A074","A291","A290","A050","A178","A027","A281","A159","A138","A124","A122","A295","A054","A287","A041"]

    total_mentions = 0
    found_atoms = 0

    print(f"Expected atom count: {len(target_atom_ids)}")

    for atom in atoms:
        if atom['atom_id'] in target_atom_ids:
            text = atom['merged_text']
            # 计算在该原子中的出现次数
            count_in_atom = 0
            count_in_atom += text.count("罗星汉")
            count_in_atom += text.count("罗兴汉")  # 星/兴变体

            if count_in_atom > 0:
                found_atoms += 1
                total_mentions += count_in_atom
                if count_in_atom > 1:
                    print(f"{atom['atom_id']}: {count_in_atom} mentions")
                    print(f"  Text: {text[:100]}...")
                    print()

    print(f"Found atoms: {found_atoms}")
    print(f"Total mentions: {total_mentions}")

    # 验证几个特定原子
    print("\n=== 验证特定原子 ===")
    sample_atoms = ["A245", "A164", "A031"]
    for atom_id in sample_atoms:
        atom = next((a for a in atoms if a['atom_id'] == atom_id), None)
        if atom:
            text = atom['merged_text']
            count = text.count("罗星汉") + text.count("罗兴汉")
            print(f"{atom_id}: {count} mentions")
            print(f"  Text: {text}")
            print()

if __name__ == "__main__":
    verify_entity_count()