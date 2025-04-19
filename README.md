# NovelForge

NovelForge 是一款基于 React + Vite（Tailwind CSS）前端 和 FastAPI 后端 的人机协作小说写作平台，提供章节管理、富文本编辑及 AI 辅助生成功能。

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
    │   ├── ai.py           # AI 推理逻辑 (OpenAI / 本地模型占位)
    │   └── main.py         # FastAPI 接口定义
    ├── requirements.txt    # Python 依赖列表
    └── README.md           # 后端启动说明
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
2. 设置环境变量（可选）：
   ```bash
   export OPENAI_API_KEY=your_openai_key
   export OPENAI_MODEL=gpt-3.5-turbo
   export LOCAL_MODEL_PATH=/path/to/model
   ```
3. 启动服务：
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

API 文档自动生成：http://localhost:8000/docs

## 核心功能

- **章节与场景管理**：可在前端侧边栏添加/编辑角色、场景、章节结构
- **富文本编辑**：主编辑区支持 Markdown 与富文本格式
- **AI 辅助写作**：通过 `/generate` 接口获取基于上下文的续写建议
- **记忆存储**：调用 `/memory` 接口可保存/读取历史上下文

## 部署建议
- 前端可部署至静态托管平台（Netlify / Vercel / GitHub Pages）
- 后端可部署至容器或云服务（Docker / AWS ECS / Heroku）

---

如有疑问或需求，欢迎提交 issue！
