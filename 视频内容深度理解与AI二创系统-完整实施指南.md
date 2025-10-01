# 视频内容深度理解与AI二创系统 - 完整实施指南

## 目录
- [核心理念](#核心理念)
- [系统架构](#系统架构)
- [阶段0：准备工作](#阶段0准备工作)
- [阶段1：解析字幕](#阶段1解析字幕-parse)
- [阶段2：原子化](#阶段2原子化-atomize)
- [阶段3：语义分析](#阶段3语义分析-analyze)
- [阶段4：结构重组](#阶段4结构重组-structure)
- [阶段5：建立索引](#阶段5建立索引-index)
- [阶段6：生成剪辑方案](#阶段6生成剪辑方案-generate)
- [完整示例](#完整示例端到端流程)
- [时间和成本估算](#时间和成本估算)

---

## 核心理念

### 核心挑战：直播内容的特殊性

直播视频不同于剪辑好的视频，它有这些特点：
- **非线性叙事**：博主想到哪说到哪，话题跳跃
- **大量冗余**：重复、停顿、"呃""啊"、等待弹幕
- **隐含上下文**：很多内容需要理解前后文才有意义
- **多线索交织**：主线故事 + 弹幕互动 + 临时插话

### 信息理解的层次

#### Level 1：表层信息捕获
- 博主说了什么字（字幕已提供）
- 在什么时间说的（时间戳）
- 说了多久

**问题**：这层信息对二创无用，因为没有"意义"

#### Level 2：语义单元识别
把碎片化的话语组织成**有意义的最小单元**：

```
原始字幕（碎片）：
00:00:07 → "what"
00:00:08 → "开始了没有啊"
00:00:11 → "我看看开始了没有"
00:00:15 → "哎开始了没有"

↓ 合并为语义单元

[00:00:07-00:00:25] 语义单元："博主确认直播是否开始"
类型：开场、技术性对话
价值：低（可跳过）
```

#### Level 3：主题块识别
把多个语义单元组织成**主题块**：

```
主题块示例：
[00:02:30-00:15:45] "金三角历史背景介绍"
  ├─ [00:02:30-00:05:20] 小主题1：1962年国民党残军背景
  ├─ [00:05:20-00:08:10] 小主题2：坤沙的崛起
  ├─ [00:08:10-00:12:30] 小主题3：罗星汉的对抗
  └─ [00:12:30-00:15:45] 小主题4：两人关系演变

[00:15:45-00:18:20] "读观众来信"
  内容：某观众问缅北现状

[00:18:20-00:35:50] "回到金三角话题"
  继续讲历史...
```

**关键问题：如何处理"话题回流"？**
- 博主可能讲了10分钟历史，插播5分钟闲聊，再回到历史
- 简单的时间线切分会破坏逻辑完整性
- **需要"逻辑重组"能力**

#### Level 4：深层结构理解

**4.1 叙事结构识别**
```
这期视频的"骨架"是什么？
- 主线：金三角双雄的权力斗争史（1962-1998）
- 支线：博主个人观点和评价
- 插曲：观众互动、当代对比
```

**4.2 逻辑关系提取**
```
坤沙 vs 罗星汉的关系：
- 时间维度：从合作 → 竞争 → 对抗 → 一方胜出
- 原因：利益冲突、性格差异、外部势力介入
- 影响：对整个金三角格局的改变
```

**4.3 情感与价值判断**
```
博主的立场和态度：
- 对坤沙：复杂，既批判又理解
- 对罗星汉：相对同情
- 对缅北局势：担忧
- 对观众提问：耐心但有时不耐烦
```

---

## 系统架构

### 信息组织的多维模型

#### 维度1：时间轴（物理结构）
```
00:00 ─────────────── 02:30:45
  └─ 这是视频的物理结构，不可变
```

#### 维度2：主题图谱（逻辑结构）
```
金三角历史
├─ 1962-1970年代
│   ├─ 片段A [00:02:30-00:15:45]
│   ├─ 片段D [00:45:20-00:52:30] ← 时间上不连续
│   └─ 片段G [01:20:15-01:28:40]
├─ 1980年代
│   └─ ...
└─ 1990年代
    └─ ...

当代缅北
├─ 片段B [00:18:20-00:22:15]
└─ 片段E [01:05:30-01:12:20]

观众互动
├─ 读来信：片段C, F, H
└─ 骂人/吐槽：片段I, J
```

#### 维度3：叙事弧线（戏剧结构）
```
起：开场 [00:00-00:02]
承：历史背景铺垫 [00:02-00:20]
转：核心冲突展开 [00:20-01:40]
    ├─ 高潮1 [00:35-00:42]
    ├─ 高潮2 [01:15-01:25]
    └─ 高潮3 [01:32-01:40]
合：总结和延伸 [01:40-02:30]
```

#### 维度4：情绪能量曲线
```
能量值
10 |     *        *              *
 8 |    * *      * *          * * *
 6 |   *   *    *   *        *     *
 4 |  *     *  *     *      *       *
 2 | *       **       *    *         *
 0 |*─────────────────────────────────*
   00:00                          02:30:45
```

#### 维度5：知识图谱（概念网络）
```
人物：坤沙 ←→ 罗星汉
       ↓         ↓
地点：金三角 ←→ 缅北
       ↓
事件：毒品贸易 ←→ 武装冲突
       ↓
影响：地区局势 ←→ 国际关系
```

### 关键洞察

**AI要做的不是"切分视频"，而是：**

1. **解构**：把直播流拆解成原子化的"信息单元"
2. **理解**：识别每个单元的类型、价值、关联
3. **重构**：按不同维度重新组织这些单元
4. **生成**：基于重构后的结构，创造新的叙事

**类比：**
- ❌ 不是"把2小时切成12个10分钟片段"
- ✅ 而是"把2小时理解成一个知识网络，然后可以按任意路径遍历"

---

## 核心存储格式

### 三层知识表示

#### 第一层：原子层（Atoms）—— 最小信息单元

```json
{
  "atom_id": "A045",
  "time": "00:32:10 - 00:35:20",
  "text": "1985年，坤沙发动了一次关键性的军事行动...",

  "semantic_vector": [0.23, 0.45, ...],  // ← 核心！语义向量

  "tags": {
    "人物": ["坤沙"],
    "地点": ["金三角东部"],
    "时间": ["1985"],
    "事件": ["军事行动"],
    "主题": ["权力扩张", "军事冲突"],
    "情感": "激动",
    "价值": 9
  },

  "summary": "坤沙1985年的关键军事行动，奠定其在金三角的统治地位"
}
```

**为什么要semantic_vector（语义向量）？**

这是让AI"理解"的关键：
- 把文本转成数学向量（embedding）
- 未来AI可以用**语义相似度**搜索，而不是关键词匹配

**例子：**
```
用户问："给我找坤沙扩张势力的片段"

传统关键词搜索：只能找到包含"坤沙"+"扩张"的片段
语义搜索：能找到所有"坤沙增强控制、占领地盘、军事行动"相关的片段
         即使原文没有"扩张"这个词
```

#### 第二层：概念层（Concepts）—— 结构化知识

**2.1 实体卡片（Entity Cards）**

```json
{
  "entity_id": "person_kunsha",
  "type": "person",
  "name": "坤沙",

  "profile": {
    "生卒年": "1934-2007",
    "身份": "金三角军阀",
    "关键特征": ["权谋高手", "毒品大王", "善于利用地缘政治"],
    "ai_summary": "坤沙是金三角历史上最有影响力的军阀..."
  },

  "facets": {
    "性格": {
      "related_atoms": ["A023", "A045", "A078"],
      "ai_analysis": "坤沙性格复杂，既残忍又有政治智慧..."
    },
    "权力手段": {
      "related_atoms": ["A034", "A056"],
      "ai_analysis": "主要通过军事控制+经济利益笼络..."
    },
    "历史评价": {
      "related_atoms": ["A089", "A112"],
      "博主观点": "批判其毒品贸易，但认可其生存智慧",
      "ai_analysis": "..."
    }
  },

  "timeline": [
    {"time": "1962", "event": "进入金三角", "atoms": ["A012"]},
    {"time": "1985", "event": "关键军事行动", "atoms": ["A045"]},
    {"time": "1996", "event": "投降", "atoms": ["A098"]}
  ],

  "relationships": [
    {
      "target": "person_luoxinghan",
      "relation": "对手",
      "description": "长期竞争关系",
      "atoms": ["A023", "A045", "A067"]
    }
  ],

  "semantic_vector": [...]
}
```

**未来AI可以这样查询：**
```
Q: "给我讲讲坤沙的性格"
→ 找到 entity_kunsha.facets.性格
→ 返回相关原子 + AI分析 + 视频时间戳

Q: "坤沙和罗星汉什么关系？"
→ 找到 entity_kunsha.relationships → person_luoxinghan
→ 返回所有相关片段 + 关系演变时间线
```

**2.2 主题网络（Topic Network）**

```json
{
  "topic_id": "theme_power_struggle",
  "name": "权力斗争",

  "definition": "金三角地区不同势力之间的控制权争夺",

  "sub_topics": [
    {
      "name": "军事对抗",
      "atoms": ["A045", "A067", "A089"],
      "key_events": [
        {"time": "1985", "event": "某次战役", "atoms": ["A045"]}
      ]
    }
  ],

  "related_entities": ["person_kunsha", "person_luoxinghan"],

  "narrative_templates": [
    {
      "template_name": "双雄争霸",
      "structure": "背景铺垫 → 势力崛起 → 正面对抗 → 一方胜出",
      "applicable_atoms": ["A012", "A023", "A045", ...],
      "estimated_duration": "15:00"
    },
    {
      "template_name": "博弈论分析",
      "structure": "定义博弈 → 参与者策略 → 均衡分析 → 结果",
      "requires_voiceover": true,
      "estimated_duration": "12:00"
    }
  ],

  "semantic_vector": [...]
}
```

**这是二创的关键！**

#### 第三层：索引层（Indexes）—— 多维检索

**3.1 语义索引（Semantic Index）**
- 使用向量数据库（Chromadb/Qdrant）
- 支持语义相似度搜索

**3.2 结构化索引（Structured Index）**
```json
{
  "by_time": {
    "1960s": ["A012", "A015"],
    "1980s": ["A023", "A034", "A045"]
  },
  "by_person": {
    "坤沙": ["A012", "A023", "A045", ...],
    "罗星汉": ["A023", "A034", ...]
  },
  "by_topic": {
    "军事冲突": ["A045", "A067", "A089"],
    "经济博弈": ["A056", "A078"]
  },
  "by_value": {
    "9-10分": ["A045", "A067"],
    "7-8分": ["A023", "A034"]
  }
}
```

**3.3 关系图索引（Graph Index）**
- 知识图谱表示实体间关系
- 支持路径查询

### 文件结构
```
video_金三角大佬4/
├── atoms.json              # 所有信息原子（5000+条）
├── entities.json           # 实体卡片（人物、地点、事件）
├── topics.json             # 主题网络
├── narratives.json         # 叙事片段库
├── indexes/
│   ├── semantic.json       # 语义索引元数据
│   ├── structured.json     # 结构化索引
│   └── graph.json          # 知识图谱
├── embeddings/
│   └── vectors.bin         # 向量数据（用于语义搜索）
└── meta.json               # 视频元信息
```

### 关键设计原则

1. **粒度分层**：原子（最细） → 概念（中等） → 叙事（完整）
2. **多维索引**：同一段内容可以从多个角度找到
3. **语义向量是核心**：让AI能做智能搜索
4. **AI摘要无处不在**：每一层都有理解，不用重复分析
5. **可扩展性**：多个视频可以合并知识库

---

## 阶段0：准备工作

### 0.1 确定技术栈

```bash
# 推荐的技术组合

1. 字幕解析：Python srt库 或 JavaScript
2. AI分析：Claude API (Sonnet 3.5/3.7)
3. Embedding：OpenAI text-embedding-3-large
4. 向量数据库：Chromadb (简单) 或 Qdrant (强大)
5. 存储：JSON文件 + 向量DB
```

### 0.2 项目结构

```
subtitle-analyzer/
├── src/
│   ├── 1-parse/          # 阶段1：解析字幕
│   ├── 2-atomize/        # 阶段2：原子化
│   ├── 3-analyze/        # 阶段3：语义分析
│   ├── 4-structure/      # 阶段4：结构重组
│   ├── 5-index/          # 阶段5：建立索引
│   └── 6-generate/       # 阶段6：生成方案
├── data/
│   ├── raw/              # 原始字幕文件
│   ├── processed/        # 处理后的数据
│   └── output/           # 最终知识库
├── prompts/              # AI提示词模板
└── utils/                # 工具函数
```

---

## 阶段1：解析字幕 (Parse)

### 目标
把SRT字幕文件解析成结构化数据

### 输入
```
金三角大佬4：缅北双雄时代1962-1998.srt
```

### 处理步骤

#### 1.1 读取SRT文件

```python
import srt
from datetime import timedelta

def parse_srt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    subtitles = list(srt.parse(content))

    parsed = []
    for sub in subtitles:
        parsed.append({
            "id": sub.index,
            "start": str(sub.start),
            "end": str(sub.end),
            "text": sub.content.strip(),
            "duration": (sub.end - sub.start).total_seconds()
        })

    return parsed

# 结果示例
[
  {"id": 1, "start": "0:00:07", "end": "0:00:07.900", "text": "what", "duration": 0.9},
  {"id": 2, "start": "0:00:08.933", "end": "0:00:10.400", "text": "开始了没有啊", "duration": 1.467},
  ...
]
```

#### 1.2 清洗和预处理

```python
def clean_subtitles(parsed):
    cleaned = []

    for item in parsed:
        text = item['text']

        # 去除无意义内容
        if text in ['呃', 'uh', 'um', '...']:
            continue

        # 去除过短的片段（<0.5秒）
        if item['duration'] < 0.5:
            continue

        # 标准化文本
        text = text.replace('\n', ' ').strip()

        cleaned.append({
            **item,
            'text': text
        })

    return cleaned
```

### 输出
```json
{
  "video_id": "jinSanJiao_04",
  "total_subtitles": 3580,
  "total_duration": "02:30:45",
  "subtitles": [
    {"id": 1, "start": "0:00:08.933", "end": "0:00:10.400", "text": "开始了没有啊"},
    ...
  ]
}
```

保存为：`data/processed/parsed_subtitles.json`

---

## 阶段2：原子化 (Atomize)

### 目标
把碎片化的字幕合并成"语义完整的信息原子"

### 核心挑战
如何判断哪些句子应该合并？

### 方法：AI驱动的智能合并

#### 2.1 设计AI提示词

```python
# prompts/atomize.txt

你是一个视频内容分析专家。我会给你一段直播的字幕片段，你的任务是把它们合并成"语义完整的信息单元"。

【规则】
1. 一个信息单元应该表达一个完整的意思（一个观点、一个故事片段、一次互动）
2. 识别边界：
   - 主题转换 → 新单元
   - 长时间停顿（>5秒）→ 新单元
   - 从叙事转到互动 → 新单元
3. 保持时间戳的连续性

【输入格式】
[时间段] 文本内容

【输出格式】
返回JSON数组：
[
  {
    "atom_id": "A001",
    "start": "起始时间",
    "end": "结束时间",
    "merged_text": "合并后的完整文本",
    "type": "叙述历史/回应弹幕/发表观点/闲聊",
    "completeness": "完整/需要上下文"
  }
]

【示例输入】
[00:08:20] 1962年
[00:08:25] 国民党残军撤到金三角
[00:08:30] 这是整个金三角问题的起源
[00:08:38] hello 海绵宝宝
[00:08:40] 然后呢坤沙就是在这个背景下崛起的

【示例输出】
[
  {
    "atom_id": "A001",
    "start": "00:08:20",
    "end": "00:08:30",
    "merged_text": "1962年国民党残军撤到金三角，这是整个金三角问题的起源",
    "type": "叙述历史",
    "completeness": "完整"
  },
  {
    "atom_id": "A002",
    "start": "00:08:38",
    "end": "00:08:40",
    "merged_text": "hello 海绵宝宝",
    "type": "回应弹幕",
    "completeness": "完整"
  },
  {
    "atom_id": "A003",
    "start": "00:08:40",
    "end": "00:08:45",
    "merged_text": "然后呢坤沙就是在这个背景下崛起的",
    "type": "叙述历史",
    "completeness": "需要上下文"
  }
]
```

#### 2.2 批量处理

```python
import anthropic

def atomize_subtitles(subtitles, batch_size=50):
    """
    把字幕分批送给AI进行原子化
    """
    client = anthropic.Anthropic(api_key="your_api_key")
    atoms = []

    # 每次处理50条字幕（约2-3分钟内容）
    for i in range(0, len(subtitles), batch_size):
        batch = subtitles[i:i+batch_size]

        # 构建输入
        input_text = "\n".join([
            f"[{sub['start']}] {sub['text']}"
            for sub in batch
        ])

        # 调用Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": f"{ATOMIZE_PROMPT}\n\n【输入】\n{input_text}"
            }]
        )

        # 解析JSON
        batch_atoms = json.loads(response.content[0].text)
        atoms.extend(batch_atoms)

        print(f"处理进度: {i}/{len(subtitles)}")

    return atoms
```

#### 2.3 后处理和验证

```python
def validate_atoms(atoms):
    """
    检查原子的质量
    """
    issues = []

    for i, atom in enumerate(atoms):
        # 检查时间连续性
        if i > 0:
            prev_end = parse_time(atoms[i-1]['end'])
            curr_start = parse_time(atom['start'])
            gap = (curr_start - prev_end).total_seconds()

            if gap > 30:  # 超过30秒的空隙
                issues.append(f"Atom {atom['atom_id']}: 大间隔 {gap}秒")

        # 检查文本长度
        if len(atom['merged_text']) < 10:
            issues.append(f"Atom {atom['atom_id']}: 文本过短")

        if len(atom['merged_text']) > 500:
            issues.append(f"Atom {atom['atom_id']}: 文本过长，可能需要拆分")

    return issues
```

### 输出
```json
{
  "total_atoms": 856,
  "atoms": [
    {
      "atom_id": "A001",
      "start": "00:00:08",
      "end": "00:00:25",
      "merged_text": "开始了没有啊，我看看开始了没有...",
      "type": "开场确认",
      "completeness": "完整",
      "source_subtitle_ids": [2, 3, 4, 5]
    },
    {
      "atom_id": "A012",
      "start": "00:08:20",
      "end": "00:09:15",
      "merged_text": "1962年国民党残军撤到金三角，这是整个金三角问题的起源...",
      "type": "叙述历史",
      "completeness": "完整",
      "source_subtitle_ids": [85, 86, 87, 88, 89]
    }
  ]
}
```

保存为：`data/processed/atoms.json`

---

## 阶段3：语义分析 (Analyze)

### 目标
给每个原子打上多维度的标签

### 3.1 主题标注

#### 提示词设计

```python
# prompts/tag_topics.txt

分析这段文本属于哪些主题。

【文本】
{atom_text}

【可选主题】
一级主题：
- 历史叙事：讲述过去的事件
- 人物分析：分析人物性格、动机、行为
- 观众互动：读来信、回应弹幕、答疑
- 当代对比：将历史与当代进行对比
- 个人观点：博主的评价和看法
- 闲聊过场：开场、技术性对话、无关内容

二级主题（如果是历史叙事）：
- 1960s背景/坤沙崛起/罗星汉对抗/权力斗争/军事冲突/经济博弈/最终结局

【要求】
1. 主题可多选
2. 给每个主题打分（1-10），表示相关度
3. 提取关键实体：人物、地点、时间、事件

【输出JSON】
{
  "primary_topic": "历史叙事",
  "secondary_topics": ["坤沙崛起", "军事冲突"],
  "topic_scores": {
    "历史叙事": 10,
    "坤沙崛起": 9,
    "军事冲突": 8
  },
  "entities": {
    "persons": ["坤沙"],
    "locations": ["金三角", "缅甸"],
    "time_points": ["1962年"],
    "events": ["国民党撤退"],
    "concepts": ["军事割据", "权力真空"]
  }
}
```

#### 批量处理

```python
def analyze_topics(atoms):
    """
    并行分析所有原子的主题
    """
    analyzed = []

    for atom in atoms:
        prompt = TOPIC_PROMPT.format(atom_text=atom['merged_text'])

        response = call_claude(prompt)
        analysis = json.loads(response)

        analyzed.append({
            **atom,
            "topics": analysis
        })

    return analyzed
```

### 3.2 情感与能量标注

#### 提示词

```python
# prompts/tag_emotion.txt

分析这段文本的情感和能量。

【文本】
{atom_text}

【分析维度】
1. 情感类型：
   - 客观叙述：平铺直叙，无明显情感
   - 激动/愤怒：语气强烈，用词激烈
   - 幽默/调侃：开玩笑、讽刺
   - 同情/感慨：表达同情或感慨
   - 批判/质疑：批评、质疑

2. 能量值（1-10）：
   - 1-3：平静、低沉
   - 4-6：正常叙述
   - 7-8：有激情、投入
   - 9-10：高度激动、高潮

3. 趋势：递增/递减/平稳

【输出JSON】
{
  "emotion_type": "激动",
  "energy_level": 9,
  "energy_trend": "递增",
  "indicators": ["用词激烈", "语气强调", "重复强调"]
}
```

### 3.3 内容价值标注

#### 提示词

```python
# prompts/tag_value.txt

评估这段内容的价值和可剪辑性。

【文本】
{atom_text}

【评估标准】

1. 信息密度（1-10）：
   - 1-3：重复、闲聊、技术性对话
   - 4-6：一般性叙述
   - 7-8：有价值的信息
   - 9-10：核心信息、关键观点、金句

2. 可剪辑性：
   - 必剪：核心内容，不能删
   - 可剪：有价值但非必需
   - 可删：冗余、重复
   - 必删：无意义填充

3. 独立性：
   - 独立：可单独成片，不需上下文
   - 需铺垫：需要前置背景
   - 需补充：需要后续解释
   - 依赖上下文：必须在特定上下文中

4. 特殊价值：
   - 金句：值得单独摘录
   - 高潮点：情节转折或冲突顶点
   - 争议点：可能引发讨论
   - 无

【输出JSON】
{
  "information_density": 9,
  "editability": "必剪",
  "independence": "需铺垫",
  "special_value": "高潮点",
  "reason": "描述了坤沙的关键军事行动，是权力转折点"
}
```

### 3.4 生成Embedding向量

```python
from openai import OpenAI

def generate_embeddings(atoms):
    """
    为每个原子生成语义向量
    """
    client = OpenAI(api_key="your_key")

    texts = [atom['merged_text'] for atom in atoms]

    # 批量生成（OpenAI支持批量）
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=texts
    )

    for i, atom in enumerate(atoms):
        atom['embedding'] = response.data[i].embedding

    return atoms
```

### 输出
```json
{
  "atoms": [
    {
      "atom_id": "A012",
      "merged_text": "1962年国民党残军...",
      "topics": {
        "primary_topic": "历史叙事",
        "secondary_topics": ["1960s背景"],
        "topic_scores": {"历史叙事": 10, "1960s背景": 9},
        "entities": {
          "persons": ["国民党残军"],
          "locations": ["金三角"],
          "time_points": ["1962年"],
          "events": ["国民党撤退"],
          "concepts": ["军事割据"]
        }
      },
      "emotion": {
        "emotion_type": "客观叙述",
        "energy_level": 6,
        "energy_trend": "平稳"
      },
      "value": {
        "information_density": 9,
        "editability": "必剪",
        "independence": "需铺垫",
        "special_value": "关键背景"
      },
      "embedding": [0.023, 0.451, -0.234, ...]
    }
  ]
}
```

保存为：`data/processed/analyzed_atoms.json`

---

## 阶段4：结构重组 (Structure)

### 目标
把分散的原子重新组织成结构化知识

### 4.1 构建实体卡片

#### 提示词

```python
# prompts/build_entity.txt

基于以下原子，构建"{entity_name}"的实体卡片。

【相关原子】
{related_atoms_text}

【要求】
1. 生成人物/地点/事件的完整画像
2. 按不同facet（面向）组织信息
3. 提取时间线
4. 识别关系网络
5. 生成AI总结

【输出JSON】
{
  "entity_id": "person_kunsha",
  "type": "person",
  "name": "坤沙",
  "profile": {
    "basic_info": "1934-2007，金三角军阀...",
    "key_characteristics": ["权谋高手", "善用地缘政治"],
    "historical_significance": "..."
  },
  "facets": {
    "性格特质": {
      "summary": "...",
      "supporting_atoms": ["A023", "A045"]
    },
    "权力手段": {
      "summary": "...",
      "supporting_atoms": ["A034", "A056"]
    }
  },
  "timeline": [
    {"year": "1962", "event": "进入金三角", "atoms": ["A012"]},
    {"year": "1985", "event": "关键军事行动", "atoms": ["A045"]}
  ],
  "relationships": [
    {
      "target": "罗星汉",
      "relation": "对手",
      "description": "长期权力竞争",
      "atoms": ["A023", "A067"]
    }
  ]
}
```

#### 实现

```python
def build_entities(analyzed_atoms):
    """
    自动识别和构建所有实体
    """
    # 1. 收集所有提到的实体
    entity_mentions = {}

    for atom in analyzed_atoms:
        persons = atom['topics']['entities']['persons']
        for person in persons:
            if person not in entity_mentions:
                entity_mentions[person] = []
            entity_mentions[person].append(atom['atom_id'])

    # 2. 为每个实体构建卡片
    entities = []

    for entity_name, atom_ids in entity_mentions.items():
        if len(atom_ids) < 3:  # 至少出现3次才建卡片
            continue

        # 获取相关原子的文本
        related_atoms = [a for a in analyzed_atoms if a['atom_id'] in atom_ids]
        atoms_text = "\n\n".join([
            f"[{a['atom_id']}] {a['merged_text']}"
            for a in related_atoms
        ])

        # 调用AI构建实体卡片
        prompt = BUILD_ENTITY_PROMPT.format(
            entity_name=entity_name,
            related_atoms_text=atoms_text
        )

        response = call_claude(prompt)
        entity_card = json.loads(response)

        # 生成实体的embedding
        entity_summary = entity_card['profile']['basic_info']
        entity_card['embedding'] = generate_embedding(entity_summary)

        entities.append(entity_card)

    return entities
```

### 4.2 构建主题网络

#### 提示词

```python
# prompts/build_topic_network.txt

基于所有原子，构建主题网络。

【所有主题统计】
{topic_statistics}

【相关原子示例】
{sample_atoms}

【要求】
1. 识别主要主题和子主题的层级关系
2. 为每个主题生成定义和描述
3. 识别主题之间的关系（并列/包含/因果）
4. 设计叙事模板

【输出JSON】
{
  "topic_id": "theme_power_struggle",
  "name": "权力斗争",
  "definition": "...",
  "sub_topics": [
    {
      "name": "军事对抗",
      "atoms": ["A045", "A067"],
      "description": "..."
    }
  ],
  "narrative_templates": [
    {
      "template_name": "双雄争霸",
      "structure": "背景 → 崛起 → 对抗 → 结局",
      "applicable_atoms": ["A012", "A023", ...],
      "estimated_duration": "15:00"
    }
  ]
}
```

#### 实现

```python
def build_topic_network(analyzed_atoms):
    """
    构建主题网络
    """
    # 1. 统计所有主题出现频率
    topic_stats = {}
    topic_atoms = {}

    for atom in analyzed_atoms:
        topics = atom['topics']['secondary_topics']
        for topic in topics:
            if topic not in topic_stats:
                topic_stats[topic] = 0
                topic_atoms[topic] = []
            topic_stats[topic] += 1
            topic_atoms[topic].append(atom['atom_id'])

    # 2. 为主要主题（出现10次以上）建立详细网络
    topic_network = []

    for topic_name, count in topic_stats.items():
        if count < 10:
            continue

        related_atoms = [a for a in analyzed_atoms if a['atom_id'] in topic_atoms[topic_name]]

        # 调用AI构建主题网络
        prompt = BUILD_TOPIC_PROMPT.format(
            topic_name=topic_name,
            topic_statistics=json.dumps(topic_stats, ensure_ascii=False),
            sample_atoms=json.dumps([a['merged_text'] for a in related_atoms[:10]], ensure_ascii=False)
        )

        response = call_claude(prompt)
        topic_card = json.loads(response)

        topic_card['embedding'] = generate_embedding(topic_card['definition'])

        topic_network.append(topic_card)

    return topic_network
```

### 4.3 识别叙事片段

#### 提示词

```python
# prompts/identify_narratives.txt

识别视频中完整的叙事片段。

【原子序列】
{sequential_atoms}

【要求】
1. 找出"完整故事"：有开头、发展、结局的片段
2. 识别叙事结构（三幕剧/编年体/主题并列）
3. 评估完整性和独立性
4. 设计不同剪辑方案

【输出JSON】
{
  "segment_id": "narrative_001",
  "title": "坤沙的崛起（1962-1985）",
  "atoms": ["A012", "A023", "A045", "A056"],
  "structure": {
    "setup": {"atoms": ["A012"], "duration": "02:30"},
    "conflict": {"atoms": ["A023", "A034"], "duration": "08:15"},
    "climax": {"atoms": ["A045"], "duration": "03:10"}
  },
  "completeness": "完整",
  "independence": "需要前置背景",
  "alternative_cuts": [
    {"name": "完整版", "duration": "15:35"},
    {"name": "精简版", "cuts": ["删除A034"], "duration": "12:00"}
  ]
}
```

### 输出

生成三个文件：

**1. entities.json**
```json
{
  "entities": [
    {
      "entity_id": "person_kunsha",
      "type": "person",
      "name": "坤沙",
      "profile": {...},
      "facets": {...},
      "timeline": [...],
      "relationships": [...],
      "embedding": [...]
    }
  ]
}
```

**2. topics.json**
```json
{
  "topics": [
    {
      "topic_id": "theme_power_struggle",
      "name": "权力斗争",
      "sub_topics": [...],
      "narrative_templates": [...],
      "embedding": [...]
    }
  ]
}
```

**3. narratives.json**
```json
{
  "narratives": [
    {
      "segment_id": "narrative_001",
      "title": "坤沙的崛起",
      "structure": {...},
      "alternative_cuts": [...]
    }
  ]
}
```

---

## 阶段5：建立索引 (Index)

### 目标
建立多维度检索系统

### 5.1 语义向量索引

```python
import chromadb

def build_semantic_index(analyzed_atoms, entities, topics):
    """
    把所有embedding存入向量数据库
    """
    client = chromadb.PersistentClient(path="data/output/vector_db")

    # 创建collection
    collection = client.create_collection(
        name="video_knowledge",
        metadata={"description": "金三角大佬4的知识库"}
    )

    # 添加原子
    for atom in analyzed_atoms:
        collection.add(
            ids=[atom['atom_id']],
            embeddings=[atom['embedding']],
            metadatas=[{
                "type": "atom",
                "start_time": atom['start'],
                "end_time": atom['end'],
                "primary_topic": atom['topics']['primary_topic'],
                "value_score": atom['value']['information_density']
            }],
            documents=[atom['merged_text']]
        )

    # 添加实体
    for entity in entities:
        collection.add(
            ids=[entity['entity_id']],
            embeddings=[entity['embedding']],
            metadatas=[{
                "type": "entity",
                "entity_type": entity['type'],
                "name": entity['name']
            }],
            documents=[entity['profile']['basic_info']]
        )

    # 添加主题
    for topic in topics:
        collection.add(
            ids=[topic['topic_id']],
            embeddings=[topic['embedding']],
            metadatas=[{
                "type": "topic",
                "name": topic['name']
            }],
            documents=[topic['definition']]
        )

    print(f"向量索引构建完成，共{collection.count()}条记录")
```

### 5.2 结构化索引

```python
def build_structured_index(analyzed_atoms, entities):
    """
    构建多维度的结构化索引
    """
    indexes = {
        "by_time": {},
        "by_person": {},
        "by_topic": {},
        "by_value": {},
        "by_emotion": {}
    }

    # 按时间索引（按10分钟分组）
    for atom in analyzed_atoms:
        time_bucket = get_time_bucket(atom['start'], bucket_size=600)  # 10分钟
        if time_bucket not in indexes['by_time']:
            indexes['by_time'][time_bucket] = []
        indexes['by_time'][time_bucket].append(atom['atom_id'])

    # 按人物索引
    for atom in analyzed_atoms:
        persons = atom['topics']['entities']['persons']
        for person in persons:
            if person not in indexes['by_person']:
                indexes['by_person'][person] = []
            indexes['by_person'][person].append(atom['atom_id'])

    # 按主题索引
    for atom in analyzed_atoms:
        topics = atom['topics']['secondary_topics']
        for topic in topics:
            if topic not in indexes['by_topic']:
                indexes['by_topic'][topic] = []
            indexes['by_topic'][topic].append(atom['atom_id'])

    # 按价值索引
    for atom in analyzed_atoms:
        value = atom['value']['information_density']
        value_tier = f"{(value-1)//2*2+1}-{(value-1)//2*2+2}分"
        if value_tier not in indexes['by_value']:
            indexes['by_value'][value_tier] = []
        indexes['by_value'][value_tier].append(atom['atom_id'])

    # 按情感索引
    for atom in analyzed_atoms:
        emotion = atom['emotion']['emotion_type']
        if emotion not in indexes['by_emotion']:
            indexes['by_emotion'][emotion] = []
        indexes['by_emotion'][emotion].append(atom['atom_id'])

    return indexes
```

### 5.3 知识图谱

```python
import networkx as nx

def build_knowledge_graph(entities, analyzed_atoms):
    """
    构建知识图谱
    """
    G = nx.DiGraph()

    # 添加实体节点
    for entity in entities:
        G.add_node(
            entity['entity_id'],
            type=entity['type'],
            name=entity['name'],
            data=entity
        )

    # 添加关系边
    for entity in entities:
        if 'relationships' in entity:
            for rel in entity['relationships']:
                target_id = find_entity_id(entities, rel['target'])
                if target_id:
                    G.add_edge(
                        entity['entity_id'],
                        target_id,
                        relation=rel['relation'],
                        atoms=rel['atoms'],
                        description=rel.get('description', '')
                    )

    # 保存为JSON（NetworkX格式）
    graph_data = nx.node_link_data(G)

    return graph_data
```

### 输出

**1. vector_db/** (向量数据库目录)
```
vector_db/
├── chroma.sqlite3
└── [binary files]
```

**2. indexes/structured.json**
```json
{
  "by_time": {
    "00:00-00:10": ["A001", "A002", ...],
    "00:10-00:20": ["A015", "A016", ...]
  },
  "by_person": {
    "坤沙": ["A012", "A023", "A045", ...],
    "罗星汉": ["A023", "A034", ...]
  },
  "by_topic": {
    "军事冲突": ["A045", "A067"],
    "权力斗争": ["A023", "A045", "A067"]
  },
  "by_value": {
    "9-10分": ["A045", "A067"],
    "7-8分": ["A023", "A034"]
  }
}
```

**3. indexes/graph.json**
```json
{
  "nodes": [
    {"id": "person_kunsha", "type": "person", "name": "坤沙"}
  ],
  "links": [
    {
      "source": "person_kunsha",
      "target": "person_luoxinghan",
      "relation": "对手",
      "atoms": ["A023", "A067"]
    }
  ]
}
```

---

## 阶段6：生成剪辑方案 (Generate)

### 目标
基于知识库，自动生成剪辑方案

### 6.1 查询接口

```python
class VideoKnowledgeBase:
    def __init__(self, data_path):
        self.atoms = load_json(f"{data_path}/atoms.json")
        self.entities = load_json(f"{data_path}/entities.json")
        self.topics = load_json(f"{data_path}/topics.json")
        self.narratives = load_json(f"{data_path}/narratives.json")
        self.indexes = load_json(f"{data_path}/indexes/structured.json")

        self.vector_db = chromadb.PersistentClient(f"{data_path}/vector_db")
        self.collection = self.vector_db.get_collection("video_knowledge")

    def semantic_search(self, query, top_k=10, filter_type=None):
        """语义搜索"""
        query_embedding = generate_embedding(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"type": filter_type} if filter_type else None
        )

        return results

    def get_entity(self, entity_name):
        """获取实体卡片"""
        for entity in self.entities['entities']:
            if entity['name'] == entity_name:
                return entity
        return None

    def get_atoms_by_topic(self, topic_name):
        """按主题获取原子"""
        atom_ids = self.indexes['by_topic'].get(topic_name, [])
        return [a for a in self.atoms['atoms'] if a['atom_id'] in atom_ids]

    def get_atoms_by_person(self, person_name):
        """按人物获取原子"""
        atom_ids = self.indexes['by_person'].get(person_name, [])
        return [a for a in self.atoms['atoms'] if a['atom_id'] in atom_ids]

    def get_high_value_atoms(self, min_score=8):
        """获取高价值原子"""
        return [a for a in self.atoms['atoms']
                if a['value']['information_density'] >= min_score]
```

### 6.2 生成剪辑方案

```python
def generate_edit_plan(kb, user_request):
    """
    根据用户需求生成剪辑方案
    """
    # 提示词
    prompt = f"""
基于视频知识库，为以下需求生成剪辑方案：

【用户需求】
{user_request}

【可用资源】
- 总计{len(kb.atoms['atoms'])}个信息原子
- {len(kb.entities['entities'])}个实体
- {len(kb.topics['topics'])}个主题
- {len(kb.narratives['narratives'])}个叙事片段

【任务】
1. 理解用户需求
2. 从知识库中选择合适的素材
3. 设计叙事结构
4. 生成完整的剪辑方案

【输出JSON】
{{
  "plan_name": "方案名称",
  "target_duration": "目标时长",
  "narrative_structure": "叙事结构描述",
  "required_atoms": ["A001", "A012", ...],
  "timeline": [
    {{"order": 1, "type": "clip", "atom_id": "A012", "start": "00:08:20", "end": "00:09:15"}},
    {{"order": 2, "type": "transition", "content": "转场文案", "duration": "00:15"}},
    ...
  ],
  "editing_suggestions": ["建议1", "建议2"],
  "alternative_versions": [...]
}}
"""

    # Step 1: 语义搜索相关内容
    search_results = kb.semantic_search(user_request, top_k=20)

    # Step 2: 准备上下文
    context = {
        "search_results": search_results,
        "available_narratives": kb.narratives['narratives']
    }

    # Step 3: 调用AI生成方案
    response = call_claude(prompt + "\n\n【搜索结果】\n" + json.dumps(context, ensure_ascii=False))

    plan = json.loads(response)

    # Step 4: 丰富方案细节
    plan = enrich_plan(kb, plan)

    return plan

def enrich_plan(kb, plan):
    """
    丰富剪辑方案的细节
    """
    # 获取所有涉及的原子的完整信息
    atom_ids = plan['required_atoms']
    atoms = [a for a in kb.atoms['atoms'] if a['atom_id'] in atom_ids]

    # 计算实际时长
    total_duration = sum([
        parse_duration(a['end']) - parse_duration(a['start'])
        for a in atoms
    ])

    plan['actual_duration'] = str(total_duration)

    # 添加完整的原子数据
    plan['atoms_detail'] = atoms

    # 生成ffmpeg命令（可选）
    plan['ffmpeg_commands'] = generate_ffmpeg_commands(atoms)

    return plan
```

### 6.3 交互式优化

```python
def interactive_editing(kb, initial_request):
    """
    交互式剪辑方案生成
    """
    # 生成初始方案
    plan = generate_edit_plan(kb, initial_request)

    print(f"生成方案：{plan['plan_name']}")
    print(f"时长：{plan['actual_duration']}")
    print(f"包含{len(plan['required_atoms'])}个片段")

    # 用户反馈循环
    while True:
        feedback = input("\n需要调整吗？(例如：'太长了，缩短到10分钟' 或 '完成')：")

        if feedback == "完成":
            break

        # 根据反馈调整方案
        adjustment_prompt = f"""
当前方案：
{json.dumps(plan, ensure_ascii=False)}

用户反馈：
{feedback}

请调整方案以满足用户需求。
"""

        response = call_claude(adjustment_prompt)
        plan = json.loads(response)
        plan = enrich_plan(kb, plan)

        print(f"\n已调整：{plan['plan_name']}")
        print(f"新时长：{plan['actual_duration']}")

    return plan
```

### 输出

```json
{
  "plan_id": "plan_001",
  "plan_name": "坤沙：从小军阀到金三角之王",
  "target_duration": "15:00",
  "actual_duration": "15:23",

  "narrative_structure": "三幕剧：起源(3min) → 崛起(8min) → 巅峰(4min)",

  "required_atoms": ["A012", "A023", "A045", "A056", "A078", "A089"],

  "timeline": [
    {
      "order": 1,
      "type": "clip",
      "atom_id": "A012",
      "start": "00:08:20",
      "end": "00:09:15",
      "duration": "00:55",
      "purpose": "介绍1962年背景"
    },
    {
      "order": 2,
      "type": "transition",
      "content": "在这个权力真空中，一个名叫坤沙的年轻人开始崭露头角...",
      "duration": "00:10",
      "voiceover": true
    },
    {
      "order": 3,
      "type": "clip",
      "atom_id": "A023",
      "start": "00:18:05",
      "end": "00:19:30",
      "duration": "01:25",
      "purpose": "坤沙初期发展"
    }
  ],

  "atoms_detail": [
    {
      "atom_id": "A012",
      "merged_text": "完整文本...",
      "start": "00:08:20",
      "end": "00:09:15"
    }
  ],

  "editing_suggestions": [
    "片段1和2之间可添加金三角地图动画",
    "片段3(A045)是高潮，建议配激昂BGM",
    "考虑使用历史照片作为B-roll"
  ],

  "alternative_versions": [
    {
      "version_name": "10分钟精简版",
      "changes": "删除A056，压缩A023",
      "estimated_duration": "10:15"
    }
  ],

  "ffmpeg_commands": [
    "ffmpeg -i input.mp4 -ss 00:08:20 -to 00:09:15 -c copy clip_001.mp4",
    "ffmpeg -i input.mp4 -ss 00:18:05 -to 00:19:30 -c copy clip_002.mp4"
  ]
}
```

---

## 完整示例：端到端流程

```python
# main.py

def process_video_subtitle(srt_path, output_dir):
    """
    完整处理流程
    """
    print("=" * 50)
    print("视频字幕深度分析系统")
    print("=" * 50)

    # 阶段1：解析
    print("\n[1/6] 解析字幕文件...")
    parsed = parse_srt(srt_path)
    cleaned = clean_subtitles(parsed)
    save_json(cleaned, f"{output_dir}/parsed_subtitles.json")
    print(f"✓ 解析完成：{len(cleaned)}条字幕")

    # 阶段2：原子化
    print("\n[2/6] 原子化处理（预计30-40分钟）...")
    atoms = atomize_subtitles(cleaned)
    save_json(atoms, f"{output_dir}/atoms.json")
    print(f"✓ 原子化完成：{len(atoms)}个信息原子")

    # 阶段3：语义分析
    print("\n[3/6] 语义分析（预计20-30分钟）...")
    analyzed = analyze_atoms(atoms)  # 包括主题、情感、价值标注
    analyzed = generate_embeddings(analyzed)
    save_json(analyzed, f"{output_dir}/analyzed_atoms.json")
    print(f"✓ 分析完成")

    # 阶段4：结构重组
    print("\n[4/6] 构建知识结构（预计10-15分钟）...")
    entities = build_entities(analyzed)
    topics = build_topic_network(analyzed)
    narratives = identify_narratives(analyzed)
    save_json(entities, f"{output_dir}/entities.json")
    save_json(topics, f"{output_dir}/topics.json")
    save_json(narratives, f"{output_dir}/narratives.json")
    print(f"✓ 识别{len(entities)}个实体，{len(topics)}个主题，{len(narratives)}个叙事片段")

    # 阶段5：建立索引
    print("\n[5/6] 建立索引...")
    build_semantic_index(analyzed, entities, topics)
    indexes = build_structured_index(analyzed, entities)
    graph = build_knowledge_graph(entities, analyzed)
    save_json(indexes, f"{output_dir}/indexes/structured.json")
    save_json(graph, f"{output_dir}/indexes/graph.json")
    print(f"✓ 索引构建完成")

    # 阶段6：生成元信息
    print("\n[6/6] 生成知识库元信息...")
    meta = generate_metadata(analyzed, entities, topics, narratives)
    save_json(meta, f"{output_dir}/meta.json")
    print(f"✓ 完成！")

    print(f"\n知识库已保存到：{output_dir}")
    print("\n现在可以使用知识库进行：")
    print("- 语义搜索")
    print("- 生成剪辑方案")
    print("- 主题合集制作")
    print("- 原创叙事创作")

# 使用示例
if __name__ == "__main__":
    process_video_subtitle(
        srt_path="D:/YouTube_Downloads/金三角大佬4：缅北双雄时代1962-1998.srt",
        output_dir="data/output/jinSanJiao_04"
    )

    # 加载知识库
    kb = VideoKnowledgeBase("data/output/jinSanJiao_04")

    # 生成剪辑方案
    plan = interactive_editing(kb, "我想做一个15分钟的视频，讲坤沙是怎么崛起的")

    save_json(plan, "output/edit_plan_001.json")
```

---

## 时间和成本估算

### 处理一个2小时视频

| 阶段 | 时间 | API成本(Claude) |
|------|------|----------------|
| 1. 解析字幕 | 1分钟 | $0 |
| 2. 原子化 | 30-40分钟 | ~$5-8 |
| 3. 语义分析 | 20-30分钟 | ~$8-12 |
| 4. 结构重组 | 10-15分钟 | ~$3-5 |
| 5. 建立索引 | 5分钟 | ~$1 (embedding) |
| **总计** | **1-1.5小时** | **~$17-26** |

### 后续使用
- 加载知识库：<1秒
- 语义搜索：<1秒
- 生成剪辑方案：10-30秒，~$0.5

---

## 总结

每一部分的核心：

1. **解析**：把字幕变成结构化数据
2. **原子化**：AI智能合并，形成语义单元
3. **分析**：多维度标注（主题/情感/价值/实体）+ 生成embedding
4. **重组**：构建实体卡片、主题网络、叙事片段
5. **索引**：多维检索（语义/结构化/图谱）
6. **生成**：基于知识库自动生成剪辑方案

**核心技术**：
- AI理解：Claude API
- 语义搜索：text-embedding-3-large + Chromadb
- 存储：JSON + 向量数据库

**关键原则**：
1. ✅ **分层结构**：原子 → 概念 → 叙事
2. ✅ **语义向量**：让AI能做智能搜索
3. ✅ **多维索引**：任何角度都能快速找到素材
4. ✅ **AI摘要**：每一层都有理解，不用重复分析
5. ✅ **结构化 + 灵活性**：既有清晰结构，又能灵活组合

**这样设计后：**
- 任何AI（包括未来的你/我/其他AI）拿到这个文件夹
- 都能立刻理解视频内容
- 快速找到需要的素材
- 自动生成剪辑方案
