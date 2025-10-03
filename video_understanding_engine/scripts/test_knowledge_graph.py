"""
测试知识图谱构建功能
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import NarrativeSegment
from analyzers.knowledge_graph_builder import KnowledgeGraphBuilder

def main():
    print("="*70)
    print("测试知识图谱构建功能")
    print("="*70)

    # 读取数据
    segments_path = Path("data/output_pipeline_v3/narrative_segments.json")
    entities_path = Path("data/output_pipeline_v3/entities.json")
    topics_path = Path("data/output_pipeline_v3/topics.json")

    # 检查文件
    for path in [segments_path, entities_path, topics_path]:
        if not path.exists():
            print(f"[X] 找不到文件: {path}")
            return

    # 加载数据
    with open(segments_path, 'r', encoding='utf-8') as f:
        segments_data = json.load(f)
    with open(entities_path, 'r', encoding='utf-8') as f:
        entities = json.load(f)
    with open(topics_path, 'r', encoding='utf-8') as f:
        topics = json.load(f)

    print(f"[OK] 加载了:")
    print(f"  - {len(segments_data)} 个叙事片段")
    print(f"  - {entities['statistics']['total_entities']} 个实体")
    print(f"  - {topics['statistics']['total_primary_topics']} 个主题")

    # 转换片段为对象
    segments = [NarrativeSegment(**seg) for seg in segments_data]

    # 创建构建器
    builder = KnowledgeGraphBuilder()

    # 构建知识图谱
    print("\n开始构建知识图谱...")
    graph = builder.build(segments, entities, topics)

    # 显示结果
    print("\n" + "="*70)
    print("构建结果")
    print("="*70)

    stats = graph['statistics']
    print(f"\n总计:")
    print(f"  节点: {stats['total_nodes']}个")
    print(f"  边: {stats['total_edges']}条")

    print(f"\n节点类型分布:")
    for node_type, count in stats['node_types'].items():
        print(f"  {node_type}: {count}个")

    print(f"\n边类型分布:")
    for edge_type, count in stats['edge_types'].items():
        print(f"  {edge_type}: {count}条")

    # 显示示例节点
    print(f"\n节点示例:")
    for node in graph['nodes'][:5]:
        print(f"  [{node['type']}] {node['label']}")

    # 显示示例边
    print(f"\n关系示例:")
    for edge in graph['edges'][:8]:
        source_label = next((n['label'] for n in graph['nodes'] if n['id'] == edge['source']), edge['source'])
        target_label = next((n['label'] for n in graph['nodes'] if n['id'] == edge['target']), edge['target'])
        print(f"  {source_label} --[{edge['relation']}]--> {target_label}")

    # 保存结果
    output_dir = Path("data/output_pipeline_v3/indexes")
    output_path = output_dir / "graph.json"
    builder.save(graph, output_path)

    print("\n" + "="*70)
    print("测试完成！")
    print("="*70)

if __name__ == "__main__":
    main()
