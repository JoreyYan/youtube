# 多视频项目架构设计文档
## Multi-Video Project Architecture Design Document

---

### 📋 文档概述

本文档详细设计了如何从当前的"一个视频一个项目"架构转换为"一个项目多个视频"架构，支持跨视频数据合并、实体关联和统一剪辑处理。

**现状**: 每个视频独立处理，生成独立的原子(Atom)、实体(Entity)、向量(Vector)等数据
**目标**: 项目内多个视频的数据能够智能合并，支持跨视频实体识别、关系发现和统一编辑

---

## 🏗️ 第一部分：当前架构分析

### 1.1 现有数据结构

#### 原子(Atom)数据模型
```json
{
  "atom_id": "A001",                    // 当前格式：A + 数字
  "start_ms": 7000,
  "end_ms": 26000,
  "duration_ms": 19000,
  "merged_text": "视频内容文本",
  "type": "闲聊/叙述历史/回应弹幕",
  "completeness": "完整/需要上下文",
  "source_utterance_ids": [1,2,3],
  "topics": null,                       // 后续填充
  "emotion": null,
  "value": null,
  "embedding": null                     // 语义向量
}
```

#### 当前处理流程
```
SRT字幕文件 → 原子化 → 实体提取 → 向量化 → 知识图谱 → 前端展示
     ↓           ↓         ↓         ↓         ↓         ↓
  解析字幕    切分片段   NER识别   嵌入模型   关系构建   可视化
```

#### 现有文件结构
```
video_understanding_engine/
├── data/output/
│   ├── atoms_full.jsonl          # 所有原子
│   ├── frontend_data.json        # 前端数据（实体+图谱）
│   └── segments/                 # 分段数据
├── models/atom.py                # 原子数据模型
└── pipeline/video_processor_v3.py # 处理管道
```

### 1.2 当前架构的限制

1. **ID冲突**: 多个视频都有A001、A002等ID
2. **实体孤立**: 同一人物在不同视频中被当作不同实体
3. **向量空间分离**: 每个视频的向量独立存储，无法跨视频搜索
4. **关系断裂**: 跨视频的实体关系无法建立
5. **编辑困难**: 无法基于跨视频内容进行统一剪辑

---

## 🎯 第二部分：多视频项目架构设计

### 2.1 新数据模型设计

#### 项目层级结构
```
Project (项目)
├── ProjectMeta (项目元数据)
├── Video_1 (视频1)
│   ├── VideoMeta (视频元数据)
│   ├── Atoms: v1_A001, v1_A002... (原子)
│   ├── LocalEntities (局部实体)
│   └── Embeddings (局部向量)
├── Video_2 (视频2)
│   ├── VideoMeta
│   ├── Atoms: v2_A001, v2_A002...
│   ├── LocalEntities
│   └── Embeddings
└── MergedData (合并数据)
    ├── GlobalEntities (全局实体)
    ├── CrossVideoRelations (跨视频关系)
    ├── UnifiedVectorSpace (统一向量空间)
    └── ProjectKnowledgeGraph (项目知识图谱)
```

#### 新原子ID策略
```python
# 当前: A001, A002, A003...
# 新设计: {video_id}_A{number}

class ProjectAtom(BaseModel):
    atom_id: str = Field(..., description="格式: v{timestamp}_A{number}")
    video_id: str = Field(..., description="所属视频ID")
    project_id: str = Field(..., description="所属项目ID")

    # 保持原有字段
    start_ms: int
    end_ms: int
    merged_text: str
    # ... 其他字段保持不变

    # 新增跨视频字段
    global_entity_refs: List[str] = Field(default=[], description="引用的全局实体ID")
    cross_video_references: List[str] = Field(default=[], description="跨视频引用")
```

### 2.2 实体合并策略

#### 三层实体识别体系
```python
class EntityMergingStrategy:
    """实体合并策略"""

    def merge_entities(self, all_videos: List[VideoData]) -> Dict[str, GlobalEntity]:
        """
        三层合并策略：
        1. 精确匹配 (Exact Match)
        2. 模糊匹配 (Fuzzy Match)
        3. 语义匹配 (Semantic Match)
        """

        # Layer 1: 精确字符串匹配
        exact_groups = self._exact_match_grouping(all_videos)

        # Layer 2: 编辑距离 + 拼音相似度
        fuzzy_groups = self._fuzzy_match_grouping(exact_groups)

        # Layer 3: 向量语义相似度
        semantic_groups = self._semantic_match_grouping(fuzzy_groups)

        return self._create_global_entities(semantic_groups)
```

#### 实体合并规则
| 匹配类型 | 规则 | 置信度阈值 | 示例 |
|---------|------|-----------|------|
| 精确匹配 | 完全相同 | 1.0 | "罗星汉" = "罗星汉" |
| 模糊匹配 | 编辑距离≤2 | >0.85 | "罗星汉" ≈ "罗兴汉" |
| 语义匹配 | 向量余弦>0.9 | >0.9 | "习近平" ≈ "习主席" |

### 2.3 向量空间统一策略

#### 分层向量存储
```python
class MultiVideoVectorStore:
    """多视频向量存储管理"""

    def __init__(self, project_id: str):
        self.project_id = project_id
        # 三层向量空间
        self.local_stores = {}      # video_id -> QdrantStore (局部)
        self.global_store = None    # 全局统一空间
        self.merged_store = None    # 合并后空间

    def add_video_vectors(self, video_id: str, atoms: List[Atom]):
        """添加单个视频的向量"""
        # 1. 存储到局部空间（保持独立性）
        local_store = QdrantVectorStore(f"{self.project_id}_{video_id}")
        local_store.add_vectors(atoms)
        self.local_stores[video_id] = local_store

        # 2. 同时加入全局空间（支持跨视频搜索）
        if not self.global_store:
            self.global_store = QdrantVectorStore(f"{self.project_id}_global")

        # 使用新的atom_id格式避免冲突
        global_atoms = [self._convert_to_global_format(atom, video_id) for atom in atoms]
        self.global_store.add_vectors(global_atoms)

    def cross_video_search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """跨视频语义搜索"""
        return self.global_store.search(query, top_k)
```

---

## 🔧 第三部分：实现方案

### 3.1 数据迁移策略

#### Phase 1: 兼容性改造
```python
def upgrade_existing_data(project_path: str):
    """现有数据升级到新格式"""

    # 1. 读取现有原子数据
    atoms = load_jsonl(f"{project_path}/atoms_full.jsonl")

    # 2. 生成video_id (基于文件路径或时间戳)
    video_id = f"v{int(time.time())}"

    # 3. 更新atom_id格式
    upgraded_atoms = []
    for atom in atoms:
        atom['atom_id'] = f"{video_id}_{atom['atom_id']}"
        atom['video_id'] = video_id
        atom['project_id'] = extract_project_id(project_path)
        upgraded_atoms.append(atom)

    # 4. 保存到新结构
    save_video_data(project_path, video_id, upgraded_atoms)
```

#### Phase 2: 新项目结构
```
projects/
├── {project_id}/
│   ├── project.json              # 项目元数据
│   ├── videos/
│   │   ├── {video_id}.json      # 单个视频数据
│   │   └── {video_id}.jsonl     # 原子数据
│   ├── merged/
│   │   ├── entities.json        # 合并实体
│   │   ├── relationships.json   # 跨视频关系
│   │   └── knowledge_graph.json # 统一知识图谱
│   └── vectors/
│       ├── local_{video_id}/    # 局部向量
│       └── global/              # 全局向量
```

### 3.2 核心类实现

#### 项目管理器
```python
class MultiVideoProjectManager:
    """多视频项目管理器"""

    def __init__(self, project_id: str, base_path: str = "projects"):
        self.project_id = project_id
        self.project_path = Path(base_path) / project_id
        self._init_project_structure()

    def add_video(self, srt_file: str, video_name: str = None) -> str:
        """添加新视频到项目"""

        # 1. 生成唯一video_id
        video_id = self._generate_video_id()

        # 2. 独立处理视频（使用现有pipeline）
        processor = VideoProcessor()
        video_data = processor.process_video(srt_file, video_id, self.project_id)

        # 3. 保存视频数据
        self._save_video_data(video_id, video_data)

        # 4. 触发项目级数据合并
        self._trigger_project_merge()

        return video_id

    def _trigger_project_merge(self):
        """触发项目级数据合并"""
        merger = ProjectDataMerger(self.project_id, self.project_path)
        merger.merge_all_videos()
```

#### 数据合并器
```python
class ProjectDataMerger:
    """项目数据合并器"""

    def merge_all_videos(self):
        """合并所有视频数据"""

        # 1. 加载所有视频数据
        all_videos = self._load_all_videos()

        # 2. 实体合并
        global_entities = self._merge_entities(all_videos)

        # 3. 关系发现
        cross_relationships = self._find_cross_relationships(all_videos, global_entities)

        # 4. 向量空间合并
        self._merge_vector_spaces(all_videos)

        # 5. 生成统一知识图谱
        unified_graph = self._build_unified_knowledge_graph(global_entities, cross_relationships)

        # 6. 保存合并结果
        self._save_merged_data(global_entities, cross_relationships, unified_graph)
```

### 3.3 API接口设计

#### RESTful API 扩展
```python
# 新增API端点

@app.post("/api/projects")
async def create_project(project_data: ProjectCreate):
    """创建新项目"""
    pass

@app.post("/api/projects/{project_id}/videos")
async def add_video_to_project(project_id: str, video_file: UploadFile):
    """向项目添加视频"""
    pass

@app.get("/api/projects/{project_id}")
async def get_project_summary(project_id: str):
    """获取项目摘要"""
    pass

@app.get("/api/projects/{project_id}/entities")
async def get_merged_entities(project_id: str):
    """获取合并后的实体"""
    pass

@app.get("/api/projects/{project_id}/graph")
async def get_unified_graph(project_id: str):
    """获取统一知识图谱"""
    pass

@app.post("/api/projects/{project_id}/search")
async def cross_video_search(project_id: str, query: SearchQuery):
    """跨视频语义搜索"""
    pass
```

---

## 🎥 第四部分：前端适配

### 4.1 UI/UX 改进

#### 项目视图重新设计
```typescript
// 新的项目数据结构
interface Project {
  project_id: string
  name: string
  description: string
  created_at: string
  videos: Video[]
  stats: ProjectStats
}

interface Video {
  video_id: string
  name: string
  filename: string
  duration: number
  atom_count: number
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
}

interface ProjectStats {
  total_videos: number
  total_atoms: number
  unique_entities: number
  cross_video_relationships: number
}
```

#### 知识图谱增强
```typescript
// 支持视频筛选的图谱组件
interface EnhancedGraphProps {
  project_id: string
  video_filters: string[]        // 选择显示哪些视频的数据
  show_cross_video_edges: boolean // 是否显示跨视频边
  layout: 'video-separated' | 'unified' // 布局模式
}

// 节点数据扩展
interface GraphNode {
  id: string
  label: string
  type: string
  video_sources: string[]        // 出现在哪些视频中
  cross_video: boolean          // 是否跨视频实体
  merged_confidence: number     // 合并置信度
}
```

### 4.2 新功能组件

#### 视频选择器
```tsx
const VideoSelector = ({ project }: { project: Project }) => {
  const [selectedVideos, setSelectedVideos] = useState<string[]>([])

  return (
    <Card>
      <CardHeader>
        <CardTitle>视频筛选</CardTitle>
      </CardHeader>
      <CardContent>
        {project.videos.map(video => (
          <div key={video.video_id} className="flex items-center space-x-2">
            <Checkbox
              checked={selectedVideos.includes(video.video_id)}
              onCheckedChange={(checked) => {/* 处理选择 */}}
            />
            <span>{video.name}</span>
            <Badge>{video.atom_count} atoms</Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
```

#### 跨视频搜索
```tsx
const CrossVideoSearch = ({ projectId }: { projectId: string }) => {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])

  const handleSearch = async () => {
    const response = await fetch(`/api/projects/${projectId}/search`, {
      method: 'POST',
      body: JSON.stringify({ query, top_k: 20 })
    })
    const data = await response.json()
    setResults(data.results)
  }

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <Input
          placeholder="跨视频语义搜索..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button onClick={handleSearch}>搜索</Button>
      </div>

      <div className="space-y-2">
        {results.map(result => (
          <Card key={result.atom_id}>
            <CardContent className="p-3">
              <div className="flex justify-between items-start mb-2">
                <Badge variant="outline">{result.atom_id}</Badge>
                <Badge>{result.video_name}</Badge>
              </div>
              <p className="text-sm text-gray-600">
                {result.text.substring(0, 100)}...
              </p>
              <div className="mt-2 text-xs text-gray-500">
                相似度: {(result.similarity * 100).toFixed(1)}%
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
```

---

## 🚀 第五部分：实施计划

### 5.1 迁移路线图

#### 阶段1: 基础架构改造 (第1-2周)
- [ ] 创建新的数据模型类
- [ ] 实现ProjectManager核心类
- [ ] 升级现有数据到新格式
- [ ] 基本的多视频支持

#### 阶段2: 数据合并逻辑 (第3-4周)
- [ ] 实体合并算法实现
- [ ] 向量空间统一
- [ ] 跨视频关系发现
- [ ] 合并数据存储

#### 阶段3: API和前端适配 (第5-6周)
- [ ] 扩展API接口
- [ ] 前端项目视图重新设计
- [ ] 知识图谱多视频支持
- [ ] 跨视频搜索功能

#### 阶段4: 优化和测试 (第7-8周)
- [ ] 性能优化
- [ ] 大规模测试
- [ ] 用户体验优化
- [ ] 文档和部署

### 5.2 关键决策点

#### 数据存储策略
```python
# 选择1: 完全分离存储（推荐）
projects/{project_id}/
├── videos/{video_id}.json     # 原始视频数据
└── merged/global_data.json    # 合并后数据

# 选择2: 混合存储
projects/{project_id}/
└── unified_data.json          # 所有数据在一个文件

# 推荐选择1，因为：
# - 支持增量更新
# - 便于调试和维护
# - 支持并行处理
```

#### 实体合并阈值调优
```python
ENTITY_MERGE_THRESHOLDS = {
    'exact_match': 1.0,           # 精确匹配
    'fuzzy_similarity': 0.85,     # 模糊匹配阈值
    'semantic_similarity': 0.9,   # 语义相似度阈值
    'min_confidence': 0.8,        # 最小合并置信度
}

# 这些阈值需要根据实际数据调优
```

### 5.3 测试策略

#### 数据质量验证
```python
class DataQualityValidator:
    """数据质量验证器"""

    def validate_entity_merging(self, global_entities: Dict):
        """验证实体合并质量"""

        issues = []

        # 检查过度合并（不同实体被错误合并）
        for entity_id, entity in global_entities.items():
            if entity.confidence < 0.8:
                issues.append(f"低置信度合并: {entity.name}")

        # 检查合并不足（同一实体被分散）
        similar_pairs = self._find_similar_entities(global_entities)
        for pair in similar_pairs:
            if pair.similarity > 0.9:
                issues.append(f"可能的遗漏合并: {pair.name1} vs {pair.name2}")

        return issues
```

#### 性能基准测试
```python
# 测试场景
test_scenarios = [
    {"videos": 2, "atoms_per_video": 100, "entities": 20},
    {"videos": 5, "atoms_per_video": 300, "entities": 50},
    {"videos": 10, "atoms_per_video": 500, "entities": 100},
]

# 性能指标
performance_metrics = [
    'entity_merging_time',      # 实体合并耗时
    'vector_indexing_time',     # 向量索引耗时
    'search_response_time',     # 搜索响应时间
    'memory_usage',            # 内存使用
    'storage_size',            # 存储空间
]
```

---

## 📚 第六部分：开发指南

### 6.1 开发环境设置

```bash
# 1. 克隆现有代码
git clone <repository>
cd video_understanding_engine

# 2. 创建多视频分支
git checkout -b feature/multi-video-support

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建项目目录
mkdir -p projects/test_project

# 5. 运行测试
python -m pytest tests/test_multi_video.py
```

### 6.2 代码规范

#### 命名约定
```python
# 项目ID: project_20241201_001
# 视频ID: v{timestamp}
# 原子ID: {video_id}_A{number}
# 实体ID: e_{uuid_8chars}
# 关系ID: r_{uuid_8chars}

# 示例
project_id = "project_20241201_001"
video_id = "v1733019600"
atom_id = "v1733019600_A001"
entity_id = "e_a1b2c3d4"
relation_id = "r_x1y2z3w4"
```

#### 错误处理
```python
class MultiVideoError(Exception):
    """多视频处理异常基类"""
    pass

class EntityMergingError(MultiVideoError):
    """实体合并异常"""
    pass

class VectorSpaceError(MultiVideoError):
    """向量空间异常"""
    pass

# 使用示例
try:
    merger.merge_entities(videos)
except EntityMergingError as e:
    logger.error(f"实体合并失败: {e}")
    # 回滚或重试逻辑
```

### 6.3 调试和监控

#### 日志配置
```python
import logging

# 为多视频功能配置专门的日志
multi_video_logger = logging.getLogger('multi_video')
multi_video_logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('logs/multi_video.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
multi_video_logger.addHandler(handler)

# 关键事件日志
multi_video_logger.info(f"开始处理项目 {project_id}")
multi_video_logger.info(f"添加视频 {video_id} 到项目")
multi_video_logger.info(f"实体合并完成，发现 {len(global_entities)} 个全局实体")
```

#### 监控指标
```python
class ProjectMetrics:
    """项目监控指标"""

    def collect_metrics(self, project_id: str):
        return {
            'video_count': self.count_videos(project_id),
            'atom_count': self.count_atoms(project_id),
            'entity_count': self.count_entities(project_id),
            'merge_quality_score': self.calculate_merge_quality(project_id),
            'processing_time': self.get_processing_time(project_id),
            'storage_size_mb': self.get_storage_size(project_id),
        }
```

---

## 🔍 第七部分：常见问题解答

### Q1: 如何处理大量视频的性能问题？
**A**: 采用分层处理策略：
- **增量合并**: 只处理新增视频，不重新处理全部
- **懒加载**: 按需加载视频数据，不一次性加载所有
- **缓存机制**: 缓存合并结果，避免重复计算
- **并行处理**: 利用多进程并行处理不同视频

### Q2: 实体合并错误如何处理？
**A**: 多层次质量保证：
- **人工审核**: 提供合并结果审核界面
- **置信度阈值**: 低置信度合并需要人工确认
- **回滚机制**: 支持撤销错误合并
- **版本控制**: 保存合并历史，支持回退

### Q3: 现有数据如何平滑迁移？
**A**: 渐进式迁移策略：
- **兼容模式**: 新系统同时支持新旧数据格式
- **批量转换**: 提供数据格式转换工具
- **备份机制**: 迁移前自动备份原始数据
- **验证工具**: 迁移后数据完整性验证

### Q4: 跨视频搜索性能如何保证？
**A**: 优化向量搜索：
- **分层索引**: 局部+全局双重索引
- **预计算**: 常用查询预计算结果
- **索引优化**: 使用近似最近邻(ANN)算法
- **结果缓存**: 缓存热门搜索结果

---

## 📋 第八部分：实施清单

### 开发任务清单

#### 后端开发 (Python)
- [ ] `models/project.py` - 项目数据模型
- [ ] `models/multi_video_atom.py` - 多视频原子模型
- [ ] `managers/project_manager.py` - 项目管理器
- [ ] `mergers/entity_merger.py` - 实体合并器
- [ ] `mergers/vector_merger.py` - 向量合并器
- [ ] `api/project_endpoints.py` - 项目API端点
- [ ] `utils/data_migration.py` - 数据迁移工具

#### 前端开发 (TypeScript/React)
- [ ] `types/project.ts` - 项目类型定义
- [ ] `pages/projects/[id].tsx` - 项目详情页
- [ ] `components/VideoSelector.tsx` - 视频选择器
- [ ] `components/CrossVideoSearch.tsx` - 跨视频搜索
- [ ] `components/UnifiedKnowledgeGraph.tsx` - 统一知识图谱
- [ ] `hooks/useProject.ts` - 项目数据钩子

#### 测试文件
- [ ] `tests/test_project_manager.py` - 项目管理测试
- [ ] `tests/test_entity_merging.py` - 实体合并测试
- [ ] `tests/test_vector_merging.py` - 向量合并测试
- [ ] `tests/test_data_migration.py` - 数据迁移测试

#### 文档和配置
- [ ] `docs/API.md` - API文档更新
- [ ] `docs/DEPLOYMENT.md` - 部署指南
- [ ] `config/multi_video.yaml` - 多视频配置
- [ ] `scripts/migrate_data.py` - 迁移脚本

---

## 🎯 总结

本架构设计提供了从单视频到多视频项目的完整迁移方案：

### 核心优势
1. **平滑迁移**: 兼容现有数据，渐进式升级
2. **智能合并**: 三层实体合并策略，高准确率
3. **统一搜索**: 跨视频语义搜索，打破视频边界
4. **可扩展性**: 支持大量视频，性能优化
5. **用户友好**: 直观的多视频项目管理界面

### 技术亮点
- **ID防冲突**: 视频前缀确保原子ID唯一性
- **分层存储**: 局部+全局向量空间设计
- **增量处理**: 支持动态添加视频
- **质量保证**: 多重验证确保合并准确性

### 实施建议
1. **优先级**: 先实现核心数据模型，再扩展前端功能
2. **测试驱动**: 每个模块都要有充分的单元测试
3. **迭代开发**: 分阶段发布，收集用户反馈
4. **性能监控**: 建立完善的性能监控体系

这个设计方案为项目从单视频扩展到多视频提供了完整的技术路径，任何开发者都可以根据这个文档进行实施。

---

**文档版本**: v1.0
**创建时间**: 2024年12月
**更新时间**: 2024年12月
**作者**: AI Architect
**审核**: 待审核