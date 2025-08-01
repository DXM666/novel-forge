# NovelForge

NovelForge 是一款基于 React + Vite（Tailwind CSS）前端和 FastAPI 后端的人机协作小说写作平台，专为创作百万字长篇小说设计。核心理念是人机协作而非完全由AI代笔，通过AI激发灵感、提供结构、填充内容和优化语言，同时保留作者对创意、情感和深度的掌控。

## 项目结构
```
novel-forge/
├── frontend/                # 前端项目 (React + Vite + Tailwind)
│   ├── public/             # 静态资源与 HTML 模板
│   ├── src/                # 源码目录
│   ├── package.json        # 前端依赖及脚本
│   ├── vite.config.js      # Vite 配置
│   └── tailwind.config.js  # Tailwind CSS 配置
│
├── requirements/           # 需求文档
│   └── ...                # 各模块需求文档
│
└── backend/                 # 后端项目 (FastAPI)
    ├── app/                # Python 包代码
    │   ├── api/             # API 端点目录
    │   │   └── health.py      # 健康检查API
    │   ├── cache/           # 缓存系统
    │   │   ├── cache_factory.py  # 缓存工厂
    │   │   ├── memory_cache.py   # 内存缓存
    │   │   └── redis_cache.py    # Redis缓存
    │   ├── config.py       # 统一配置管理
    │   ├── database/        # 数据库及模型
    │   │   └── db_utils.py    # 数据库工具
    │   ├── memory.py       # 记忆存储管理
    │   ├── memory_system.py # 记忆系统业务逻辑
    │   ├── embeddings.py   # 统一嵌入向量管理
    │   ├── vector_store.py # 向量存储管理
    │   ├── vector_db_init.py # 向量数据库初始化
    │   ├── context_manager.py # 上下文管理
    │   ├── main.py         # FastAPI 应用入口
    │   ├── routes/          # API 路由模块
    │   │   ├── style.py        # 风格管理 API
    │   │   └── memory_api.py   # 记忆管理 API
    │   ├── utils/           # 工具类
    │   │   ├── logging_utils.py # 日志工具
    │   │   ├── error_handler.py # 错误处理
    │   │   ├── config_validator.py # 配置验证
    │   │   └── app_state.py    # 应用状态管理
    │   └── pipeline/       # AI 生成管道
    │       ├── workflow.py     # 主工作流程
    │       ├── parser.py       # 输入解析
    │       ├── generator.py    # 内容生成
    │       ├── consistency.py  # 一致性检查
    │       └── knowledge_graph.py # 知识图谱
    ├── migrations/         # 数据库迁移脚本
    │   ├── env.py          # 迁移环境配置
    │   └── versions/       # 版本迁移脚本
    ├── tests/              # 测试目录
    ├── alembic.ini         # Alembic 配置
    ├── manage_db.py        # 数据库管理脚本
    ├── pytest.ini         # Pytest 配置
    ├── requirements.txt    # Python 依赖列表
    └── .env.example        # 环境变量示例
```

## 快速开始

### 前端 (frontend)
1. 安装依赖：
   ```bash
   cd frontend
   pnpm install
   ```
2. 本地开发：
   ```bash
   pnpm dev
   ```
3. 打包部署：
   ```bash
   pnpm build
   ```

开发服务器默认运行于 `http://localhost:5173`

### 后端 (backend)

1. **安装依赖：**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **配置环境变量（重要！）：**
   
   为了保证安全性，所有敏感信息都通过环境变量管理：
   
   ```bash
   # 方法1：使用自动设置脚本（推荐）
   powershell -ExecutionPolicy Bypass -File scripts/setup_env.ps1
   
   # 方法2：手动复制配置模板
   cp .env.example .env
   # 然后编辑 .env 文件，填入真实的配置值
   ```
   
   **❗ 安全提示：**
   - `.env` 文件已在 `.gitignore` 中，不会被提交到 Git
   - 绝不要在代码中硬编码 API 密钥
   - 定期轮换 API 密钥和密码

3. **选择AI推理方式：**
   
   在 `.env` 文件中配置：
   
   - **使用 OpenAI API：**
     ```bash
     MODE=api
     OPENAI_API_KEY=sk-your-real-api-key-here
     OPENAI_MODEL=gpt-4
     ```
   
   - **使用本地模型（Ollama）：**
     ```bash
     MODE=local
     LOCAL_MODEL_NAME=qwen2.5:7b
     # OPENAI_API_KEY 可以留空
     ```
   
   **依赖说明：**
   - 本地推理需安装 [Ollama](https://ollama.com/)
   - pip 依赖已包含 langchain_ollama

4. **启动服务：**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   
5. **验证配置：**
   ```bash
   # 检查健康状态
   curl http://localhost:8000/health
   
   # 查看详细状态
   curl http://localhost:8000/health/status
   ```

API 文档自动生成：http://localhost:8000/docs

---

### AI推理切换机制说明
- 后端会根据 `OPENAI_API_KEY` 是否存在自动决定调用云端API还是本地模型。
- 可通过 `.env` 文件或环境变量灵活切换。
- 本地推理默认模型为 `qwen2.5:7b`，如需更换请修改 `backend/app/ai.py`。

## 核心功能

### 前端功能
- **富文本编辑器**：基于 Slate.js/ProseMirror，支持章节树状导航、角色/场景标签系统
- **大纲管理**：三层大纲生成（故事骨架、章节脉络、场景卡片）
- **世界观资料库**：侧边栏提供角色、地点、物品等元素的管理
- **多视图模式**：支持时间线视图、大纲视图和编辑视图的切换

### 后端 AI 引擎

#### 1. 上下文管理
- **递归摘要**：使用动态摘要技术压缩历史内容，扩展上下文窗口
- **分块生成**：将小说分成小块（章节/场景）单独生成，避免上下文漂移

#### 2. 风格控制
- **风格嵌入**：将风格向量注入生成过程，确保文风一致性
- **风格微调**：支持用户上传样本文本，基于样本微调风格迁移模型

#### 3. 并行推理
- **分布式计算**：使用并行处理技术同时生成多个章节或场景
- **多模型实例**：支持部署多个模型实例分担不同生成任务

#### 4. 一致性维护
- **知识图谱**：构建动态更新的角色/世界观数据库，确保设定一致
- **实时校验**：在生成过程中持续检查角色行为和情节发展是否一致

#### 5. 后处理优化
- **文本润色**：优化语法、句式和表达
- **风格迁移**：应用特定作家或流派的风格
- **多样性增强**：避免重复句式和表达
- **情感曲线分析**：分析并可视化文本情感变化

## 技术实现

### 前端技术栈
- **框架**：React + Vite
- **样式**：Tailwind CSS
- **状态管理**：React Context/Redux
- **编辑器**：定制的富文本编辑器

### 后端技术栈
- **框架**：FastAPI
- **数据库**：PostgreSQL（集成pg_vector向量扩展）
- **缓存**：Redis 分布式缓存和内存缓存适配器
- **数据迁移**：Alembic 实现版本化数据库管理
- **向量引擎**：固有PostgreSQL pg_vector和外部Pinecone/Weaviate/Chroma
- **AI 模型**：OpenAI API / 本地大语言模型
- **并行处理**：ThreadPoolExecutor（可扩展为Ray分布式）
- **知识图谱**：自定义实体-关系模型
- **状态管理**：集中化应用状态和健康检查
- **配置管理**：统一配置模块与验证机制

## 部署建议
- **前端**：静态托管平台（Netlify / Vercel / GitHub Pages）
- **后端**：容器或云服务（Docker / AWS ECS / Heroku）
- **AI 模型**：根据需求选择云API或自托管模型
- **扩展性**：支持水平扩展以处理更多并发请求

## 功能实现状态

### ✅ 已实现功能

#### 前端界面
- ✅ **基础UI框架**：React + Vite + Tailwind CSS
- ✅ **富文本编辑器**：支持基本文本编辑和格式化
- ✅ **三栏布局**：左侧元素管理、中央编辑区、右侧风格控制
- ✅ **元素管理系统**：角色、地点、物品的添加、编辑和管理
- ✅ **大纲管理面板**：支持章节结构化管理
- ✅ **知识图谱可视化**：基础的关系图展示
- ✅ **错误边界处理**：防止页面崩溃的错误捕获
- ✅ **元素插入功能**：通过@角色、#地点、*物品格式快速插入
- ✅ **内容高亮显示**：自动识别和高亮文本中的元素引用
- ✅ **撤销/重做功能**：编辑历史管理

#### 后端核心架构
- ✅ **FastAPI应用框架**：完整的API服务架构
- ✅ **统一配置管理**：集中化的配置系统和验证
- ✅ **数据库集成**：PostgreSQL + pg_vector向量扩展
- ✅ **缓存系统**：Redis分布式缓存和内存缓存适配器
- ✅ **数据库迁移**：Alembic版本化数据库管理
- ✅ **统一日志系统**：结构化日志记录和管理
- ✅ **错误处理机制**：全局异常处理和错误分类
- ✅ **应用状态管理**：健康检查和组件状态监控
- ✅ **向量存储系统**：支持多种向量数据库后端
- ✅ **嵌入向量管理**：统一的文本嵌入生成和存储

#### AI推理引擎
- ✅ **多模型支持**：OpenAI API和本地模型集成
- ✅ **记忆系统**：短期和长期记忆管理
- ✅ **上下文管理**：递归摘要和动态上下文构建
- ✅ **知识图谱**：实体关系管理和一致性检查框架
- ✅ **风格管理**：风格样本上传和微调框架
- ✅ **并行推理**：多线程并行文本生成

#### API接口
- ✅ **文本生成API**：基础的AI文本生成接口
- ✅ **记忆管理API**：记忆存储和检索接口
- ✅ **小说元素API**：角色、地点、物品管理接口
- ✅ **大纲生成API**：结构化大纲生成
- ✅ **章节生成API**：章节内容生成和优化
- ✅ **健康检查API**：系统状态监控接口

### 🚧 部分实现功能

#### 前端功能
- 🚧 **AI辅助功能集成**：前端已有UI按钮，但与后端AI接口集成不完整
- 🚧 **实时预览**：基础功能已实现，需要优化性能
- 🚧 **多项目管理**：UI框架已准备，后端支持需要完善
- 🚧 **导出功能**：基础导出逻辑存在，需要支持更多格式

#### AI功能
- 🚧 **一致性检查**：框架已建立，检查逻辑需要完善
- 🚧 **风格迁移**：基础架构存在，模型微调功能需要优化
- 🚧 **情感分析**：接口已定义，分析算法需要实现
- 🚧 **智能续写**：基本功能可用，上下文理解需要增强

#### 数据处理
- 🚧 **向量检索优化**：基础功能已实现，性能优化进行中
- 🚧 **批量处理**：框架已建立，并发控制需要完善

### ❌ 待实现功能

#### 高级AI功能
- ❌ **深度学习风格模型**：当前使用模拟实现，需要真实模型训练
- ❌ **高级NLP分析**：命名实体识别、情感分析等需要集成专业模型
- ❌ **智能大纲生成**：当前为基础模板，需要AI驱动的智能生成
- ❌ **多模态支持**：图片、音频等多媒体内容支持

#### 用户体验
- ❌ **用户认证系统**：用户注册、登录、权限管理
- ❌ **协作功能**：多用户协同编辑
- ❌ **版本控制**：文档版本管理和比较
- ❌ **云端同步**：跨设备数据同步

#### 性能优化
- ❌ **分布式计算**：Ray框架集成用于大规模并行处理
- ❌ **模型优化**：模型量化、缓存优化
- ❌ **CDN集成**：静态资源加速

#### 部署运维
- ❌ **容器化部署**：Docker和Kubernetes配置
- ❌ **监控告警**：完整的监控和告警系统
- ❌ **自动化CI/CD**：持续集成和部署流水线
- ❌ **负载均衡**：高可用性部署架构

### 📋 开发优先级

#### 高优先级（近期目标）
1. **完善前后端集成**：确保所有AI功能在前端可用
2. **优化AI生成质量**：改进提示工程和模型参数
3. **增强一致性检查**：完善角色和情节一致性验证
4. **用户认证系统**：实现基础的用户管理功能

#### 中优先级（中期目标）
1. **性能优化**：提升大文档处理性能
2. **高级AI功能**：集成更强大的NLP模型
3. **协作功能**：支持多用户协同编辑
4. **移动端适配**：响应式设计优化

#### 低优先级（长期目标）
1. **分布式架构**：支持大规模用户和内容
2. **多模态支持**：图文混合创作
3. **商业化功能**：付费订阅、高级功能
4. **生态系统**：插件系统、第三方集成

---

**这是一个正在开发中的项目，旨在为小说创作者提供AI辅助的创作工具。**

如有疑问或需求，欢迎提交 issue！
