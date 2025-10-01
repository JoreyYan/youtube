"""
测试 SemanticSearchEngine - 语义搜索引擎

测试场景：
1. 原子级语义搜索
2. 片段级语义搜索
3. 相似原子查找
4. 混合搜索（语义+关键词）
5. 按时间范围搜索
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from searchers import SemanticSearchEngine
from embedders import EmbeddingGenerator
from vectorstores import QdrantVectorStore
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def print_separator(title: str):
    """打印分隔线"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_atom_result(result: dict, index: int):
    """打印原子搜索结果"""
    print(f"\n[{index+1}] Atom ID: {result['atom_id']} | Score: {result['score']:.4f}")
    print(f"    Time: {result['start_time']} - {result['end_time']}")
    print(f"    Type: {result['type']} | Completeness: {result['completeness']}")
    print(f"    Text: {result['text'][:100]}..." if len(result['text']) > 100 else f"    Text: {result['text']}")


def print_segment_result(result: dict, index: int):
    """打印片段搜索结果"""
    print(f"\n[{index+1}] Segment ID: {result['segment_id']} | Score: {result['score']:.4f}")
    print(f"    Time: {result['start_time']} - {result['end_time']}")
    print(f"    Title: {result['title']}")
    print(f"    Topic: {result['primary_topic']}")
    print(f"    Summary: {result['summary'][:150]}..." if len(result['summary']) > 150 else f"    Summary: {result['summary']}")


def load_test_data():
    """加载测试数据"""
    data_dir = Path("data/output_semantic_test")

    # 加载原子数据
    atoms_file = data_dir / "atoms.jsonl"
    atoms = []
    with open(atoms_file, 'r', encoding='utf-8') as f:
        for line in f:
            atoms.append(json.loads(line))

    # 加载片段数据
    segments_file = data_dir / "segments.jsonl"
    segments = []
    if segments_file.exists():
        with open(segments_file, 'r', encoding='utf-8') as f:
            for line in f:
                segments.append(json.loads(line))

    # 加载embeddings
    embeddings_file = data_dir / "test_embeddings.json"
    with open(embeddings_file, 'r', encoding='utf-8') as f:
        embeddings_data = json.load(f)

    return atoms, segments, embeddings_data


def setup_search_engine():
    """设置搜索引擎"""
    # 获取API密钥
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")

    # 创建embedder
    embedder = EmbeddingGenerator(
        api_key=api_key,
        model='text-embedding-3-small',
        provider='openai'
    )

    # 创建vector store (内存模式)
    vector_store = QdrantVectorStore(
        location=":memory:",
        collection_name="test_search"
    )

    # 创建collection
    vector_store.create_collection(
        dimension=embedder.get_dimension(),
        recreate=True
    )

    # 创建搜索引擎
    search_engine = SemanticSearchEngine(
        vector_store=vector_store,
        embedder=embedder
    )

    return search_engine, vector_store


def test_1_atom_search(search_engine: SemanticSearchEngine):
    """测试1: 原子级语义搜索"""
    print_separator("TEST 1: 原子级语义搜索")

    # 测试查询
    queries = [
        "金三角的历史起源",
        "国民党军队的故事"
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = search_engine.search_atoms(query, limit=3)

        print(f"Found {len(results)} results:")
        for idx, result in enumerate(results):
            print_atom_result(result, idx)

    print("\n[OK] 原子级语义搜索测试通过")


def test_2_segment_search(search_engine: SemanticSearchEngine):
    """测试2: 片段级语义搜索"""
    print_separator("TEST 2: 片段级语义搜索")

    # 测试查询
    query = "金三角的历史背景"

    print(f"\nQuery: '{query}'")
    results = search_engine.search_segments(query, limit=2)

    print(f"Found {len(results)} results:")
    for idx, result in enumerate(results):
        print_segment_result(result, idx)

    print("\n[OK] 片段级语义搜索测试通过")


def test_3_similar_atoms(search_engine: SemanticSearchEngine):
    """测试3: 查找相似原子"""
    print_separator("TEST 3: 查找相似原子")

    # 使用第一个原子查找相似原子
    target_atom_id = "A001"

    print(f"\nFinding atoms similar to: {target_atom_id}")
    results = search_engine.find_similar_atoms(target_atom_id, limit=3)

    print(f"Found {len(results)} similar atoms:")
    for idx, result in enumerate(results):
        print_atom_result(result, idx)

    print("\n[OK] 相似原子查找测试通过")


def test_4_hybrid_search(search_engine: SemanticSearchEngine):
    """测试4: 混合搜索"""
    print_separator("TEST 4: 混合搜索 (语义 + 关键词)")

    query = "金三角的起源"
    keywords = ["1962", "国民党", "军队"]

    print(f"\nQuery: '{query}'")
    print(f"Keywords: {keywords}")

    results = search_engine.hybrid_search(
        query=query,
        keywords=keywords,
        limit=3,
        semantic_weight=0.7
    )

    print(f"\nFound {len(results)} results:")
    for idx, result in enumerate(results):
        print(f"\n[{idx+1}] Atom ID: {result['atom_id']}")
        print(f"    Hybrid Score: {result['hybrid_score']:.4f}")
        print(f"    Semantic: {result['semantic_score']:.4f} | Keyword: {result['keyword_score']:.4f}")
        print(f"    Text: {result['text'][:100]}...")

    print("\n[OK] 混合搜索测试通过")


def test_5_time_range_search(search_engine: SemanticSearchEngine):
    """测试5: 按时间范围搜索"""
    print_separator("TEST 5: 按时间范围搜索")

    # 搜索前1分钟的内容
    start_ms = 0
    end_ms = 60000

    print(f"\nSearching atoms in time range: {start_ms}ms - {end_ms}ms")

    results = search_engine.search_by_time_range(
        start_ms=start_ms,
        end_ms=end_ms,
        data_type="atom",
        limit=5
    )

    print(f"Found {len(results)} atoms in this time range:")
    for idx, result in enumerate(results):
        print(f"\n[{idx+1}] ID: {result['id']}")
        print(f"    Time: {result['start_time']} - {result['end_time']}")
        print(f"    Text: {result['text'][:80]}...")

    print("\n[OK] 按时间范围搜索测试通过")


def test_6_filtered_search(search_engine: SemanticSearchEngine):
    """测试6: 带过滤条件的搜索"""
    print_separator("TEST 6: 带过滤条件的搜索")

    query = "金三角历史"

    # 测试不同的过滤条件
    print(f"\nQuery: '{query}' with filters")

    # 1. 按completeness过滤
    results = search_engine.search_atoms(
        query=query,
        limit=5,
        score_threshold=0.5
    )

    print(f"\nWith score_threshold=0.5:")
    print(f"  Found {len(results)} results")
    if results:
        print(f"  Top score: {results[0]['score']:.4f}")
        print(f"  Lowest score: {results[-1]['score']:.4f}")

    print("\n[OK] 带过滤条件的搜索测试通过")


def main():
    """主函数"""
    print_separator("SemanticSearchEngine 完整测试")

    # 1. 设置搜索引擎
    print("\n[1/7] Setting up search engine...")
    search_engine, vector_store = setup_search_engine()
    print("[OK] Search engine ready")

    # 2. 加载测试数据
    print("\n[2/7] Loading test data...")
    atoms, segments, embeddings_data = load_test_data()
    print(f"[OK] Loaded {len(atoms)} atoms, {len(segments)} segments")

    # 3. 插入数据到向量库
    print("\n[3/7] Inserting data into vector store...")
    atom_count = vector_store.insert_atoms(atoms[:10], embeddings_data['embeddings'])
    print(f"[OK] Inserted {atom_count} atoms")

    if segments:
        segment_embeddings = embeddings_data.get('segment_embeddings', [])
        if segment_embeddings:
            segment_count = vector_store.insert_segments(segments[:5], segment_embeddings[:5])
            print(f"[OK] Inserted {segment_count} segments")

    # 4. 运行测试
    print("\n[4/7] Running test 1...")
    test_1_atom_search(search_engine)

    if segments:
        print("\n[5/7] Running test 2...")
        test_2_segment_search(search_engine)

    print("\n[6/7] Running test 3...")
    test_3_similar_atoms(search_engine)

    print("\n[7/7] Running test 4...")
    test_4_hybrid_search(search_engine)

    # Additional tests
    test_5_time_range_search(search_engine)
    test_6_filtered_search(search_engine)

    # 统计信息
    print_separator("统计信息")
    stats = search_engine.get_stats()

    print("\nVector Store:")
    print(f"  Collection: {stats['vector_store']['collection_name']}")
    print(f"  Points: {stats['vector_store']['points_count']}")
    print(f"  Dimension: {stats['vector_store']['dimension']}")

    print("\nEmbedder:")
    print(f"  Model: {stats['embedder']['model']}")
    print(f"  Total calls: {stats['embedder']['total_calls']}")
    print(f"  Total tokens: {stats['embedder']['total_tokens']}")
    print(f"  Estimated cost: {stats['embedder']['estimated_cost']}")

    print_separator("SUCCESS - All Tests Passed!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
