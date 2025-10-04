# -*- coding: utf-8 -*-
"""Extract entities from full video with relevance scoring"""

import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers.entity_extractor import EntityExtractor
from models import NarrativeSegment, NarrativeStructure, Topics, Entities, ContentFacet, AIAnalysis

def main():
    print("=" * 70)
    print("提取实体并评估相关性")
    print("=" * 70)

    # Load full atoms from updated pipeline_v3 directory
    atoms_file = Path("data/output_pipeline_v3/atoms.jsonl")
    atoms = []

    if atoms_file.exists():
        with open(atoms_file, 'r', encoding='utf-8') as f:
            for line in f:
                atoms.append(json.loads(line))
        print(f"[OK] Loaded {len(atoms)} atoms")
    else:
        print("[ERROR] atoms_full.jsonl not found")
        return

    # Create a single segment with all atoms
    # Calculate time range
    start_ms = min(atom['start_ms'] for atom in atoms) if atoms else 0
    end_ms = max(atom['end_ms'] for atom in atoms) if atoms else 0
    duration_ms = end_ms - start_ms

    # Combine all atom texts
    full_text = " ".join(atom['merged_text'] for atom in atoms)
    atom_ids = [atom['atom_id'] for atom in atoms]

    segment = NarrativeSegment(
        segment_id="FULL_VIDEO",
        title="金三角历史与缅北双雄时代完整视频",
        atoms=atom_ids,
        start_ms=start_ms,
        end_ms=end_ms,
        duration_ms=duration_ms,
        summary="完整视频的实体提取分析，涵盖金三角历史和缅北双雄时代的所有内容",
        full_text=full_text,
        narrative_structure=NarrativeStructure(
            type="历史叙事",
            structure="历史背景→人物介绍→事件发展→影响分析",
            acts=[]
        ),
        topics=Topics(
            primary_topic="金三角历史与缅北双雄时代",
            secondary_topics=["昆沙", "坤沙", "缅甸", "毒品贸易", "历史人物"],
            free_tags=[]
        ),
        entities=Entities(),  # Will be filled by the extractor
        content_facet=ContentFacet(
            type="历史叙述",
            aspect="历史事件全景",
            stance="中立客观"
        ),
        ai_analysis=AIAnalysis(
            core_argument="金三角历史的复杂性和缅北双雄时代的重要影响",
            key_insights=[],
            logical_flow="时间线叙述，从历史背景到人物故事",
            suitable_for_reuse=True,
            reuse_suggestions=[]
        ),
        importance_score=1.0,
        quality_score=1.0
    )

    # Extract entities
    print("\n开始提取实体...")
    extractor = EntityExtractor()
    entities_result = extractor.extract([segment])

    # Save to output_pipeline_v3
    output_dir = Path("data/output_pipeline_v3")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "entities.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(entities_result, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Saved entities to: {output_file}")

    # Print statistics
    print("\n" + "=" * 70)
    print("统计信息")
    print("=" * 70)

    stats = entities_result.get('statistics', {})
    print(f"\n总实体数: {stats.get('total_entities', 0)}")
    print(f"\n按类型统计:")
    for entity_type, count in stats.get('by_type', {}).items():
        print(f"  {entity_type}: {count}")

    # Show examples of each type
    for entity_type in ['persons', 'countries', 'organizations', 'events', 'concepts']:
        entities_list = entities_result.get(entity_type, [])
        if entities_list:
            print(f"\n{entity_type} 示例 (前5个):")
            for entity in entities_list[:5]:
                mentions = entity.get('mentions', 0)
                atoms = entity.get('atoms', [])
                print(f"  - {entity['name']}: {mentions}次提及, 出现在{len(atoms)}个原子中")
                if atoms:
                    print(f"    原子: {', '.join(atoms[:5])}")

if __name__ == "__main__":
    main()
