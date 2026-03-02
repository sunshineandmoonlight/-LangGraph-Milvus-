# Enterprise Multi-Agent System

> 基于 LangGraph 和 Milvus 的企业级 AI 多智能体协作系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.x-brightgreen.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌐 在线演示

**服务器地址：** http://106.53.173.173:3000

> 使用测试账号快速体验：点击"测试模式快速体验"按钮即可（多智能体模型因模型原因加载有些久）


---

## 📖 项目简介

这是一个功能完整的企业级 **AI 多智能体协作系统**，采用 **Supervisor-Worker 架构**，实现了智能体协作、知识库检索（RAG）和网络搜索等功能。系统支持三种对话模式，可根据场景灵活切换。

### 核心亮点

- 🤖 **多智能体协作** - Supervisor 协调 Research 和 Writer 智能体完成任务
- 📚 **智能知识库** - 支持 Milvus 向量检索，企业文档一键上传
- 🌐 **联网搜索** - 集成 Tavily API，获取最新实时信息
- 🔐 **完整认证** - JWT 用户认证、会话管理、权限控制
- 💬 **三种模式** - Agent 模式 / RAG 模式 / 普通对话模式
- 🎨 **现代界面** - Vue 3 + Element Plus，响应式设计

---

## 🏗️ 系统架构

### 整体架构图

### 整体架构图

![系统架构图](docs/1-系统架构图.drawio.png)

[![查看原图](https://img.shields.io/badge/编辑-draw.io-blue)](https://app.diagrams.net/?U=https://github.com/sunshineandmoonlight/-LangGraph-Milvus-/raw/main/docs/architecture-diagram.drawio)

### 三种对话模式

| 模式 | 说明 | 适用场景 | 相似度阈值 |
|------|------|----------|-----------|
| **Agent 模式** | 完整的多智能体协作，自动调用工具搜索信息 | 复杂研究、深度分析 | - |
| **RAG 模式** | 仅从知识库检索回答，低于 35% 直接返回无结果 | 企业文档查询、FAQ | 35% |
| **Normal 模式** | 普通对话，不使用工具 | 闲聊、简单问答 | - |

---

## 🤖 使用的 AI 模型

### 大语言模型 (LLM)

| 模型 | 提供商 | 用途 | 维度 |
|------|--------|------|------|
| **Qwen2.5-7B-Instruct** | SiliconFlow | 主要对话模型（Agent/Normal 模式） | - |
| **glm-4-flash** | 智谱 AI | 备用对话模型 | - |

### 嵌入模型 (Embedding)

| 模型 | 提供商 | 用途 | 向量维度 |
|------|--------|------|---------|
| **Qwen3-Embedding-4B** | SiliconFlow | 文本向量化、语义搜索 | 2560 维 |

### 模型配置

```python
# LLM 配置 (app/config.py)
SILICONFLOW_CHAT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
SILICONFLOW_API_BASE = "https://api.siliconflow.cn/v1"
SILICONFLOW_TEMPERATURE = 0.7

# Embedding 配置
EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-4B"
EMBEDDING_DIMENSION = 2560
```

---

## 🛠️ 调用的工具

### 1. Milvus 向量搜索工具

**功能：** 从企业知识库中检索相关文档

```python
# app/graph/tools.py
class MilvusSearchTool(BaseTool):
    name = "milvus_search"
    description = "从企业知识库向量数据库中搜索相关文档"

    def _run(self, query: str, top_k: int = 5) -> str:
        # 1. 生成查询向量
        query_vector = get_embedding(query)

        # 2. Milvus 相似度搜索
        results = milvus_service.search(query_vector, top_k)

        # 3. 返回最相关的文档内容
        return format_results(results)
```

**参数：**
- `query`: 搜索查询文本
- `top_k`: 返回结果数量（默认 5）

**返回：** 按相似度排序的文档列表，包含相似度分数

### 2. Tavily 网络搜索工具

**功能：** 搜索互联网获取最新信息

```python
class TavilySearchTool(BaseTool):
    name = "tavily_search"
    description = "搜索互联网获取最新信息和实时数据"

    def _run(self, query: str, max_results: int = 5) -> str:
        # 调用 Tavily API
        results = tavily_client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced"
        )
        return format_search_results(results)
```

**参数：**
- `query`: 搜索关键词
- `max_results`: 最大结果数（默认 5）

**返回：** 搜索结果列表，包含标题、URL、摘要

### 工具调用流程

```
用户提问
    │
    ▼
Supervisor Agent 分析问题
    │
    ├─ 需要企业文档？ ──→ Milvus 搜索工具
    │
    ├─ 需要最新信息？ ──→ Tavily 搜索工具
    │
    ▼
Research Agent 综合结果
    │
    ▼
Writer Agent 生成最终回答
```

---

## 📊 数据流程

### RAG 模式数据流

![RAG 模式数据流](docs/1-RAG 模式数据流.drawio.png)

**流程说明：**
1. 用户提问 → Qwen3-Embedding-4B 向量化 (2560维)
2. Milvus 向量搜索 (HNSW 索引，IP 距离)
3. 相似度判断 (阈值 35%)
   - **低于阈值** → 直接返回无结果
   - **高于阈值** → LLM 生成回答

### Agent 模式数据流

![Agent 模式数据流](docs/1-Agent 模式数据流.drawio.png)

**流程说明：**
1. 用户提问 → Supervisor Agent (Qwen2.5-7B-Instruct) 分析
2. 根据需要调用：
   - Milvus 搜索 (知识库)
   - Tavily 搜索 (互联网)
3. Research Agent 收集整合信息
4. Writer Agent 生成结构化报告
5. 返回最终答案 + 来源

---

## 🛠️ 技术栈

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.10+ | 主要开发语言 |
| **FastAPI** | Latest | 高性能异步 Web 框架 |
| **LangGraph** | 0.2+ | 多智能体状态机编排 |
| **LangChain** | 0.3+ | LLM 应用开发框架 |
| **Milvus** | 2.3.4 | 开源向量数据库 |
| **PostgreSQL** | 15 | 关系型数据库（用户/会话） |
| **SQLAlchemy** | 2.0+ | ORM 框架 |
| **Pydantic** | 2.7+ | 数据验证 |
| **PyJWT** | - | JWT 认证 |
| **bcrypt** | - | 密码加密 |

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **Vue** | 3.4+ | 渐进式前端框架 |
| **Element Plus** | Latest | Vue 3 UI 组件库 |
| **Pinia** | Latest | 状态管理 |
| **Vue Router** | 4.x | 路由管理 |
| **Axios** | Latest | HTTP 客户端 |
| **Vite** | 5.x | 快速构建工具 |
| **Markdown-it** | Latest | Markdown 渲染 |
| **Tailwind CSS** | 3.x | 原子化 CSS |

---

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| **多智能体协作** | Supervisor 协调 Research 和 Writer 智能体，自动拆解任务 |
| **知识库管理** | 支持 .txt/.md/.json/.doc/.docx/.pdf 文件上传，自动向量化 |
| **语义搜索** | 基于向量相似度的智能检索，快速定位相关内容 |
| **联网搜索** | 集成 Tavily 搜索 API，获取最新网络信息 |
| **会话管理** | 完整的对话历史保存，支持多会话切换 |
| **用户认证** | 注册登录、JWT 认证、演示模式快速体验 |
| **流式输出** | 实时展示 AI 思考过程和工具调用状态 |
| **源码追踪** | 显示回答来源，支持可追溯性 |

---

## 📂 项目结构

```
Enterprise-MultiAgent-System/
├── app/                          # 后端应用
│   ├── api/                      # API 路由
│   │   ├── agent.py             # Agent 执行接口 (RAG 阈值 35%)
│   │   ├── auth.py              # 认证接口 (登录/注册/demo)
│   │   ├── knowledge.py         # 知识库接口 (上传/搜索/统计)
│   │   └── session.py           # 会话接口 (历史管理)
│   ├── graph/                    # LangGraph 配置
│   │   ├── agents.py            # Agent 定义 (Supervisor/Research/Writer)
│   │   ├── graph.py             # 工作流图 (状态机)
│   │   ├── state.py             # 状态定义 (AgentState)
│   │   └── tools.py             # 工具定义 (Milvus/Tavily)
│   ├── core/                     # 核心模块
│   │   └── security.py          # JWT 认证 (bcrypt rounds=4)
│   ├── models/                   # 数据模型
│   │   ├── user.py              # 用户模型 (User)
│   │   └── session.py           # 会话模型 (ChatSession)
│   ├── schemas/                  # Pydantic 模式
│   │   ├── user.py              # 用户相关 Schema
│   │   └── session.py           # 会话相关 Schema
│   ├── services/                 # 业务服务
│   │   ├── embedding_service.py # Embedding 服务 (Qwen3-Embedding-4B)
│   │   └── milvus_service.py    # Milvus 服务 (HNSW 索引)
│   ├── config.py                 # 配置管理 (环境变量)
│   ├── database.py               # 数据库连接
│   └── main.py                   # FastAPI 主应用
│
├── frontend/                     # 前端应用
│   ├── src/
│   │   ├── api/                  # API 客户端
│   │   │   └── index.js         # Axios 封装 + 拦截器
│   │   ├── components/           # Vue 组件
│   │   │   ├── ChatWindow.vue   # 聊天窗口 (消息展示)
│   │   │   ├── Sidebar.vue      # 侧边栏 (知识库上传/统计)
│   │   │   ├── ThoughtProcess.vue # 思考过程展示
│   │   │   └── SourcesPanel.vue # 来源面板
│   │   ├── views/                # 页面视图
│   │   │   ├── ChatView.vue     # 聊天页面
│   │   │   ├── KnowledgeView.vue # 知识库页面
│   │   │   ├── AgentsView.vue   # Agent 页面
│   │   │   └── LoginView.vue    # 登录页面
│   │   ├── store/                # Pinia 状态
│   │   │   ├── chat.js          # 聊天状态
│   │   │   └── user.js          # 用户状态
│   │   └── router/               # 路由配置
│   ├── Dockerfile                # 前端 Docker 配置
│   └── package.json
│
├── tests/                        # 测试代码
│   ├── conftest.py               # Pytest 配置
│   ├── test_unit.py              # 单元测试
│   ├── test_auth.py              # 认证测试
│   ├── test_knowledge.py         # 知识库测试
│   ├── test_agent.py             # Agent 测试
│   └── test_e2e.py               # 端到端测试
│
├── docker-compose.yml            # Docker 编排
├── Dockerfile                    # 后端 Docker 镜像
├── requirements.txt              # Python 依赖
├── init_db.py                    # 数据库初始化脚本
├── .env.example                  # 环境变量模板
├── DEPLOYMENT.md                 # 部署指南
├── README.md                     # 项目文档
└── CLAUDE.md                     # Claude Code 指南
```

---

## 🚀 快速开始

### 方式一：Docker 一键启动（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/sunshineandmoonlight/-LangGraph-Milvus-.git
cd -LangGraph-Milvus-

# 2. 配置环境变量
cp .env.example .env
nano .env  # 填写 API Keys

# 3. 启动所有服务
docker-compose up -d

# 4. 初始化数据库
docker exec -it enterprise_backend python init_db.py

# 5. 等待服务启动（Milvus 需要 30-60 秒）
docker-compose logs -f backend
```

访问应用：
- **前端界面：** http://localhost:3000
- **API 文档：** http://localhost:8000/docs

### 方式二：本地开发

```bash
# 后端
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

---

## 🔧 环境配置

复制 `.env.example` 为 `.env` 并配置以下必要参数：

```env
# ========== 数据库配置 ==========
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=enterprise_agent
DATABASE_URL=postgresql+asyncpg://postgres:your_secure_password@postgres:5432/enterprise_agent

# ========== Milvus 向量数据库 ==========
MILVUS_HOST=milvus-standalone
MILVUS_PORT=19530

# ========== LLM 配置 ==========
# SiliconFlow (推荐 - 免费，限制少)
USE_SILICONFLOW=true
SILICONFLOW_API_KEY=your_siliconflow_key
SILICONFLOW_CHAT_MODEL=Qwen/Qwen2.5-7B-Instruct
SILICONFLOW_API_BASE=https://api.siliconflow.cn/v1
SILICONFLOW_TEMPERATURE=0.7

# GLM (备选)
GLM_API_KEY=your_glm_key

# ========== Embedding 配置 ==========
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-4B
EMBEDDING_API_BASE=https://api.siliconflow.cn/v1
EMBEDDING_DIMENSION=2560

# ========== 网络搜索 ==========
TAVILY_API_KEY=your_tavily_key

# ========== JWT 认证 ==========
SECRET_KEY=your-secret-key-change-this-in-production-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

### API Key 获取

| 服务 | 获取地址 |
|------|----------|
| **SiliconFlow** | https://cloud.siliconflow.cn/account/ak |
| **智谱 GLM** | https://open.bigmodel.cn/usercenter/apikeys |
| **Tavily** | https://tavily.com |

---

## 📦 部署到云服务器

详细的部署指南请查看 [DEPLOYMENT.md](DEPLOYMENT.md)

简要步骤：

```bash
# 1. 上传项目到服务器
scp -r Enterprise-MultiAgent-System ubuntu@your-server:/home/ubuntu/

# 2. 配置环境变量
cp .env.example .env
nano .env

# 3. 启动服务
docker-compose up -d

# 4. 初始化数据库
docker exec -it enterprise_backend python init_db.py

# 5. 配置防火墙（开放端口）
sudo ufw allow 3000/tcp  # 前端
sudo ufw allow 8000/tcp  # 后端 API
```

---

## 🧪 运行测试

```bash
# 安装测试依赖
pip install -r requirements-test.txt

# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

---

## 📝 更新日志

### v1.1.0 (2025-03)
- ✅ 修复前端硬编码 localhost URL 问题
- ✅ 修复注册响应解析错误
- ✅ RAG 相似度阈值从 0.3 提升到 0.35
- ✅ 低于阈值时直接返回提示，不再调用 LLM
- ✅ 添加数据库初始化脚本 `init_db.py`
- ✅ 添加 `psycopg2-binary` 和 `email-validator` 依赖

### v1.0.0 (2024-03)
- ✅ 多智能体协作系统
- ✅ Milvus 向量数据库集成
- ✅ 三种对话模式
- ✅ JWT 用户认证
- ✅ 知识库管理
- ✅ 完整的测试套件

---

## ❓ 常见问题

**Q: Milvus 启动失败？**

A: Milvus 启动需要 30-60 秒，请耐心等待。检查容器状态：`docker-compose ps`

**Q: 如何更换 LLM 模型？**

A: 编辑 `.env` 文件中的 `SILICONFLOW_CHAT_MODEL` 或 `GLM_CHAT_MODEL` 配置

**Q: 知识库搜索结果不准确？**

A: 调整 `app/api/agent.py` 中的 `SIMILARITY_THRESHOLD` 相似度阈值（当前 0.35）




## 🤝 参与贡献

欢迎贡献代码、报告 Bug 或提出新功能建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 开源协议

本项目采用 [MIT](LICENSE) 协议

---

## 🙏 致谢

本项目使用了以下优秀的开源项目：

- [LangGraph](https://github.com/langchain-ai/langgraph) - 多智能体编排框架
- [Milvus](https://github.com/milvus-io/milvus) - 开源向量数据库
- [FastAPI](https://github.com/tiangolo/fastapi) - 现代化 Python Web 框架
- [Vue 3](https://github.com/vuejs/core) - 渐进式前端框架
- [Element Plus](https://github.com/element-plus/element-plus) - Vue 3 组件库
- [SiliconFlow](https://siliconflow.cn) - 国产 AI 模型服务

---

## 📮 联系方式

- **项目主页：** https://github.com/sunshineandmoonlight/-LangGraph-Milvus-
- **在线演示：** http://106.53.173.173:3000
- **问题反馈：** [Issues](https://github.com/sunshineandmoonlight/-LangGraph-Milvus-/issues)
