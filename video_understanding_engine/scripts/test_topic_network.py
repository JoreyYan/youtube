"""
测试主题网络构建功能
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import NarrativeSegment
from analyzers.topic_network_builder import TopicNetworkBuilder

def main():
    print("="*70)
    print("测试主题网络构建功能")
    print("="*70)

    # 读取叙事片段
    segments_path = Path("data/output_pipeline_v3/narrative_segments.json")

    if not segments_path.exists():
        print(f"[X] 找不到文件: {segments_path}")
        return

    with open(segments_path, 'r', encoding='utf-8') as f:
        segments_data = json.load(f)

    print(f"[OK] 加载了 {len(segments_data)} 个叙事片段")

    # 转换为对象
    segments = [NarrativeSegment(**seg) for seg in segments_data]

    # 创建构建器
    builder = TopicNetworkBuilder()

    # 构建主题网络
    print("\n开始构建主题网络...")
    topic_network = builder.build(segments)

    # 显示结果
    print("\n" + "="*70)
    print("构建结果")
    print("="*70)

    stats = topic_network['statistics']
    print(f"\n总计:")
    print(f"  主要主题: {stats['total_primary_topics']}个")
    print(f"  次要主题: {stats['total_secondary_topics']}个")
    print(f"  标签: {stats['total_tags']}个")
    print(f"  关系: {stats['total_relations']}条")

    # 显示主要主题
    if topic_network['primary_topics']:
        print(f"\n主要主题:")
        for topic in topic_network['primary_topics'][:3]:
            print(f"  - {topic['topic']} (权重: {topic['weight']})")
            print(f"    次要主题: {', '.join(topic['subtopics'][:3])}")
            print(f"    标签: {', '.join(topic['tags'][:5])}")

    # 显示次要主题
    if topic_network['secondary_topics']:
        print(f"\n次要主题:")
        for topic in topic_network['secondary_topics'][:3]:
            print(f"  - {topic['topic']} (权重: {topic['weight']})")
            if topic['parent_topics']:
                print(f"    属于: {', '.join(topic['parent_topics'])}")

    # 显示热门标签
    if topic_network['tags']:
        print(f"\n热门标签:")
        for tag in topic_network['tags'][:10]:
            print(f"  - {tag['tag']}: {tag['count']}次")

    # 显示关系
    if topic_network['topic_relations']:
        print(f"\n主题关系示例:")
        for rel in topic_network['topic_relations'][:5]:
            print(f"  {rel['from']} --[{rel['relation']}]--> {rel['to']}")

    # 保存结果
    output_path = Path("data/output_pipeline_v3/topics.json")
    builder.save(topic_network, output_path)

    print("\n" + "="*70)
    print("测试完成！")
    print("="*70)

if __name__ == "__main__":
    main()
