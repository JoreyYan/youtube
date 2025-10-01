"""
DeepAnalyzer - 深度语义分析器
对叙事片段进行全面的语义分析（主题、实体、结构、AI洞察）
"""

import json
import re
from typing import List, Dict, Any
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    Atom, SegmentMeta, NarrativeSegment,
    NarrativeStructure, Topics, Entities,
    ContentFacet, AIAnalysis
)
from utils import ClaudeClient, setup_logger

logger = setup_logger(__name__)


class DeepAnalyzer:
    """深度语义分析器"""

    def __init__(self, api_key: str):
        self.client = ClaudeClient(api_key)

        # 加载提示词
        prompt_path = Path(__file__).parent.parent / 'prompts' / 'analyze_comprehensive.txt'
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.prompt_template = f.read()
        else:
            # 如果提示词文件不存在，使用内嵌的简化版
            self.prompt_template = self._get_default_prompt()

    def analyze_segment(
        self,
        segment_meta: SegmentMeta,
        atoms: List[Atom]
    ) -> NarrativeSegment:
        """
        深度分析片段

        Args:
            segment_meta: 片段元数据
            atoms: 完整的原子列表

        Returns:
            完整的叙事片段对象
        """
        logger.info(f"分析片段 SEG_{segment_meta.segment_num:03d}")

        # 提取该片段的原子
        atoms_dict = {atom.atom_id: atom for atom in atoms}
        segment_atoms = [atoms_dict[aid] for aid in segment_meta.atoms if aid in atoms_dict]

        if len(segment_atoms) == 0:
            raise ValueError(f"片段{segment_meta.segment_num}没有有效原子")

        # 合并文本
        full_text = self._merge_atoms_text(segment_atoms)
        logger.info(f"  文本长度: {len(full_text)}字")

        # 调用AI进行综合分析
        analysis_result = self._call_ai_analysis(full_text, segment_meta)

        # 构建NarrativeSegment对象
        narrative_segment = self._build_narrative_segment(
            segment_meta,
            segment_atoms,
            full_text,
            analysis_result
        )

        logger.info(f"  分析完成: {narrative_segment.title}")

        return narrative_segment

    def analyze_batch(
        self,
        segment_metas: List[SegmentMeta],
        atoms: List[Atom],
        show_progress: bool = True
    ) -> List[NarrativeSegment]:
        """
        批量分析多个片段

        Args:
            segment_metas: 片段元数据列表
            atoms: 完整的原子列表
            show_progress: 是否显示进度

        Returns:
            叙事片段列表
        """
        logger.info(f"开始批量分析，共{len(segment_metas)}个片段")

        narrative_segments = []

        for i, seg_meta in enumerate(segment_metas):
            if show_progress:
                logger.info(f"进度: {i+1}/{len(segment_metas)}")

            try:
                segment = self.analyze_segment(seg_meta, atoms)
                narrative_segments.append(segment)
            except Exception as e:
                logger.error(f"片段{seg_meta.segment_num}分析失败: {e}")
                logger.error(f"异常类型: {type(e).__name__}")
                logger.error(f"异常详情", exc_info=True)
                continue

        logger.info(f"批量分析完成，成功{len(narrative_segments)}/{len(segment_metas)}个")

        return narrative_segments

    def _merge_atoms_text(self, atoms: List[Atom]) -> str:
        """合并原子文本"""
        texts = []
        for atom in sorted(atoms, key=lambda a: a.start_ms):
            texts.append(atom.merged_text)
        return "\n\n".join(texts)

    def _call_ai_analysis(self, full_text: str, segment_meta: SegmentMeta) -> Dict[str, Any]:
        """调用AI进行综合分析"""
        # 构建上下文信息
        context = {
            "segment_num": segment_meta.segment_num,
            "duration_minutes": round(segment_meta.duration_minutes, 1),
            "start_time": segment_meta.start_time,
            "end_time": segment_meta.end_time
        }

        # 构建提示词
        prompt = self.prompt_template.format(
            CONTEXT=json.dumps(context, ensure_ascii=False),
            FULL_TEXT=full_text
        )

        # 调用API
        response = self.client.call(prompt, max_tokens=4000)

        # DEBUG: 记录原始响应
        logger.debug(f"AI原始响应（前500字符）: {response[:500]}")
        logger.debug(f"响应长度: {len(response)}字符")

        # 解析响应
        analysis_result = self._parse_ai_response(response)

        return analysis_result

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析AI响应"""
        try:
            # 尝试多种方式提取JSON
            # 方法1: 查找```json代码块
            json_block_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_block_match:
                json_str = json_block_match.group(1)
            else:
                # 方法2: 查找第一个{到最后一个}
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if not json_match:
                    raise ValueError("响应中未找到JSON对象")
                json_str = json_match.group(0)

            # 清理JSON字符串
            json_str = json_str.strip()

            # 额外清理：移除可能的前导/尾随空白字符和换行
            # 移除JSON外部的任何说明文字（例如：这里是JSON: {...}）
            json_str = re.sub(r'^[^\{]*', '', json_str)  # 移除首个{之前的内容
            json_str = re.sub(r'[^\}]*$', '', json_str)  # 移除最后一个}之后的内容

            # 解析JSON
            analysis_result = json.loads(json_str)

            # DEBUG: 验证解析结果
            logger.debug(f"JSON解析成功，包含键: {list(analysis_result.keys())}")
            logger.debug(f"title值类型: {type(analysis_result.get('title'))}")
            logger.debug(f"title值内容: {repr(analysis_result.get('title', 'N/A')[:100])}")

            return analysis_result

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"JSON内容预览: {json_str[:500] if 'json_str' in locals() else response[:500]}")
            logger.error(f"完整响应长度: {len(response)}字符")
            # 返回默认结构
            return self._get_default_analysis()
        except Exception as e:
            logger.error(f"解析AI响应失败: {e}")
            logger.error(f"响应预览: {response[:500]}")
            # 返回默认结构
            return self._get_default_analysis()

    def _build_narrative_segment(
        self,
        segment_meta: SegmentMeta,
        atoms: List[Atom],
        full_text: str,
        analysis: Dict[str, Any]
    ) -> NarrativeSegment:
        """构建NarrativeSegment对象"""

        # 提取各部分数据
        narrative_structure = NarrativeStructure(
            type=analysis.get('narrative_structure', {}).get('type', '未知类型'),
            structure=analysis.get('narrative_structure', {}).get('structure', ''),
            acts=analysis.get('narrative_structure', {}).get('acts', [])
        )

        topics = Topics(
            primary_topic=analysis.get('topics', {}).get('primary_topic'),
            secondary_topics=analysis.get('topics', {}).get('secondary_topics', []),
            free_tags=analysis.get('topics', {}).get('free_tags', [])
        )

        entities = Entities(
            persons=analysis.get('entities', {}).get('persons', []),
            countries=analysis.get('entities', {}).get('countries', []),
            organizations=analysis.get('entities', {}).get('organizations', []),
            time_points=analysis.get('entities', {}).get('time_points', []),
            events=analysis.get('entities', {}).get('events', []),
            concepts=analysis.get('entities', {}).get('concepts', [])
        )

        content_facet = ContentFacet(
            type=analysis.get('content_facet', {}).get('type', '陈述'),
            aspect=analysis.get('content_facet', {}).get('aspect', '综合视角'),
            stance=analysis.get('content_facet', {}).get('stance', '中立客观')
        )

        ai_analysis = AIAnalysis(
            core_argument=analysis.get('ai_analysis', {}).get('core_argument', ''),
            key_insights=analysis.get('ai_analysis', {}).get('key_insights', []),
            logical_flow=analysis.get('ai_analysis', {}).get('logical_flow', ''),
            suitable_for_reuse=analysis.get('ai_analysis', {}).get('suitable_for_reuse', True),
            reuse_suggestions=analysis.get('ai_analysis', {}).get('reuse_suggestions', [])
        )

        # 生成摘要（如果AI没有提供，则自动截取）
        summary = analysis.get('summary', full_text[:300] + "...")

        # 创建NarrativeSegment对象
        segment = NarrativeSegment(
            segment_id=f"SEG_{segment_meta.segment_num:03d}",
            title=analysis.get('title', f"片段{segment_meta.segment_num}"),
            atoms=segment_meta.atoms,
            start_ms=segment_meta.start_ms,
            end_ms=segment_meta.end_ms,
            duration_ms=segment_meta.duration_ms,
            summary=summary,
            full_text=full_text,
            narrative_structure=narrative_structure,
            topics=topics,
            entities=entities,
            content_facet=content_facet,
            ai_analysis=ai_analysis,
            importance_score=analysis.get('importance_score', 0.7),
            quality_score=analysis.get('quality_score', 0.7)
        )

        return segment

    def _get_default_analysis(self) -> Dict[str, Any]:
        """获取默认分析结果（当AI失败时）"""
        return {
            "title": "未命名片段",
            "summary": "",
            "narrative_structure": {
                "type": "未知",
                "structure": "",
                "acts": []
            },
            "topics": {
                "primary_topic": None,
                "secondary_topics": [],
                "free_tags": []
            },
            "entities": {
                "persons": [],
                "countries": [],
                "organizations": [],
                "time_points": [],
                "events": [],
                "concepts": []
            },
            "content_facet": {
                "type": "陈述",
                "aspect": "综合",
                "stance": "中立"
            },
            "ai_analysis": {
                "core_argument": "",
                "key_insights": [],
                "logical_flow": "",
                "suitable_for_reuse": True,
                "reuse_suggestions": []
            },
            "importance_score": 0.5,
            "quality_score": 0.5
        }

    def _get_default_prompt(self) -> str:
        """获取默认提示词（如果文件不存在）"""
        return """你是一个专业的视频内容分析专家，擅长分析金融、历史、政治类的口播内容。

【上下文】
{CONTEXT}

【完整文本】
{FULL_TEXT}

【分析任务】
请对这段内容进行深度分析，提取以下信息：

1. **片段标题**：用10-20字概括该片段的核心主题
2. **内容摘要**：150-300字的摘要
3. **叙事结构**：
   - type: 叙事类型（历史叙事/观点论述/案例分析/数据展示）
   - structure: 叙事结构（如：背景→危机→决策→结果）
   - acts: 叙事幕次（每一幕包含role和description）
4. **主题标注**：
   - primary_topic: 主要话题
   - secondary_topics: 次要话题列表
   - free_tags: 自由标签（3-10个关键词）
5. **实体提取**：
   - persons: 人物
   - countries: 国家/地区
   - organizations: 组织/机构
   - time_points: 时间点
   - events: 历史事件
   - concepts: 概念/术语
6. **内容维度**：
   - type: 内容类型
   - aspect: 关注点
   - stance: 立场
7. **AI深度分析**：
   - core_argument: 核心论点
   - key_insights: 关键洞察（3-5条）
   - logical_flow: 逻辑流程
   - suitable_for_reuse: 是否适合二创（true/false）
   - reuse_suggestions: 二创建议
8. **评分**：
   - importance_score: 重要性（0-1）
   - quality_score: 质量（0-1）

【输出格式】
JSON对象，严格按照上述结构。

【输出】"""
