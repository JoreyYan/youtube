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

        # 直接使用已经解析好的原子对象 - FIXED 2024-10-04
        segment_atoms = atoms

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

    def _call_ai_analysis(self, full_text: str, segment_meta: SegmentMeta, max_retries: int = 3) -> Dict[str, Any]:
        """调用AI进行综合分析（带重试）"""
        # 构建上下文信息
        context = {
            "segment_num": segment_meta.segment_num,
            "duration_minutes": round(segment_meta.duration_minutes, 1),
            "start_time": segment_meta.start_time,
            "end_time": segment_meta.end_time
        }

        # 构建提示词 - 使用简单替换避免format()解析JSON示例
        prompt = self.prompt_template.replace(
            '{CONTEXT}', json.dumps(context, ensure_ascii=False)
        ).replace(
            '{FULL_TEXT}', full_text
        )

        # 重试机制
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"  [API调用] 尝试 {attempt + 1}/{max_retries}")

                # 调用API
                response = self.client.call(prompt, max_tokens=4000)

                # DEBUG: 记录原始响应
                logger.debug(f"AI原始响应（前500字符）: {response[:500]}")
                logger.debug(f"响应长度: {len(response)}字符")

                # 解析响应
                analysis_result = self._parse_ai_response(response)

                # 如果成功解析且不是默认值，返回结果
                if analysis_result.get('title') != "未命名片段":
                    logger.info(f"  [成功] 第 {attempt + 1} 次尝试成功")
                    return analysis_result
                else:
                    logger.warning(f"  [警告] 第 {attempt + 1} 次尝试返回默认值，重试中...")
                    last_error = ValueError("API返回默认分析结果")

            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"  [JSON错误] 第 {attempt + 1} 次尝试失败: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"  [重试] 等待后重试...")
                    continue
            except Exception as e:
                last_error = e
                logger.error(f"  [错误] 第 {attempt + 1} 次尝试失败: {type(e).__name__}: {e}")
                if attempt < max_retries - 1:
                    continue

        # 所有重试都失败，返回默认值
        logger.error(f"  [失败] {max_retries} 次尝试全部失败，使用默认值")
        logger.error(f"  [最后错误] {type(last_error).__name__}: {last_error}")
        return self._get_default_analysis()

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析AI响应 - 增强容错"""
        try:
            json_str = None

            # 方法1: 查找```json代码块
            json_block_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_block_match:
                json_str = json_block_match.group(1).strip()
                logger.debug("使用方法1: 找到```json代码块")

            # 方法2: 查找```代码块（不带json标记）
            if not json_str:
                json_block_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
                if json_block_match:
                    content = json_block_match.group(1).strip()
                    # 检查是否以{开头
                    if content.startswith('{'):
                        json_str = content
                        logger.debug("使用方法2: 找到```代码块")

            # 方法3: 查找第一个{到最后一个}
            if not json_str:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0).strip()
                    logger.debug("使用方法3: 提取{...}内容")

            # 如果都失败，抛出错误
            if not json_str:
                raise ValueError("响应中未找到JSON对象")

            # 清理JSON字符串
            json_str = self._clean_json_string(json_str)

            # 记录JSON前100字符用于调试
            logger.debug(f"JSON前100字符: {json_str[:100]}")
            logger.debug(f"JSON长度: {len(json_str)}")

            # 解析JSON
            analysis_result = json.loads(json_str)

            # 验证必需字段
            required_fields = ['title', 'summary', 'narrative_structure', 'topics',
                             'entities', 'content_facet', 'ai_analysis',
                             'importance_score', 'quality_score']

            missing_fields = [f for f in required_fields if f not in analysis_result]
            if missing_fields:
                logger.warning(f"缺少字段: {missing_fields}")
                # 补充默认值
                defaults = self._get_default_analysis()
                for field in missing_fields:
                    analysis_result[field] = defaults.get(field)

            logger.debug(f"JSON解析成功，包含键: {list(analysis_result.keys())}")
            logger.debug(f"title: {analysis_result.get('title', 'N/A')[:50]}")

            return analysis_result

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"错误位置: line {e.lineno}, column {e.colno}")
            if 'json_str' in locals():
                # 显示出错位置附近的内容
                start = max(0, e.pos - 100)
                end = min(len(json_str), e.pos + 100)
                logger.error(f"出错附近内容: ...{json_str[start:end]}...")
            else:
                logger.error(f"响应预览: {response[:500]}")
            return self._get_default_analysis()
        except Exception as e:
            logger.error(f"解析AI响应失败: {type(e).__name__}: {e}")
            logger.error(f"响应长度: {len(response)}")
            logger.error(f"响应前500字符: {response[:500]}")
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

    def _clean_json_string(self, json_str: str) -> str:
        """清理JSON字符串，移除常见的格式问题"""
        # 移除BOM和零宽字符
        json_str = json_str.replace('\ufeff', '')
        json_str = json_str.replace('\u200b', '')
        json_str = json_str.replace('\u200c', '')
        json_str = json_str.replace('\u200d', '')

        # 移除可能的前后空白
        json_str = json_str.strip()

        # 修复常见的JSON格式问题
        # 1. 修复缺少逗号的问题（例如："key": "value"\n  "key2":）
        json_str = re.sub(r'"\s*\n\s*"', '",\n  "', json_str)

        # 2. 修复中文引号
        json_str = json_str.replace('"', '"').replace('"', '"')
        json_str = json_str.replace(''', "'").replace(''', "'")

        # 3. 移除JavaScript风格的注释
        json_str = re.sub(r'//.*?\n', '\n', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

        # 4. 修复行尾多余的逗号（JSON不允许）
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)

        return json_str

    def analyze_segment_entities(self, text: str) -> Dict[str, Any]:
        """
        专门用于实体提取的方法

        Args:
            text: 待分析的文本

        Returns:
            包含实体信息的字典
        """
        # 构建专门的实体提取提示词
        entity_prompt = """你是一个专业的中文实体识别专家。请从以下文本中准确提取实体，注意实体边界的准确性。

【文本】
{TEXT}

【任务】
请提取以下类型的实体，注意：
1. **实体边界必须准确**，不要包含多余的字符
2. **人名**：如"温哥华"应该是地名，"罗星汉"应该准确识别边界
3. **地名**：城市、国家、地区名称
4. **组织机构**：公司、政府部门、团体等
5. **时间点**：具体时间、年份、日期等
6. **事件**：历史事件、新闻事件等
7. **概念术语**：专业术语、概念等

【输出格式】
请以JSON格式输出：
```json
{
  "entities": {
    "persons": ["人名1", "人名2"],
    "countries": ["国家1", "地区1"],
    "organizations": ["组织1", "机构1"],
    "time_points": ["时间1", "时间2"],
    "events": ["事件1", "事件2"],
    "concepts": ["概念1", "术语1"]
  }
}
```

【输出】""".replace('{TEXT}', text)

        try:
            logger.info("开始AI实体提取")

            # 调用AI进行实体提取
            response = self.client.call(entity_prompt, max_tokens=2000)
            logger.debug(f"实体提取AI响应（前300字符）: {response[:300]}")

            # 解析响应
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if not json_match:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)

            if json_match:
                json_str = json_match.group(1) if json_match.group(0).startswith('```') else json_match.group(0)
                json_str = self._clean_json_string(json_str)
                result = json.loads(json_str)

                # 验证结果结构
                if 'entities' in result:
                    logger.info(f"AI实体提取成功，提取实体类型: {list(result['entities'].keys())}")
                    return result
                else:
                    logger.warning("AI响应格式不正确，缺少entities字段")

        except json.JSONDecodeError as e:
            logger.error(f"实体提取JSON解析失败: {e}")
            logger.error(f"响应内容: {response[:500] if 'response' in locals() else 'None'}")
        except Exception as e:
            logger.error(f"AI实体提取失败: {type(e).__name__}: {e}")

        # 返回空结果
        logger.warning("AI实体提取失败，返回空结果")
        return {
            "entities": {
                "persons": [],
                "countries": [],
                "organizations": [],
                "time_points": [],
                "events": [],
                "concepts": []
            }
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
