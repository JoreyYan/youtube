"""
测试 EmbeddingGenerator
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from embedders import EmbeddingGenerator
import config


def test_single_embedding():
    """测试单个文本的 embedding 生成"""
    print("\n" + "="*70)
    print("[TEST 1] 单文本 Embedding 生成")
    print("="*70)

    generator = EmbeddingGenerator(
        api_key=config.OPENAI_API_KEY,
        model='text-embedding-3-small'
    )

    text = "1962年古巴导弹危机是冷战时期的重大事件"

    print(f"\n输入文本: {text}")
    print(f"预估tokens: {generator.count_tokens(text)}")

    embedding = generator.generate_embedding(text)

    print(f"\n[OK] 生成成功")
    print(f"  向量维度: {len(embedding)}")
    print(f"  向量类型: {type(embedding[0])}")
    print(f"  向量范围: [{min(embedding):.4f}, {max(embedding):.4f}]")
    print(f"  前5个值: {embedding[:5]}")

    stats = generator.get_stats()
    print(f"\n统计信息:")
    print(f"  API调用: {stats['total_calls']}次")
    print(f"  处理tokens: {stats['total_tokens']}")
    print(f"  预估成本: {stats['estimated_cost']}")

    assert len(embedding) == 1536, "向量维度应为1536"
    assert all(isinstance(v, float) for v in embedding[:5]), "向量值应为float"

    print("\n[PASS] 测试通过!")


def test_batch_embedding():
    """测试批量 embedding 生成"""
    print("\n" + "="*70)
    print("[TEST 2] 批量 Embedding 生成")
    print("="*70)

    generator = EmbeddingGenerator(
        api_key=config.OPENAI_API_KEY,
        model='text-embedding-3-small'
    )

    texts = [
        "这是第一段测试文本，讲述金三角的历史",
        "这是第二段测试文本，关于缅甸军政府",
        "这是第三段测试文本，罗星汉的故事",
        "这是第四段测试文本，冷战时期的国际关系",
        "这是第五段测试文本，东南亚地区的政治格局"
    ]

    print(f"\n输入: {len(texts)}个文本")
    total_tokens = sum(generator.count_tokens(t) for t in texts)
    print(f"预估总tokens: {total_tokens}")

    print(f"\n开始批量生成...")
    embeddings = generator.generate_batch(texts, batch_size=5, show_progress=True)

    print(f"\n[OK] 批量生成成功")
    print(f"  生成数量: {len(embeddings)}")
    print(f"  每个维度: {len(embeddings[0])}")

    stats = generator.get_stats()
    print(f"\n统计信息:")
    print(f"  API调用: {stats['total_calls']}次")
    print(f"  处理tokens: {stats['total_tokens']}")
    print(f"  处理文本: {stats['total_texts']}个")
    print(f"  预估成本: {stats['estimated_cost']}")

    assert len(embeddings) == len(texts), "生成数量应等于输入数量"
    assert all(len(e) == 1536 for e in embeddings), "所有向量维度应为1536"

    print("\n[PASS] 测试通过!")


def test_real_data():
    """测试真实数据（使用 atoms）"""
    print("\n" + "="*70)
    print("[TEST 3] 真实数据测试（Atoms）")
    print("="*70)

    # 读取真实的 atoms 数据
    import json
    atoms_file = Path("data/output_semantic_test/atoms.jsonl")

    if not atoms_file.exists():
        print("\n[SKIP] atoms.jsonl 不存在，跳过此测试")
        return

    # 加载原子
    atoms = []
    with open(atoms_file, 'r', encoding='utf-8') as f:
        for line in f:
            atoms.append(json.loads(line))

    print(f"\n加载了 {len(atoms)} 个原子")

    # 提取文本
    texts = [atom['merged_text'] for atom in atoms[:10]]  # 只测试前10个
    print(f"测试前 {len(texts)} 个原子")

    generator = EmbeddingGenerator(
        api_key=config.OPENAI_API_KEY,
        model='text-embedding-3-small'
    )

    # 生成向量
    print(f"\n开始生成向量...")
    embeddings = generator.generate_batch(texts, batch_size=10, show_progress=True)

    print(f"\n[OK] 真实数据测试成功")
    print(f"  生成数量: {len(embeddings)}")

    stats = generator.get_stats()
    print(f"\n统计信息:")
    print(f"  API调用: {stats['total_calls']}次")
    print(f"  处理tokens: {stats['total_tokens']}")
    print(f"  预估成本: {stats['estimated_cost']}")

    # 保存结果（供后续测试使用）
    output_file = Path("data/output_semantic_test/test_embeddings.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'atom_ids': [atoms[i]['atom_id'] for i in range(len(texts))],
            'embeddings': embeddings,
            'stats': stats
        }, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 结果已保存到: {output_file}")
    print("\n[PASS] 测试通过!")


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("EmbeddingGenerator 测试套件")
    print("="*70)

    try:
        test_single_embedding()
        test_batch_embedding()
        test_real_data()

        print("\n" + "="*70)
        print("[SUCCESS] 所有测试通过!")
        print("="*70)

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
