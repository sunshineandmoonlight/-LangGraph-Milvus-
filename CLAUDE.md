# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an enterprise multi-agent collaboration system built with LangGraph and Milvus. The system uses a Supervisor-Worker architecture where a Supervisor agent coordinates Research and Writer agents to automate complex research and report generation tasks.

## Architecture

### Multi-Agent System
The system implements LangGraph's StateGraph pattern:

- **Supervisor Agent** (`app/graph/agents.py`): LLM-powered coordinator that decides which worker agent to invoke next based on conversation state
- **Research Agent** (`app/graph/agents.py`): Uses tools (Milvus vector search, Tavily web search) to gather information
- **Writer Agent** (`app/graph/agents.py`): Synthesizes research into comprehensive reports

### State Management
The workflow state (`app/graph/state.py`) maintains:
- Messages between agents
- Current agent status (next agent to execute)
- Research findings
- Execution metadata

The graph (`app/graph/graph.py`) defines conditional edges where the Supervisor routes to appropriate workers until task completion.

### Vector Database
- **Milvus** provides semantic search capabilities for RAG
- HNSW indexing for efficient approximate nearest neighbor search
- 2560-dimensional vectors matching Qwen3-Embedding-4B
- Collection name: `enterprise_knowledge`
- Managed through `app/services/milvus_service.py`

### Tech Stack
- **Backend**: Python 3.10+, FastAPI, LangGraph, LangChain
- **Frontend**: Vue 3, Element Plus, Pinia, Vite
- **Databases**: PostgreSQL (relational), Milvus (vector)
- **LLM**: SiliconFlow (Qwen2.5-7B-Instruct) as primary, GLM (智谱AI) as fallback
- **Embeddings**: Qwen3-Embedding-4B (2560 dimensions)
- **External APIs**: Tavily (web search)

## Development Commands

### Backend Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Development server (http://localhost:5173)
npm run dev

# Production build
npm run build
npm run preview
```

### Docker Deployment
```bash
# Start all services (API, Milvus, PostgreSQL)
docker-compose up -d

# View API logs
docker-compose logs -f api

# Stop services
docker-compose down
```

**Important**: Milvus requires 30-60 seconds to fully initialize. The API includes startup checks but may log connection warnings initially.

## Configuration

Configuration is managed through `app/config.py` using Pydantic Settings. Environment variables are loaded from `.env` file:

**Required variables:**
- `DATABASE_URL`: PostgreSQL connection string
- `MILVUS_HOST`: Milvus server address
- `MILVUS_PORT`: Milvus port
- `SILICONFLOW_API_KEY` or `GLM_API_KEY`: LLM provider credentials
- `TAVILY_API_KEY`: Web search API

**Optional variables:**
- `USE_SILICONFLOW`: Enable SiliconFlow as primary LLM (default: true)
- `LANGCHAIN_TRACING_V2`: Enable LangSmith tracing
- `LANGCHAIN_API_KEY`: LangSmith API key
- `LANGCHAIN_PROJECT`: LangSmith project name

## Key API Endpoints

### Agent Execution
- `POST /api/v1/agent/execute` - Execute multi-agent workflow
- `POST /api/v1/agent/stream` - Streaming agent execution with real-time updates
- `GET /api/v1/agent/status/{session_id}` - Query execution status
- `GET /api/v1/agent/history` - Retrieve execution history

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration

### Session Management
- `GET /api/v1/session/history` - Retrieve conversation history
- `GET /api/v1/session/{session_id}` - Get session details

### Knowledge Base
- `POST /api/v1/knowledge/upload` - Upload documents to Milvus
- `POST /api/v1/knowledge/search` - Semantic search in knowledge base
- `GET /api/v1/knowledge/stats` - Knowledge base statistics
- `POST /api/v1/knowledge/batch-insert` - Batch insert vectors

## Adding New Agents

1. **Define Agent Function** in `app/graph/agents.py`:
   ```python
   def create_new_agent() -> callable:
       llm = create_llm()
       prompt = ChatPromptTemplate.from_messages([
           ("system", "Your system prompt here"),
           MessagesPlaceholder(variable_name="messages"),
       ])
       chain = prompt | llm

       def new_agent_node(state: AgentState) -> dict:
           result = chain.invoke({"messages": state["messages"]})
           response_message = AIMessage(content=result.content, name="NewAgent")
           return {"messages": state["messages"] + [response_message]}

       return new_agent_node
   ```

2. **Register Node** in `app/graph/graph.py`:
   ```python
   workflow.add_node("NewAgent", create_new_agent())
   # Add conditional edge from Supervisor
   ```

3. **Update Supervisor Prompt** in `app/config.py` to include instructions for when to call the new agent

## Adding New Tools

1. **Define Tool Class** in `app/graph/tools.py`:
   ```python
   from langchain_core.tools import BaseTool
   from pydantic import BaseModel, Field

   class NewToolInput(BaseModel):
       query: str = Field(description="The query to process")

   class NewTool(BaseTool):
       name = "new_tool"
       description = "Tool description"
       args_schema = NewToolInput

       def _run(self, query: str) -> str:
           # Tool implementation
           return result
   ```

2. **Register Tool** by binding to LLM in agent creation in `app/graph/agents.py`:
   ```python
   llm = create_llm().bind_tools(
       tools=[milvus_search_tool, tavily_search_tool, new_tool]
   )
   ```

## Code Organization

- `app/api/`: FastAPI route handlers (agent, knowledge, auth, session)
- `app/graph/`: LangGraph orchestration (agents, graph, state, tools)
- `app/services/`: Business logic (embedding generation, Milvus operations)
- `app/core/`: Security utilities (JWT, password hashing)
- `app/models/`: Database models (user, session)
- `app/schemas/`: Pydantic schemas for request/response validation
- `frontend/src/components/`: Vue components (ChatWindow, ThoughtProcess, SourcesPanel, Sidebar)
- `frontend/src/views/`: Page views (ChatView, KnowledgeView, HistoryView, AgentsView, LoginView)
- `frontend/src/store/`: Pinia state stores
- `frontend/src/api/`: API client functions

## Authentication & Sessions

The system includes user authentication and session management:
- JWT-based authentication via `app/api/auth.py`
- Session persistence in PostgreSQL via `app/models/session.py`
- Password hashing with bcrypt via `app/core/security.py`
- Login endpoint: `POST /api/v1/auth/login`
- Session history endpoint: `GET /api/v1/session/history`

## Important Notes

- The system uses SiliconFlow's OpenAI-compatible API for LLM calls
- Milvus collection name is `enterprise_knowledge`
- Agent state is persisted in PostgreSQL for session management
- Frontend uses Server-Sent Events (SSE) for real-time streaming updates
- The Supervisor agent uses `{"next": "agent_name"}` JSON format to route to workers
- Embedding dimension is 2560 (Qwen3-Embedding-4B)
- Milvus requires 30-60 seconds to fully initialize on startup
