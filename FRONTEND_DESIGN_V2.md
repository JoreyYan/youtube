# 前端设计方案 v2.0 - 基于完整Phase 2功能

**更新日期**: 2025-01-XX
**状态**: 设计阶段
**技术栈**: Next.js 14 + TypeScript + TailwindCSS + Shadcn/ui

---

## 📊 现状分析

### 已有前端 (atom-viewer)
```
现有页面:
├── / (首页 - 项目列表)
├── /projects/[id] (项目概览)
├── /projects/[id]/atoms (原子列表)
└── /projects/[id]/segments/[num] (片段详情)

现有组件:
├── AtomList.tsx - 原子列表
├── AtomDetail.tsx - 原子详情
├── FilterBar.tsx - 过滤器
├── StatsCards.tsx - 统计卡片
├── TypeDistribution.tsx - 类型分布
└── QualityReport.tsx - 质量报告
```

### 新增后端能力 (Phase 2 完整)
```
✅ 6个AI模块:
- DataLoader (统一数据访问)
- ContextManager (多会话管理)
- QueryUnderstanding (意图识别)
- HybridRetriever (8种检索策略)
- ResponseGenerator (自然语言生成)
- ConversationalInterface (主控制器)

✅ 新增数据:
- entities.json (实体索引)
- topics.json (主题网络)
- knowledge_graph.json (知识图谱)
- video_structure.md (结构报告)
- creative_angles.json (创作建议)
```

---

## 🎯 设计目标

### 核心原则
1. **AI优先**: AI对话作为主要交互方式
2. **数据可视化**: 充分展示Phase 2的丰富数据
3. **渐进增强**: 在现有基础上升级，而非重写
4. **移动友好**: 响应式设计，支持手机使用

### 关键页面优先级
1. 🔥 **AI Chat** (新增，最高优先级)
2. ⭐ **Knowledge Graph** (新增，独特卖点)
3. 🔧 **Enhanced Dashboard** (升级现有)
4. 💡 **Creative Studio** (新增，创作工具)

---

## 📱 完整页面架构

```
┌─────────────────────────────────────────────────────────┐
│  Navigation Bar (全局导航)                               │
│  [Logo] [Projects] [Chat] [Explore] [Create] [Settings] │
└─────────────────────────────────────────────────────────┘

页面结构:
/
├── / (首页 - 项目列表)
│
├── /projects/[id]/ (项目主页 - 升级版)
│   ├── overview (概览仪表板)
│   ├── chat (AI对话 - 新增 ⭐)
│   ├── timeline (时间轴视图)
│   ├── atoms (原子浏览 - 升级)
│   ├── segments (片段浏览)
│   ├── entities (实体探索 - 新增)
│   ├── topics (主题网络 - 新增)
│   ├── graph (知识图谱 - 新增 ⭐)
│   ├── creative (创作工具 - 新增)
│   └── reports (分析报告)
│
└── /settings (设置)
```

---

## 🎨 UI设计 - 详细Mockup

### 1️⃣ 项目主页 (Dashboard) - 升级版

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Projects / 缅北双雄时代历史讲座                    [Share] [⚙]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 📹 视频信息                                                      │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 标题: 缅北双雄时代历史讲座                                    ││
│ │ 时长: 5:23  |  分析时间: 2025-01-05                          ││
│ │ 质量分数: ⭐⭐⭐⭐☆ 4.2/5                                      ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ 🤖 快速操作                                                      │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│ │ 💬 AI对话 │ │ 🕸️ 图谱   │ │ 🎬 创作   │ │ 📊 报告   │           │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                 │
│ 📊 内容统计                                                      │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│ │  16     │ │   1     │ │  15     │ │   1     │ │  46     │  │
│ │ 原子     │ │ 片段     │ │ 实体    │ │ 主题    │ │ 关系    │  │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
│                                                                 │
│ 🎯 核心主题                                                      │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 金三角历史 ████████████ 80%                                  ││
│ │   缅北地区 ██████ 45%                                        ││
│ │   双雄时代 █████ 35%                                         ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ 🔑 关键实体                                                      │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ [彭家声] [缅北] [金三角] [1962-1998] [中国] [Myanmar]         ││
│ │ [教父系列] [历史讲座] [树挪死人挪活] ...                       ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ 📝 AI执行摘要                                                    │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 这是一场以"教父系列"叙事风格呈现的金三角历史讲座，聚焦        ││
│ │ 1962-1998年间的"缅北双雄"时代。内容强调金三角地区与中国      ││
│ │ 的深厚联系，被称为"小中国"，当地居民多通晓汉语普通话...      ││
│ │                                                              ││
│ │ [展开全文] [Ask AI: "更详细的摘要?"]                          ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2️⃣ AI Chat 页面 - 🔥 最高优先级

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Dashboard / AI Chat              🔍 Search in Chat  [New +]    │
├─────────────────────────────────────────────────────────────────┤
│ Sidebar (30%)    │ Chat Window (70%)                            │
│                  │                                              │
│ 💬 会话历史       │ ┌─────────────────────────────────────────┐ │
│ ┌──────────────┐ │ │ 💬 AI 视频助手                          │ │
│ │ ✨ 新对话     │ │ │ 已分析: 缅北双雄时代历史讲座              │ │
│ └──────────────┘ │ │ 模式: 🔍 探索模式                        │ │
│                  │ └─────────────────────────────────────────┘ │
│ 📅 今天          │                                              │
│ ┌──────────────┐ │ ┌─────────────────────────────────────────┐ │
│ │ 🔵 视频主要... │ │ │ 👤 User (12:35)                        │ │
│ │   内容是什么   │ │ │                                        │ │
│ └──────────────┘ │ │ What is this video about?              │ │
│ ┌──────────────┐ │ └─────────────────────────────────────────┘ │
│ │ 🟢 谁在视频...  │ │                                              │
│ │   中被提到     │ │ ┌─────────────────────────────────────────┐ │
│ └──────────────┘ │ │ 🤖 AI Assistant (12:35)                  │ │
│                  │ │                                            │ │
│ 📅 昨天          │ │ This video is an introductory segment    │ │
│ ┌──────────────┐ │ │ of a lecture series focused on the       │ │
│ │ 🟣 创作建议...  │ │ history of the Golden Triangle. The      │ │
│ └──────────────┘ │ │ speaker employs a narrative style...     │ │
│                  │ │                                            │ │
│ 🗂️ 全部会话 (15) │ │ 📎 Sources:                              │ │
│                  │ │ ┌──────────────────────────────────────┐  │ │
│                  │ │ │ [1] Segment SEG_001 | 00:00-05:23   │  │ │
│                  │ │ │     Score: 0.75 | Type: narrative   │  │ │
│                  │ │ │     [View in Timeline →]            │  │ │
│                  │ │ └──────────────────────────────────────┘  │ │
│                  │ │                                            │ │
│                  │ │ ⚡ Response: 3.2s | Confidence: 0.80      │ │
│                  │ └─────────────────────────────────────────┘ │
│                  │                                              │
│                  │ ┌─────────────────────────────────────────┐ │
│                  │ │ 👤 User (12:36)                        │ │
│                  │ │                                        │ │
│                  │ │ Tell me more about the main topics    │ │
│                  │ └─────────────────────────────────────────┘ │
│                  │                                              │
│                  │ ┌─────────────────────────────────────────┐ │
│                  │ │ 🤖 AI Assistant (12:36) [Streaming...] │ │
│                  │ │                                        │ │
│                  │ │ The main topics revolve around...▊    │ │
│                  │ └─────────────────────────────────────────┘ │
│                  │                                              │
│                  │ ┌─────────────────────────────────────────┐ │
│                  │ │ 💡 Quick Prompts:                       │ │
│                  │ │ • 总结视频内容                            │ │
│                  │ │ • 提到了哪些实体?                         │ │
│                  │ │ • 推荐短视频片段                          │ │
│                  │ │ • 分析核心观点                            │ │
│                  │ └─────────────────────────────────────────┘ │
│                  │                                              │
│                  │ ┌─────────────────────────────────────────┐ │
│                  │ │ Type your message...                    │ │
│                  │ │                              [Send 📤]  │ │
│                  │ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Chat功能特性**:
- ✅ 多会话管理（sidebar）
- ✅ 实时流式输出（SSE）
- ✅ 来源引用（可跳转到timeline）
- ✅ 快速提示词（Quick Prompts）
- ✅ 7种查询意图自动识别
- ✅ 上下文连续对话

---

### 3️⃣ Knowledge Graph 页面 - ⭐ 独特卖点

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Dashboard / Knowledge Graph         Layout: [Force] [Tree] [⚙]│
├─────────────────────────────────────────────────────────────────┤
│ Sidebar (25%)    │ Graph Canvas (75%)                           │
│                  │                                              │
│ 🎯 图谱控制       │         彭家声 ●                             │
│                  │           │ \                                │
│ 显示选项:        │           │  \                               │
│ ☑ 人物 (6)       │           │   缅北 ●                         │
│ ☑ 地点 (2)       │           │    │ \                           │
│ ☑ 时间 (3)       │   金三角 ●│    │  \                          │
│ ☑ 事件 (1)       │      │ \  │    │   Myanmar ●                │
│ ☑ 概念 (3)       │      │  \ │    │                            │
│                  │   中国 ● \│    │                            │
│ 关系类型:        │           1962-1998 ●                        │
│ ☑ 提到 (24)      │                                              │
│ ☑ 相关 (12)      │                                              │
│ ☑ 属于 (10)      │        [Zoom: ━━━●━━━ 100%]                 │
│                  │        [Pan] [Zoom] [Fullscreen]            │
│ 🔍 搜索实体       │                                              │
│ ┌──────────────┐ │                                              │
│ │ 搜索节点...   │ │ ┌─────────────────────────────────────────┐ │
│ └──────────────┘ │ │ 📊 Selected Node: 彭家声                 │ │
│                  │ │                                          │ │
│ 🎨 图例          │ │ Type: 人物 (Person)                       │ │
│ ● 人物 (蓝色)    │ │ Mentions: 8 atoms                         │ │
│ ● 地点 (绿色)    │ │ Importance: High (0.85)                   │ │
│ ● 时间 (橙色)    │ │                                          │ │
│ ● 事件 (红色)    │ │ Connected to:                             │ │
│ ● 概念 (紫色)    │ │ • 缅北 (mentioned_in)                     │ │
│                  │ │ • 金三角 (related_to)                     │ │
│ 📊 统计          │ │ • 1962-1998 (active_during)               │ │
│ 节点: 15         │ │                                          │ │
│ 边: 46          │ │ [View Atoms →] [Ask AI about this]       │ │
│ 密度: 0.43      │ └─────────────────────────────────────────┘ │
│                  │                                              │
│ 🚀 操作          │ ┌─────────────────────────────────────────┐ │
│ [导出 PNG]       │ │ 💡 Ask AI:                               │ │
│ [导出 JSON]      │ │ • "彭家声和金三角的关系?"                  │ │
│ [Find Path]      │ │ • "这个时期的主要事件?"                    │ │
│ [Expand Node]    │ │ • "Show all related entities"            │ │
│                  │ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Graph功能特性**:
- ✅ 交互式力导向图（D3.js / React Flow）
- ✅ 节点筛选（按类型、重要度）
- ✅ 路径查找（两个实体间的连接）
- ✅ 节点展开（显示关联原子）
- ✅ AI集成（点击节点可直接提问）

---

### 4️⃣ Creative Studio 页面 - 💡 创作工具

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Dashboard / Creative Studio          Filter: [All] [TikTok]..│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 🎬 推荐片段 (1个)                               Sort: 适合度 ▼  │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 📹 Clip #1 - 金三角历史讲座开场                              ││
│ │                                                              ││
│ │ ┌────────────────────────────────────────┐                 ││
│ │ │ ▶ [00:00 - 01:23]                     │ 🔊 ━━●━━━━ 80%  ││
│ │ │                                        │                 ││
│ │ │ [Video Player Thumbnail]               │                 ││
│ │ └────────────────────────────────────────┘                 ││
│ │                                                              ││
│ │ 🎯 适合度评分: ⭐⭐⭐⭐☆ 0.82/1.00                           ││
│ │                                                              ││
│ │ 📊 评分细节:                                                  ││
│ │ ├─ 时长适合度: 92% (83秒，短视频最佳)                         ││
│ │ ├─ 内容完整性: 85% (有明确的开始和结尾)                       ││
│ │ ├─ 重要性: 78% (包含核心主题)                                ││
│ │ ├─ 复用价值: 70% (适合独立传播)                              ││
│ │ └─ 观点明确: 65% (有清晰的论点)                              ││
│ │                                                              ││
│ │ 🎬 推荐平台:                                                  ││
│ │ [TikTok ✓] [Instagram Reels ✓] [YouTube Shorts ✓]          ││
│ │                                                              ││
│ │ 💡 钩子建议:                                                  ││
│ │ "用《教父》的方式讲金三角历史？这个系列不一样！"               ││
│ │                                                              ││
│ │ ✏️ 标题建议 (4个):                                            ││
│ │ ┌──────────────────────────────────────────────────────────┐││
│ │ │ 1. [原生] 金三角历史讲座第一期：缅北双雄时代开讲           │││
│ │ │ 2. [提问] 为什么金三角被称为"小中国"？                     │││
│ │ │ 3. [数字] 一口气了解1962-1998年的缅北历史                  │││
│ │ │ 4. [冲突] 树挪死，人挪活？金三角的生存哲学                 │││
│ │ └──────────────────────────────────────────────────────────┘││
│ │                                                              ││
│ │ 🎯 目标受众:                                                  ││
│ │ • 历史爱好者 (35-50岁)                                        ││
│ │ • 地缘政治关注者                                             ││
│ │ • 教育学习者                                                 ││
│ │                                                              ││
│ │ #️⃣ SEO关键词:                                                ││
│ │ #金三角 #缅北历史 #彭家声 #历史讲座 #Myanmar #中缅关系        ││
│ │                                                              ││
│ │ 🚀 操作:                                                      ││
│ │ [下载片段] [复制标题] [生成脚本] [Ask AI: "更多建议?"]        ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ 💡 系列化建议                                                    │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 建议创建系列: "金三角历史系列"                                ││
│ │ • 第1集: 双雄时代背景介绍 (本片段)                           ││
│ │ • 第2集: 主要人物详解 (待提取)                               ││
│ │ • 第3集: 历史事件梳理 (待提取)                               ││
│ │                                                              ││
│ │ [生成完整系列方案 →]                                          ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Creative功能特性**:
- ✅ 片段适合度评分（加权算法）
- ✅ 多平台推荐（TikTok/Instagram/YouTube）
- ✅ 4种标题生成策略
- ✅ SEO关键词提取
- ✅ 系列化内容建议

---

### 5️⃣ Entities 页面 - 实体探索

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Dashboard / Entities                Type: [All] [Person]...   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 🔍 Search: [Search entities...]                  Sort: Count ▼ │
│                                                                 │
│ 📊 实体统计                                                      │
│ ┌──────┬──────┬──────┬──────┬──────┐                          │
│ │人物   │地点   │时间   │事件   │概念   │                          │
│ │  6   │  2   │  3   │  1   │  3   │                          │
│ └──────┴──────┴──────┴──────┴──────┘                          │
│                                                                 │
│ 👥 人物 (6)                                                      │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 彭家声                                                        ││
│ │ 提及: 8次 | 重要度: ⭐⭐⭐⭐⭐ 0.95                             ││
│ │ 出现时间: 00:15, 01:32, 02:45, ...                           ││
│ │ [View in Graph] [Ask AI] [Show Atoms]                       ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ 缅甸政府                                                      ││
│ │ 提及: 5次 | 重要度: ⭐⭐⭐⭐☆ 0.78                             ││
│ │ ...                                                          ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ 🌍 地点 (2)                                                      │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 金三角                                                        ││
│ │ 提及: 12次 | 重要度: ⭐⭐⭐⭐⭐ 1.00                            ││
│ │ ...                                                          ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ ⏰ 时间 (3)                                                      │
│ 📌 事件 (1)                                                      │
│ 💡 概念 (3)                                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 6️⃣ Timeline 页面 - 时间轴视图

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Dashboard / Timeline            View: [Atoms] [Segments] [All]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 🎬 Video Player                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ▶ [Video Preview]                                   🔊 ━━●━━ ││
│ │ 00:32 / 05:23                                               ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ 📊 Importance Timeline                                          │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ████      ███        ██       ████                           ││
│ │ 00:00    01:00      02:00    03:00      04:00      05:00    ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ 🔍 Filter: [High Importance] [Contains Entity: 彭家声]          │
│                                                                 │
│ ⏱️ 00:00 - 00:45 ⭐⭐⭐⭐⭐                                        │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 大家好我是马督公今天是2024年5月21号星期二欢迎收看第629期...  ││
│ │                                                              ││
│ │ 类型: 开场白 | 质量: 4.5/5                                    ││
│ │ 实体: [彭家声] [金三角] [缅北]                                ││
│ │ [Play] [View Detail] [Ask AI about this]                    ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ ⏱️ 00:45 - 01:23 ⭐⭐⭐⭐☆                                        │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 这个系列我会用《教父》三部曲的叙事方式...                     ││
│ │ ...                                                          ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 技术实现方案

### 前端技术栈

```typescript
核心框架:
- Next.js 14 (App Router)
- TypeScript 5+
- TailwindCSS 3
- Shadcn/ui

状态管理:
- Zustand (轻量级状态)
- React Query (服务端状态)

数据可视化:
- D3.js (知识图谱)
- Recharts (图表)
- React Flow (流程图备选)

实时通信:
- Server-Sent Events (SSE) - AI流式输出
- WebSocket (可选，未来多人协作)

其他库:
- Framer Motion (动画)
- React Markdown (渲染Markdown)
- date-fns (时间处理)
```

### 后端API设计

```python
# video_understanding_engine/api/server.py
from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse
from conversational import ConversationalInterface

app = FastAPI()

# 1. Chat API
@app.post("/api/chat/ask")
async def chat_ask(request: ChatRequest):
    """AI对话接口 (SSE流式)"""
    async def generate():
        response = interface.ask(
            request.query,
            session_id=request.session_id
        )
        # 流式返回
        yield f"data: {json.dumps(response.dict())}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

# 2. Data APIs
@app.get("/api/projects/{id}/atoms")
async def get_atoms(id: str):
    """获取原子列表"""
    return data_loader.get_atoms()

@app.get("/api/projects/{id}/entities")
async def get_entities(id: str):
    """获取实体列表"""
    return data_loader.get_entities()

@app.get("/api/projects/{id}/graph")
async def get_graph(id: str):
    """获取知识图谱"""
    return data_loader.get_graph()

@app.get("/api/projects/{id}/creative")
async def get_creative(id: str):
    """获取创作建议"""
    with open('data/output_pipeline_v3/creative_angles.json') as f:
        return json.load(f)

# 3. Session Management
@app.post("/api/sessions")
async def create_session(mode: str):
    """创建新会话"""
    return context_manager.create_session("default", mode)

@app.get("/api/sessions/{id}/history")
async def get_history(id: str):
    """获取会话历史"""
    return interface.get_session_history(id)
```

### 前端API调用示例

```typescript
// lib/api/chat.ts
export async function askAI(
  query: string,
  sessionId?: string,
  onChunk?: (chunk: string) => void
) {
  const response = await fetch('/api/chat/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, session_id: sessionId }),
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        onChunk?.(data.answer);
      }
    }
  }
}

// Usage in component
const [messages, setMessages] = useState<Message[]>([]);

const handleSend = async (query: string) => {
  const userMsg = { role: 'user', content: query };
  setMessages(prev => [...prev, userMsg]);

  let assistantMsg = { role: 'assistant', content: '' };
  setMessages(prev => [...prev, assistantMsg]);

  await askAI(query, sessionId, (chunk) => {
    assistantMsg.content += chunk;
    setMessages(prev => [...prev.slice(0, -1), assistantMsg]);
  });
};
```

---

## 📋 开发路线图

### Phase 1: 基础设施 (Week 1-2)

**目标**: 搭建API和基础组件

```
✅ 任务:
1. FastAPI后端服务
   - 基础路由结构
   - 数据加载中间件
   - CORS配置

2. Next.js前端结构
   - App Router设置
   - 基础布局组件
   - API客户端封装

3. 连接测试
   - 原子列表API
   - 实体列表API
   - 基础UI渲染
```

### Phase 2: AI Chat (Week 3-4) 🔥

**目标**: 实现核心AI对话功能

```
✅ 任务:
1. Chat Backend
   - SSE流式接口
   - Session管理
   - QueryUnderstanding集成

2. Chat Frontend
   - 消息列表组件
   - 流式渲染
   - 会话sidebar
   - Quick prompts

3. 功能优化
   - 来源引用跳转
   - 意图标识显示
   - Loading状态
```

### Phase 3: Knowledge Graph (Week 5-6) ⭐

**目标**: 实现交互式知识图谱

```
✅ 任务:
1. Graph Backend
   - 图数据API
   - 路径查找算法
   - 节点筛选

2. Graph Frontend
   - D3.js力导向图
   - 节点交互
   - 侧边栏详情
   - 筛选控制

3. AI集成
   - 点击节点提问
   - 路径解释
```

### Phase 4: Enhanced Dashboard (Week 7) 🔧

**目标**: 升级现有页面

```
✅ 任务:
1. 升级Atoms页面
   - 添加"Ask AI"按钮
   - 实体高亮
   - 跳转到Graph

2. 升级Dashboard
   - 实时统计卡片
   - 主题条形图
   - 快速操作

3. Timeline视图
   - 视频播放器集成
   - 重要度时间轴
   - 同步滚动
```

### Phase 5: Creative Studio (Week 8) 💡

**目标**: 创作工具界面

```
✅ 任务:
1. Clip推荐
   - 卡片式布局
   - 适合度展示
   - 标题建议

2. 视频预览
   - 内嵌播放器
   - 片段裁剪
   - 下载功能

3. 系列化建议
   - 内容规划
   - SEO优化
```

### Phase 6: Polish & Deploy (Week 9-10) ✨

**目标**: 优化和部署

```
✅ 任务:
1. 性能优化
   - 代码分割
   - 懒加载
   - 缓存策略

2. 移动端适配
   - 响应式布局
   - 触摸优化

3. 部署
   - Docker化
   - CI/CD
   - 监控日志
```

---

## 🎯 关键实现细节

### 1. SSE流式对话

```typescript
// components/chat/ChatWindow.tsx
const [isStreaming, setIsStreaming] = useState(false);

const handleSendMessage = async (query: string) => {
  setIsStreaming(true);

  const eventSource = new EventSource(
    `/api/chat/ask?query=${encodeURIComponent(query)}&session_id=${sessionId}`
  );

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'chunk') {
      // 逐字显示
      setCurrentMessage(prev => prev + data.content);
    } else if (data.type === 'complete') {
      // 完成，显示来源
      setSources(data.sources);
      setIsStreaming(false);
      eventSource.close();
    }
  };

  eventSource.onerror = () => {
    setIsStreaming(false);
    eventSource.close();
  };
};
```

### 2. 知识图谱渲染

```typescript
// components/graph/KnowledgeGraph.tsx
import * as d3 from 'd3';

const KnowledgeGraph = ({ data }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    const width = 800, height = 600;

    // 力导向图
    const simulation = d3.forceSimulation(data.nodes)
      .force('link', d3.forceLink(data.edges).id(d => d.id))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2));

    // 绘制边
    const link = svg.append('g')
      .selectAll('line')
      .data(data.edges)
      .enter().append('line')
      .attr('stroke', '#999')
      .attr('stroke-width', 2);

    // 绘制节点
    const node = svg.append('g')
      .selectAll('circle')
      .data(data.nodes)
      .enter().append('circle')
      .attr('r', d => d.importance * 10)
      .attr('fill', d => getColorByType(d.type))
      .call(drag(simulation))
      .on('click', (event, d) => {
        onNodeClick(d);
      });

    // 更新位置
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);
    });
  }, [data]);

  return <svg ref={svgRef} width="100%" height="100%" />;
};
```

### 3. 来源引用跳转

```typescript
// components/chat/SourceCard.tsx
const SourceCard = ({ source }) => {
  const router = useRouter();

  const handleJumpToTimeline = () => {
    // 跳转到Timeline并定位到该时间点
    router.push(
      `/projects/${projectId}/timeline?start=${source.start_time}`
    );
  };

  return (
    <div className="border rounded p-3">
      <div className="flex justify-between">
        <span className="font-medium">[{source.item_id}]</span>
        <span className="text-sm text-gray-500">
          {formatTime(source.start_time)} - {formatTime(source.end_time)}
        </span>
      </div>
      <p className="text-sm mt-2">{source.excerpt}</p>
      <div className="flex gap-2 mt-2">
        <Button size="sm" onClick={handleJumpToTimeline}>
          View in Timeline →
        </Button>
        <Button size="sm" variant="outline">
          Ask AI about this
        </Button>
      </div>
    </div>
  );
};
```

---

## 📊 预期效果对比

### 现在 vs 未来

| 功能 | 现有前端 | 新前端v2.0 |
|------|---------|-----------|
| **数据展示** | 仅原子和片段 | 原子+片段+实体+主题+图谱+报告 |
| **交互方式** | 点击浏览 | AI对话 + 点击浏览 + 图谱探索 |
| **查询能力** | 无 | 7种意图识别，8种检索策略 |
| **可视化** | 简单列表 | 知识图谱 + 时间轴 + 标签云 |
| **创作工具** | 无 | 片段推荐 + 标题生成 + SEO |
| **用户体验** | 基础 | 现代化、AI驱动、交互丰富 |

---

## 🚀 立即开始

### 第一步: 创建FastAPI后端

```bash
cd video_understanding_engine
mkdir api
touch api/server.py api/__init__.py
pip install fastapi uvicorn python-multipart
```

```python
# api/server.py - 最小可用版本
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/projects/test/atoms")
async def get_atoms():
    with open('data/output_pipeline_v3/atoms.jsonl') as f:
        atoms = [json.loads(line) for line in f]
    return {"atoms": atoms}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 第二步: 在Next.js中调用

```typescript
// atom-viewer/app/projects/[id]/atoms/page.tsx
// 修改现有文件
useEffect(() => {
  fetch('http://localhost:8000/api/projects/test/atoms')
    .then(res => res.json())
    .then(data => setAtoms(data.atoms))
    .catch(err => console.error(err));
}, []);
```

### 第三步: 测试

```bash
# Terminal 1: 启动FastAPI
cd video_understanding_engine
python api/server.py

# Terminal 2: 启动Next.js
cd atom-viewer
npm run dev

# 访问 http://localhost:3000
```

---

## 📝 总结

### 你将拥有

1. **AI驱动的对话界面** - 最核心的功能，让用户自然提问
2. **交互式知识图谱** - 独特卖点，可视化实体关系
3. **现代化仪表板** - 充分展示Phase 2的丰富数据
4. **创作辅助工具** - 实用的短视频推荐和标题生成
5. **完整的前后端架构** - 可扩展、可维护

### 下一步建议

**立即开始**: 按照上面的"立即开始"步骤，先连接后端API
**优先级**: AI Chat > Dashboard升级 > Knowledge Graph > Creative Studio
**时间估算**: 8-10周全部完成

---

**需要我帮你开始实现哪个部分？** 🚀
