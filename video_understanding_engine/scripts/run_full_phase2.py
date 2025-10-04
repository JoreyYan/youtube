# -*- coding: utf-8 -*-
"""Run Phase 2 analysis on full 342 atoms"""

import json
import sys
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers.entity_extractor import EntityExtractor
from analyzers.topic_network_builder import TopicNetworkBuilder
from analyzers.knowledge_graph_builder import KnowledgeGraphBuilder

def load_atoms():
    """Load all 342 atoms"""
    atoms_file = Path("data/output/atoms_full.jsonl")
    atoms = []
    with open(atoms_file, 'r', encoding='utf-8') as f:
        for line in f:
            atoms.append(json.loads(line))
    return atoms

def create_mock_segment(atoms, segment_id="FULL"):
    """Create mock segment object for analysis"""
    class MockAtom:
        def __init__(self, data):
            self.atom_id = data['atom_id']
            self.merged_text = data['merged_text']
            self.start_ms = data.get('start_ms', 0)
            self.end_ms = data.get('end_ms', 0)

    class MockEntities:
        def __init__(self):
            self.persons = []
            self.countries = []
            self.organizations = []
            self.time_points = []
            self.events = []
            self.concepts = []

    class MockNarrative:
        def __init__(self):
            self.primary_topic = "金三角历史与缅北双雄时代"
            self.secondary_topics = []
            self.tags = []

    class MockSegment:
        def __init__(self, atoms, seg_id):
            self.segment_id = seg_id
            self.atoms = [MockAtom(a) for a in atoms]
            self.entities = MockEntities()
            self.narrative_arc = MockNarrative()
            self.full_text = " ".join([a['merged_text'] for a in atoms])

    return MockSegment(atoms, segment_id)

def main():
    print("=" * 70)
    print("Full Phase 2 Analysis - 342 Atoms")
    print("=" * 70)

    # Load atoms
    print("\n[1/4] Loading atoms...")
    atoms = load_atoms()
    print(f"  Loaded {len(atoms)} atoms")

    # Create segments (split into chunks to avoid token limits)
    print("\n[2/4] Creating analysis segments...")
    chunk_size = 50  # Process 50 atoms at a time
    segments = []

    for i in range(0, len(atoms), chunk_size):
        chunk = atoms[i:i+chunk_size]
        seg_id = f"CHUNK_{i//chunk_size + 1:03d}"
        segments.append(create_mock_segment(chunk, seg_id))
        print(f"  Created {seg_id}: {len(chunk)} atoms")

    print(f"\n  Total: {len(segments)} segments")

    # Extract entities
    print("\n[3/4] Extracting entities...")
    extractor = EntityExtractor()

    all_entities = {
        'persons': {},
        'countries': {},
        'organizations': {},
        'time_points': {},
        'events': {},
        'concepts': {}
    }

    for seg in tqdm(segments, desc="Processing segments"):
        result = extractor.extract([seg])

        # Merge results
        for entity_type in all_entities.keys():
            for entity in result.get(entity_type, []):
                name = entity['name']
                if name not in all_entities[entity_type]:
                    all_entities[entity_type][name] = entity
                else:
                    # Merge atoms and segments
                    existing = all_entities[entity_type][name]
                    existing['mentions'] += entity.get('mentions', 1)
                    existing['atoms'] = list(set(existing.get('atoms', []) + entity.get('atoms', [])))
                    existing['segments'] = list(set(existing.get('segments', []) + entity.get('segments', [])))

    # Convert back to lists
    final_entities = {}
    for entity_type, entities_dict in all_entities.items():
        final_entities[entity_type] = list(entities_dict.values())

    # Calculate statistics
    final_entities['statistics'] = {
        'total_entities': sum(len(entities) for entities in final_entities.values() if isinstance(entities, list)),
        'by_type': {k: len(v) for k, v in final_entities.items() if isinstance(v, list)}
    }

    # Save entities
    print("\n[4/4] Saving results...")
    output_dir = Path("data/output_pipeline_v3")
    output_dir.mkdir(parents=True, exist_ok=True)

    entities_file = output_dir / "entities.json"
    with open(entities_file, 'w', encoding='utf-8') as f:
        json.dump(final_entities, f, ensure_ascii=False, indent=2)

    print(f"  [OK] Entities saved: {entities_file}")

    # Print summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"\nTotal entities: {final_entities['statistics']['total_entities']}")
    print("\nBy type:")
    for entity_type, count in final_entities['statistics']['by_type'].items():
        print(f"  {entity_type}: {count}")

    # Show top entities by mentions
    print("\nTop entities by mentions:")
    all_entity_list = []
    for entity_type in ['persons', 'countries', 'events', 'concepts']:
        for entity in final_entities.get(entity_type, []):
            all_entity_list.append((entity['name'], entity.get('mentions', 0), entity_type, len(entity.get('atoms', []))))

    all_entity_list.sort(key=lambda x: x[1], reverse=True)
    for name, mentions, etype, atom_count in all_entity_list[:20]:
        print(f"  {name} ({etype}): {mentions} mentions, {atom_count} atoms")

if __name__ == "__main__":
    main()
