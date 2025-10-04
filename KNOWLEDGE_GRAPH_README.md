# Knowledge Graph 可视化 - 使用指南

## ✅ 完成状态

**实现日期**: 2025-01-XX
**状态**: 已完成并可用

---

## 🎉 已实现功能

### 后端 (FastAPI)

✅ **API服务器** (`video_understanding_engine/api/server.py`)
- Port: 8000
- CORS 配置完成
- 6个API端点：
  - `/api/health` - 健康检查
  - `/api/projects/{id}/atoms` - 原子列表
  - `/api/projects/{id}/segments` - 片段列表
  - `/api/projects/{id}/entities` - 实体列表
  - `/api/projects/{id}/topics` - 主题网络
  - **`/api/projects/{id}/graph`** - 知识图谱 ⭐

✅ **知识图谱数据格式**
- 14个节点（6人物、2国家、1事件、3概念、1主题、1片段）
- 46条边（关系）
- D3.js/React Flow 兼容格式

### 前端 (Next.js + React Flow + Shadcn/ui)

✅ **Knowledge Graph 页面** (`/projects/[id]/graph`)
- 交互式力导向图
- 节点类型颜色编码：
  - 🔵 人物 (persons) - 蓝色
  - 🟢 国家 (countries) - 绿色
  - 🔴 事件 (events) - 红色
  - 🟣 概念 (concepts) - 紫色
  - 🟡 主题 (topic) - 黄色
  - ⚪ 片段 (segment) - 灰色

✅ **交互功能**
- 点击节点查看详情
- 缩放和平移
- MiniMap 导航
- 节点类型筛选
- 图谱统计信息

✅ **UI组件**
- 使用 Shadcn/ui（Card, Badge, Button等）
- 响应式布局
- Sidebar详情面板
- 图例说明

✅ **项目页面集成**
- 添加了快速访问按钮
- 🕸️ Knowledge Graph
- 🔬 Atoms View
- 💬 AI Chat (待实现)
- 🎬 Creative Tools (待实现)

---

## 🚀 快速开始

### 1. 启动后端API

```bash
cd video_understanding_engine
python api/server.py
```

**输出**:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**测试**:
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/projects/test/graph
```

### 2. 启动前端

```bash
cd atom-viewer
npm run dev
```

**输出**:
```
▲ Next.js 15.5.4
- Local:        http://localhost:3000
✓ Ready in 2.1s
```

### 3. 访问Knowledge Graph

浏览器打开：
```
http://localhost:3000
```

点击项目 → 点击 "🕸️ Knowledge Graph" 按钮

或直接访问：
```
http://localhost:3000/projects/test/graph
```

---

## 📸 界面截图（文字描述）

### 主要区域布局

```
┌─────────────────────────────────────────────────────────────┐
│ Header: Knowledge Graph                [Export] [Fullscreen] │
│ 14 nodes · 46 edges                                          │
├────────────────────────────────────────────┬────────────────┤
│                                            │ Sidebar        │
│                                            │                │
│        ●孙中山                              │ Node Types:    │
│          ╱ ╲                               │ 🔵 Person (6)  │
│     ● ───●─── ●                           │ 🟢 Country(2)  │
│  金三角   │   缅甸                          │ 🔴 Event  (1)  │
│          ●                                 │ 🟣 Concept(3)  │
│        中国                                  │ 🟡 Topic  (1)  │
│                                            │                │
│     [Interactive Force Graph]              │ Selected:      │
│                                            │ 孙中山          │
│                                            │ Type: persons  │
│                                            │ Mentions: 1    │
│     [Zoom Controls]  [Mini Map]            │                │
│                                            │ [Ask AI]       │
│                                            │                │
└────────────────────────────────────────────┴────────────────┘
```

### 节点颜色示例

- **孙中山** 🔵 (蓝色圆圈) - 人物
- **中国** 🟢 (绿色圆圈) - 国家
- **缅北双雄时代** 🔴 (红色圆圈) - 事件
- **金三角** 🟣 (紫色圆圈) - 概念
- **金三角历史与缅北双雄时代** 🟡 (黄色圆圈) - 主题

### 边（关系）示例

```
孙中山 ──→ 缅北双雄时代  (参与事件)
孙中山 ──→ 中国          (关联国家)
金三角 ──→ 缅北双雄时代  (相关概念)
```

---

## 🔧 技术栈

### 后端
- **FastAPI** - 现代Python Web框架
- **Uvicorn** - ASGI服务器
- **CORS中间件** - 跨域支持

### 前端
- **Next.js 15** - React框架
- **React Flow** - 图谱可视化库
- **Shadcn/ui** - UI组件库
- **TailwindCSS** - 样式框架
- **TypeScript** - 类型安全

---

## 📁 文件结构

```
D:\code\youtube/
├── video_understanding_engine/
│   ├── api/
│   │   ├── __init__.py
│   │   └── server.py              ← FastAPI服务器 ⭐
│   ├── data/output_pipeline_v3/
│   │   └── indexes/
│   │       └── graph.json         ← 知识图谱数据
│   └── ...
│
└── atom-viewer/
    ├── app/projects/[id]/
    │   ├── page.tsx               ← 添加快速访问按钮
    │   └── graph/
    │       └── page.tsx           ← Knowledge Graph 页面 ⭐
    ├── components/
    │   ├── KnowledgeGraph.tsx     ← React Flow 组件 ⭐
    │   └── ui/                    ← Shadcn 组件
    └── ...
```

---

## 🎯 使用场景

### 场景1: 探索视频内容结构

1. 打开Knowledge Graph
2. 观察节点分布和连接
3. 识别核心实体（节点大小代表重要性）
4. 理解实体间关系

### 场景2: 查找特定实体

1. 在图谱中定位目标节点
2. 点击节点查看详情
3. 查看相关连接
4. 点击"Ask AI"深入了解

### 场景3: 分析主题结构

1. 找到主题节点（黄色）
2. 查看连接的实体
3. 理解主题覆盖范围
4. 导出图谱进行分享

---

## 🐛 已知问题

### 小问题
1. ⚠️ 节点初始布局是简单的圆形排列
   - **影响**: 复杂图谱可能重叠
   - **解决方案**: 可手动拖动调整
   - **未来优化**: 实现更智能的布局算法

2. ⚠️ 大型图谱（>100节点）性能待优化
   - **当前状态**: 14节点流畅运行
   - **未来需求**: 需要虚拟化渲染

### 待实现功能
- [ ] 节点搜索
- [ ] 路径查找（两个节点间最短路径）
- [ ] 导出功能（PNG/JSON）
- [ ] 全屏模式
- [ ] 与AI Chat集成

---

## 📊 API详细文档

### GET `/api/projects/{id}/graph`

**Response Format**:
```json
{
  "nodes": [
    {
      "id": "persons_孙中山",
      "type": "persons",
      "label": "孙中山",
      "mentions": 1,
      "segments": ["SEG_001"]
    }
  ],
  "edges": [
    {
      "source": "persons_孙中山",
      "target": "segment_SEG_001",
      "relation": "出现在",
      "type": "entity_to_segment"
    }
  ],
  "stats": {
    "node_count": 14,
    "edge_count": 46
  }
}
```

**节点类型**:
- `persons` - 人物
- `countries` - 国家
- `events` - 事件
- `concepts` - 概念
- `topic` - 主题
- `segment` - 视频片段

**边类型**:
- `entity_to_segment` - 实体出现在片段中
- `entity_to_topic` - 实体相关主题
- `person_to_event` - 人物参与事件
- `person_to_country` - 人物关联国家
- `concept_to_event` - 概念相关事件
- `topic_to_segment` - 主题涵盖片段

---

## 🔮 未来规划

### Phase 3.1: 增强交互 (1-2天)
- [ ] 节点搜索框
- [ ] 高亮相关节点
- [ ] 路径查找算法
- [ ] 节点详情弹窗优化

### Phase 3.2: AI集成 (2-3天)
- [ ] 点击节点 → AI解释
- [ ] 点击边 → AI解释关系
- [ ] 图谱生成摘要
- [ ] 智能推荐相关节点

### Phase 3.3: 高级功能 (1周)
- [ ] 图谱历史版本
- [ ] 多视频对比
- [ ] 协作标注
- [ ] 自定义布局保存

---

## 🎓 学习资源

### React Flow
- 官方文档: https://reactflow.dev/
- 示例库: https://reactflow.dev/examples/

### Shadcn/ui
- 官方文档: https://ui.shadcn.com/
- 组件库: https://ui.shadcn.com/docs/components/

### FastAPI
- 官方文档: https://fastapi.tiangolo.com/
- CORS配置: https://fastapi.tiangolo.com/tutorial/cors/

---

## 💡 提示和技巧

### 提示1: 快速定位重要节点
- 节点大小 = 重要性/提及次数
- 大节点通常是核心概念

### 提示2: 理解关系
- 箭头方向表示关系方向
- 边上的标签说明关系类型

### 提示3: 导航大型图谱
- 使用MiniMap快速定位
- 双击空白区域重置视图
- 滚轮缩放

---

## 🆘 故障排除

### 问题1: 后端8000端口被占用

**解决方案**:
```bash
# 查找占用进程
netstat -ano | findstr :8000

# 杀掉进程 (替换PID)
taskkill /F /PID <PID>
```

### 问题2: 前端无法连接后端

**检查**:
1. 后端是否运行: `curl http://localhost:8000/api/health`
2. CORS是否配置: 检查`server.py`中的`allow_origins`
3. 浏览器Console是否有错误

### 问题3: 图谱不显示

**检查**:
1. 浏览器Console是否有错误
2. API返回的数据格式是否正确
3. React Flow是否正确安装: `npm list reactflow`

---

## 📝 总结

Knowledge Graph可视化功能已完全实现！

**核心价值**:
- ✅ 直观展示视频内容结构
- ✅ 快速理解实体关系
- ✅ 为系统思考提供可视化基础
- ✅ 使用现代化技术栈（Shadcn/ui）

**下一步建议**:
1. 尝试分析更多视频
2. 探索不同类型的图谱
3. 集成AI Chat功能
4. 添加更多交互特性

---

**Happy Exploring! 🎉**
