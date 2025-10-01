"""测试 QdrantVectorStore"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vectorstores import QdrantVectorStore
import json

def main():
    print("\n" + "="*70)
    print("[TEST] QdrantVectorStore")
    print("="*70)

    # 创建向量存储
    store = QdrantVectorStore(location=":memory:", collection_name="test_atoms")
    print("\n[OK] VectorStore initialized (in-memory mode)")

    # 创建collection
    store.create_collection(dimension=1536, recreate=True)
    print("[OK] Collection created (dimension=1536)")

    # 加载测试数据
    test_file = Path("data/output_semantic_test/test_embeddings.json")
    with open(test_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)

    # 加载原子数据
    atoms_file = Path("data/output_semantic_test/atoms.jsonl")
    atoms = []
    with open(atoms_file, 'r', encoding='utf-8') as f:
        for line in f:
            atoms.append(json.loads(line))

    # 插入向量
    test_atoms = atoms[:10]
    test_embeddings = test_data['embeddings']

    count = store.insert_atoms(test_atoms, test_embeddings)
    print(f"[OK] Inserted {count} atoms")

    # 搜索测试
    query_vector = test_embeddings[0]
    results = store.search(query_vector, limit=5)

    print(f"\n[OK] Search returned {len(results)} results")
    print(f"  Top result score: {results[0]['score']:.4f}")
    print(f"  Top result atom_id: {results[0]['payload']['atom_id']}")

    # 统计信息
    stats = store.get_stats()
    print(f"\n[OK] Collection stats:")
    print(f"  Points: {stats['points_count']}")
    print(f"  Dimension: {stats['dimension']}")

    print("\n[SUCCESS] All tests passed!")

if __name__ == "__main__":
    main()
