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
└── backend/                 # 后端项目 (FastAPI)
    ├── app/                # Python 包代码
    │   ├── config.py       # 环境及配置管理
    │   ├── memory.py       # 记忆存储模块 (内存/可扩展 Redis)
    │   ├── ai.py           # AI 推理逻辑 (OpenAI / 本地模型)
    │   ├── context_manager.py # 上下文管理（递归摘要）
    │   ├── main.py         # FastAPI 接口定义
    │   ├── routers/        # API 路由模块
    │   │   └── style.py    # 风格管理 API
    │   └── pipeline/       # AI 生成管道
    │       ├── workflow.py     # 主工作流程协调
    │       ├── parser.py       # 输入解析（意图识别、大纲生成）
    │       ├── generator.py    # 内容生成（段落、对话、场景）
    │       ├── consistency.py  # 一致性检查
    │       ├── postprocessing.py # 后处理（润色、风格迁移）
    │       ├── knowledge_graph.py # 知识图谱（角色/世界观）
    │       ├── style_tuner.py  # 风格微调
    │       └── parallel_inference.py # 并行推理
    ├── examples/           # 示例脚本
    │   └── generate_chapter.py # 章节生成示例
    ├── data/               # 数据存储目录
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
1. 安装依赖：
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. 选择推理模型方式（通过环境变量配置）：
   - **使用 OpenAI API 调用云端模型：**
     ```bash
     export OPENAI_API_KEY=your_openai_key
     export OPENAI_MODEL=gpt-3.5-turbo
     # 不设置 LOCAL_MODEL_PATH
     ```
     只要 OPENAI_API_KEY 存在，系统自动走 OpenAI API。
   - **使用本地模型（Ollama + langchain）：**
     ```bash
     export LOCAL_MODEL_PATH=/path/to/model # 路径可选，仅供自定义
     unset OPENAI_API_KEY  # 或不设置
     ```
     此时将自动调用本地Ollama模型（默认qwen2.5:7b，可在代码中调整）。
   - **依赖说明：**
     - 本地推理需安装并配置好 Ollama（详见 https://ollama.com/）
     - pip 依赖已包含 langchain_ollama

3. 启动服务：
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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
- **AI 模型**：OpenAI API / 本地大语言模型
- **并行处理**：ThreadPoolExecutor（可扩展为Ray分布式）
- **知识图谱**：自定义实体-关系模型
- **数据存储**：文件系统/可扩展为数据库

## 部署建议
- **前端**：静态托管平台（Netlify / Vercel / GitHub Pages）
- **后端**：容器或云服务（Docker / AWS ECS / Heroku）
- **AI 模型**：根据需求选择云API或自托管模型
- **扩展性**：支持水平扩展以处理更多并发请求

---

如有疑问或需求，欢迎提交 issue！
