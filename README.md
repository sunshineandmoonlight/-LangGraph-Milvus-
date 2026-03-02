# Enterprise Multi-Agent System

> 基于 LangGraph 和 Milvus 的企业级 AI 多智能体协作系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.x-brightgreen.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 项目简介

一个功能完整的企业级 AI 多智能体系统，采用 **Supervisor-Worker 架构**，实现了智能体协作、知识库检索（RAG）和网络搜索等功能。系统支持三种对话模式，可根据场景灵活切换。

### 核心亮点

- 🤖 **多智能体协作** - Supervisor 协调 Research 和 Worker 智能体完成任务
- 📚 **智能知识库** - 支持 Milvus 向量检索，企业文档一键上传
- 🌐 **联网搜索** - 集成 Tavily API，获取最新实时信息
- 🔐 **完整认证** - JWT 用户认证、会话管理、权限控制
- 💬 **三种模式** - Agent 模式 / RAG 模式 / 普通对话模式
- 🎨 **现代界面** - Vue 3 + Element Plus，响应式设计

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

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         用户界面 (Vue 3)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  聊天界面    │  │  知识库管理  │  │    会话历史        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI 后端                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Agent     │  │  Knowledge  │  │     Auth           │  │
│  │    API      │  │     API     │  │     API           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      LangGraph 工作流                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Supervisor Agent                     │  │
│  │         (LLM 驱动的任务协调与决策)                     │  │
│  └────────────┬────────────────────┬─────────────────────┘  │
│               │                    │                         │
│      ▼──────────────────────▼    ▼───────────────────────│
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  Research Agent  │  │   Writer Agent   │  │  完成/响应    │  │
│  │                  │  │                  │  │              │  │
│  │ • Milvus 搜索    │  │ • 综合研究结果   │  │              │  │
│  │ • Tavily 网搜    │  │ • 生成结构化报告 │  │              │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  PostgreSQL │  │   Milvus    │  │   Tavily API       │  │
│  │  (用户/会话) │  │  (向量数据库) │  │   (网络搜索)       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 三种对话模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **Agent 模式** | 完整的多智能体协作，自动调用工具搜索信息 | 复杂研究、深度分析 |
| **RAG 模式** | 仅从知识库检索回答 | 企业文档查询、FAQ |
| **Normal 模式** | 普通对话，不使用工具 | 闲聊、简单问答 |

---

## 🛠️ 技术栈

### 后端
- **Python 3.10+**
- **FastAPI** - 高性能异步 Web 框架
- **LangGraph** - 多智能体状态机编排
- **LangChain** - LLM 应用开发框架
- **Milvus 2.3** - 开源向量数据库
- **PostgreSQL 15** - 关系型数据库
- **SiliconFlow / GLM** - LLM 服务（国内友好）
- **Qwen3-Embedding-4B** - 文本向量化（2560维）

### 前端
- **Vue 3** - 渐进式前端框架
- **Element Plus** - Vue 3 组件库
- **Pinia** - 状态管理
- **Axios** - HTTP 客户端
- **Vite** - 快速构建工具
- **Markdown-it** - Markdown 渲染

---

## 🚀 快速开始

### 方式一：Docker 一键启动（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/Enterprise-MultiAgent-System.git
cd Enterprise-MultiAgent-System

# 2. 配置环境变量
cp .env.example .env
nano .env  # 填写 API Keys

# 3. 启动所有服务
docker-compose up -d

# 4. 等待服务启动（Milvus 需要 30-60 秒）
docker-compose logs -f
```

访问应用：
- 前端界面：http://localhost:3000
- API 文档：http://localhost:8000/docs

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

## 📸 功能展示

### 1. 多智能体协作

用户提问后，Supervisor 智能分析任务并自动调度：

```
用户: "分析人工智能在医疗领域的最新进展"
  │
  ▼
Supervisor: "需要研究，调用 Research Agent"
  │
  ▼
Research Agent: [调用 Milvus 搜索] [调用 Tavily 网搜]
  │
  ▼
Writer Agent: 综合研究结果，生成结构化报告
```

### 2. 知识库管理

支持多种文档格式上传：

- 文本文件：`.txt`, `.md`, `.json`
- Office 文档：`.doc`, `.docx`
- PDF 文档：`.pdf`

上传后自动提取文本并生成向量索引。

### 3. 三种模式切换

| 模式 | 特点 |
|------|------|
| 🤖 Agent | 完整的多智能体协作，自动搜索和综合信息 |
| 📚 RAG | 仅从已上传的知识库中检索回答 |
| 💬 Normal | 普通 LLM 对话，不使用额外工具 |

---

## 📂 项目结构

```
Enterprise-MultiAgent-System/
├── app/                          # 后端应用
│   ├── api/                      # API 路由
│   │   ├── agent.py             # Agent 执行接口
│   │   ├── auth.py              # 认证接口
│   │   ├── chat.py              # 聊天接口
│   │   ├── knowledge.py         # 知识库接口
│   │   └── session.py           # 会话接口
│   ├── graph/                    # LangGraph 配置
│   │   ├── agents.py            # Agent 定义
│   │   ├── graph.py             # 工作流图
│   │   ├── state.py             # 状态定义
│   │   └── tools.py             # 工具定义
│   ├── core/                     # 核心模块
│   │   └── security.py          # JWT 认证
│   ├── models/                   # 数据模型
│   │   ├── user.py              # 用户模型
│   │   └── session.py           # 会话模型
│   ├── schemas/                  # Pydantic 模式
│   ├── services/                 # 业务服务
│   │   ├── embedding_service.py # Embedding 服务
│   │   └── milvus_service.py    # Milvus 服务
│   ├── config.py                 # 配置管理
│   └── main.py                   # FastAPI 主应用
│
├── frontend/                     # 前端应用
│   ├── src/
│   │   ├── api/                  # API 客户端
│   │   ├── components/           # Vue 组件
│   │   │   ├── ChatWindow.vue    # 聊天窗口
│   │   │   ├── Sidebar.vue       # 侧边栏
│   │   │   ├── ThoughtProcess.vue # 思考过程
│   │   │   └── SourcesPanel.vue  # 来源面板
│   │   ├── views/                # 页面视图
│   │   │   ├── ChatView.vue      # 聊天页面
│   │   │   ├── KnowledgeView.vue # 知识库页面
│   │   │   ├── AgentsView.vue    # Agent 页面
│   │   │   └── LoginView.vue     # 登录页面
│   │   ├── store/                # Pinia 状态
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
├── .env.example                  # 环境变量模板
├── DEPLOYMENT.md                 # 部署指南
├── README.md                     # 项目文档
└── CLAUDE.md                     # Claude Code 指南
```

---

## 🔧 环境配置

复制 `.env.example` 为 `.env` 并配置以下必要参数：

```env
# 数据库
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=enterprise_agent

# LLM API (二选一)
SILICONFLOW_API_KEY=your_siliconflow_key    # 推荐
GLM_API_KEY=your_glm_key                    # 备选

# 网络搜索
TAVILY_API_KEY=your_tavily_key

# JWT 密钥
JWT_SECRET_KEY=your-secret-key-min-32-chars
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
```

详细测试说明请查看 [tests/README.md](tests/README.md)

---

## 📦 部署到云服务器

详细的部署指南请查看 [DEPLOYMENT.md](DEPLOYMENT.md)

简要步骤：

```bash
# 1. 上传项目到服务器
scp -r Enterprise-MultiAgent-System root@your-server:/root/

# 2. 配置环境变量
cp .env.example .env
nano .env

# 3. 启动服务
docker-compose up -d

# 4. 配置 Nginx 反向代理（可选）
sudo apt install nginx certbot python3-certbot-nginx -y
```

---

## 🤝 参与贡献

欢迎贡献代码、报告 Bug 或提出新功能建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📝 更新日志

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

A: 调整 `app/api/agent.py` 中的 `SIMILARITY_THRESHOLD` 相似度阈值

---

## 📄 开源协议

本项目采用 [MIT](LICENSE) 协议

---

## 🙏 致谢

本项目使用了以下优秀的开源项目：

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [Milvus](https://github.com/milvus-io/milvus)
- [FastAPI](https://github.com/tiangolo/fastapi)
- [Vue 3](https://github.com/vuejs/core)
- [Element Plus](https://github.com/element-plus/element-plus)

---

## 📮 联系方式

- 项目主页：[Enterprise-MultiAgent-System](https://github.com/yourusername/Enterprise-MultiAgent-System)
- 问题反馈：[Issues](https://github.com/yourusername/Enterprise-MultiAgent-System/issues)
