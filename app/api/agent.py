"""
Agent 相关 API 路由

提供多智能体系统的执行接口
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from loguru import logger
from sqlalchemy.orm import Session

from app.graph.graph import run_multi_agent, stream_multi_agent
from app.database import get_db
from app.models.user import User
from app.models.session import ChatSession
from app.schemas.session import Message, SessionCreate
from app.core.security import get_current_active_user

router = APIRouter()


# ============================
# Session 管理辅助函数
# ============================

def get_or_create_session(
    db: Session,
    user_id: int,
    session_id: Optional[str],
    mode: str
) -> tuple[str, ChatSession]:
    """
    获取或创建会话

    Args:
        db: 数据库会话
        user_id: 用户ID
        session_id: 会话ID (可选)
        mode: 执行模式

    Returns:
        tuple: (session_id, ChatSession对象)
    """
    if session_id:
        # 尝试获取现有会话
        db_session = db.query(ChatSession)\
            .filter(ChatSession.session_id == session_id)\
            .filter(ChatSession.user_id == user_id)\
            .first()
        if db_session:
            return session_id, db_session

    # 创建新会话
    import uuid
    new_session_id = str(uuid.uuid4())

    # 检查session_id是否已存在（极小概率）
    while db.query(ChatSession).filter(ChatSession.session_id == new_session_id).first():
        new_session_id = str(uuid.uuid4())

    db_session = ChatSession(
        user_id=user_id,
        session_id=new_session_id,
        mode=mode,
        messages=[],
        meta={}
    )

    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return new_session_id, db_session


def add_message_to_session(
    db: Session,
    db_session: ChatSession,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    向会话添加消息

    Args:
        db: 数据库会话
        db_session: ChatSession对象
        role: 消息角色 (user/assistant/system)
        content: 消息内容
        metadata: 可选的元数据
    """
    from datetime import datetime

    if db_session.messages is None:
        db_session.messages = []

    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": metadata or {}
    }

    db_session.messages.append(message)

    # 如果是第一条用户消息且没有标题，自动生成标题
    if not db_session.title and role == "user":
        title = content.strip().replace("\n", " ")
        if len(title) > 50:
            title = title[:50] + "..."
        db_session.title = title or "新会话"

    db.commit()


# ============================
# 请求/响应模型
# ============================

class AgentExecuteRequest(BaseModel):
    """Agent 执行请求"""
    query: str = Field(..., description="用户查询", min_length=1)
    session_id: Optional[str] = Field(None, description="会话 ID")
    stream: bool = Field(False, description="是否使用流式输出")
    mode: Optional[str] = Field("agent", description="模式选择: rag(仅知识库), agent(多智能体), normal(普通对话)")
    history: Optional[List[Dict[str, str]]] = Field([], description="对话历史")


class AgentExecuteResponse(BaseModel):
    """Agent 执行响应"""
    session_id: str
    final_answer: str
    execution_trace: List[Dict[str, Any]]
    status: str
    sources: List[Dict[str, str]] = Field(default_factory=list, description="参考来源链接列表")


class AgentStatusResponse(BaseModel):
    """Agent 状态响应"""
    thread_id: str
    status: str
    current_step: str
    progress: float


# ============================
# API 端点
# ============================

@router.post("/execute", response_model=AgentExecuteResponse)
async def execute_agent(
    request: AgentExecuteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    执行多智能体任务

    支持三种模式:
    1. agent模式 (默认): 完整的多智能体协作系统 (Supervisor + Research + Writer)
    2. rag模式: 仅使用知识库检索
    3. normal模式: 普通对话，不使用任何工具

    Args:
        request: 包含用户查询、会话 ID、模式和对话历史
        current_user: 当前认证用户
        db: 数据库会话

    Returns:
        AgentExecuteResponse: 执行结果，包括最终答案和执行轨迹

    示例:
        ```python
        response = await execute_agent(
            AgentExecuteRequest(
                query="分析人工智能在医疗领域的最新进展",
                session_id="session-123",
                mode="agent",
                history=[{"role": "user", "content": "你好"}]
            )
        )
        ```
    """
    try:
        print(f"\n{'='*60}")
        print(f"[API] 收到请求")
        print(f"[API] 模式: {request.mode}")
        print(f"[API] 查询: {request.query[:50]}...")
        print(f"{'='*60}\n")

        logger.info(f"收到 Agent 执行请求 (模式: {request.mode}): {request.query}")

        # 获取或创建会话
        session_id, db_session = get_or_create_session(
            db=db,
            user_id=current_user.id,
            session_id=request.session_id,
            mode=request.mode
        )

        # 保存用户消息到会话
        add_message_to_session(
            db=db,
            db_session=db_session,
            role="user",
            content=request.query,
            metadata={"mode": request.mode}
        )

        # 根据模式选择不同的处理逻辑
        if request.mode == "rag":
            # RAG模式: 仅使用知识库检索
            print(f"[API] 使用 RAG 模式 - 不会返回 sources")
            logger.info(f"[API] 使用 RAG 模式 - 不会返回 sources")
            result = await _execute_rag_mode(request)
        elif request.mode == "normal":
            # 普通模式: 直接使用LLM，不使用工具
            print(f"[API] 使用 Normal 模式 - 不会返回 sources")
            logger.info(f"[API] 使用 Normal 模式 - 不会返回 sources")
            result = await _execute_normal_mode(request)
        else:
            # Agent模式 (默认): 完整的多智能体系统
            print(f"[API] 使用 Agent 模式 - 应该返回 sources")
            logger.info(f"[API] 使用 Agent 模式 - 应该返回 sources")
            result = run_multi_agent(
                query=request.query,
                session_id=session_id,  # 使用新创建的session_id
                history=request.history
            )

        print(f"\n{'='*60}")
        print(f"[API] 执行完成")
        print(f"[API] 模式: {request.mode}")
        print(f"[API] result 中的 sources 数量: {len(result.get('sources', []))}")
        print(f"{'='*60}\n")

        logger.info(f"Agent 执行完成: {session_id}")
        logger.info(f"[API] 模式: {request.mode}, result 中的 sources 数量: {len(result.get('sources', []))}")

        # 保存助手响应到会话
        add_message_to_session(
            db=db,
            db_session=db_session,
            role="assistant",
            content=result["final_answer"],
            metadata={
                "mode": request.mode,
                "execution_trace": result.get("execution_trace", []),
                "sources": result.get("sources", [])
            }
        )

        # 构建响应
        sources_from_result = result.get("sources", [])
        response = AgentExecuteResponse(
            session_id=session_id,  # 返回实际的session_id
            final_answer=result["final_answer"],
            execution_trace=result.get("execution_trace", []),
            status="completed",
            sources=sources_from_result
        )

        print(f"[API] 返回给前端的 sources 数量: {len(response.sources)}\n")
        logger.info(f"[API] 返回给前端的 sources 数量: {len(response.sources)}")

        return response

    except Exception as e:
        logger.error(f"Agent 执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _execute_rag_mode(request: AgentExecuteRequest):
    """RAG模式: 仅使用知识库检索"""
    from app.services.embedding_service import get_embedding
    from app.services.milvus_service import milvus_service
    from langchain_openai import ChatOpenAI
    from app.config import settings

    # 1. 检索知识库
    query_vector = get_embedding(request.query)
    search_results = milvus_service.search(query_vector=query_vector, top_k=5)

    # 2. 相似度阈值
    SIMILARITY_THRESHOLD = 0.35  # 相似度阈值

    if not search_results or len(search_results) == 0:
        return {
            "session_id": request.session_id or "default",
            "final_answer": "❌ **知识库为空**\n\n**说明：**\n- 知识库中没有任何文档\n- 相似度: 0%\n\n**建议：**\n1. 上传文档到知识库\n2. 使用「多智能体模式」进行网络搜索",
            "execution_trace": [{"mode": "rag", "documents_retrieved": 0, "max_score": 0}],
            "sources": []
        }

    # 检查最高相似度分数
    max_score = max([result.get("score", 0) for result in search_results])

    print(f"[RAG] 检索到 {len(search_results)} 条结果")
    print(f"[RAG] 最高相似度分数: {max_score:.4f}")
    print(f"[RAG] 相似度阈值: {SIMILARITY_THRESHOLD}")

    # 如果相似度低于阈值，直接返回提示信息
    if max_score < SIMILARITY_THRESHOLD:
        return {
            "session_id": request.session_id or "default",
            "final_answer": f"❌ **知识库中没有找到相关内容**\n\n**检索情况：**\n- 检索到 {len(search_results)} 条文档片段\n- 最高相似度：{max_score:.2%}（低于阈值 {SIMILARITY_THRESHOLD:.2%}）\n\n**建议：**\n1. 尝试用不同的关键词重新提问\n2. 上传更多相关文档到知识库\n3. 使用「多智能体模式」进行网络搜索",
            "execution_trace": [{"mode": "rag", "documents_retrieved": len(search_results), "max_score": max_score, "below_threshold": True}],
            "sources": []
        }

    # 3. 构建上下文和来源文件信息
    context_parts = []
    source_files = set()  # 用于去重文件名

    for i, doc in enumerate(search_results):
        filename = doc.get("metadata", {}).get("filename", f"文档{i+1}")
        score = doc.get("score", 0)
        source_files.add(filename)
        # 在上下文中标注相似度
        context_parts.append(f"【来源: {filename} (相似度: {score:.2%})】\n{doc['text']}")

    context = "\n\n".join(context_parts)
    source_files_list = list(source_files)

    print(f"[RAG] 使用 {len(search_results)} 条文档生成回答")

    # 4. 根据相似度决定如何使用LLM
    if settings.USE_SILICONFLOW:
        llm = ChatOpenAI(
            model=settings.SILICONFLOW_CHAT_MODEL,
            api_key=settings.SILICONFLOW_API_KEY,
            base_url=settings.SILICONFLOW_API_BASE,
            temperature=settings.SILICONFLOW_TEMPERATURE
        )
    else:
        llm = ChatOpenAI(
            model="glm-4-flash",
            api_key=settings.GLM_API_KEY,
            base_url="https://open.bigmodel.cn/api/paas/v4/"
        )

    # 构建对话历史
    messages = []
    for msg in request.history:
        messages.append((msg["role"], msg["content"]))

    # 构建来源信息文本
    source_info = "、".join(source_files_list)

    # 构建系统提示（只有相似度足够高才会执行到这里）
    system_prompt = f"""你是一个专业的AI助手。请基于以下知识库内容回答用户问题。

知识库内容:
{context}

**重要提示：**
1. 回答时请引用相关文档，使用格式：`[来源: 文件名.md]`
2. 如果内容来自多个文件，请在相关段落后面标注来源
3. 请明确指出哪些信息来自哪个文件
4. 使用结构化的方式组织回答（使用数字序号或项目符号）
5. 重要内容使用粗体强调
6. 分段清晰，每段一个要点

本次查询的知识库来源文件: {source_info}"""

    messages.insert(0, ("system", system_prompt))
    messages.append(("human", request.query))

    # 生成回答
    response = llm.invoke(messages)
    final_answer = response.content

    # 5. RAG模式不返回sources（不显示右侧面板）
    sources = []

    return {
        "session_id": request.session_id or "default",
        "final_answer": final_answer,
        "execution_trace": [{"mode": "rag", "documents_retrieved": len(search_results), "max_score": max_score, "source_files": source_files_list}],
        "sources": sources
    }


async def _execute_normal_mode(request: AgentExecuteRequest):
    """普通模式: 直接使用LLM，不使用工具"""
    from langchain_openai import ChatOpenAI
    from app.config import settings

    # 1. 使用LLM生成回答
    if settings.USE_SILICONFLOW:
        # 使用 SiliconFlow 免费模型
        llm = ChatOpenAI(
            model=settings.SILICONFLOW_CHAT_MODEL,
            api_key=settings.SILICONFLOW_API_KEY,
            base_url=settings.SILICONFLOW_API_BASE,
            temperature=settings.SILICONFLOW_TEMPERATURE
        )
    else:
        # 使用智谱 GLM
        llm = ChatOpenAI(
            model="glm-4-flash",
            api_key=settings.GLM_API_KEY,
            base_url="https://open.bigmodel.cn/api/paas/v4/"
        )

    # 构建对话历史
    messages = []
    for msg in request.history:
        messages.append((msg["role"], msg["content"]))

    # 添加系统提示
    system_prompt = """你是一个友好、专业的AI助手。请用简洁清晰的语言回答用户问题。

回答格式要求：
1. 使用结构化的方式组织回答（使用数字序号或项目符号）
2. 重要内容使用粗体强调
3. 分段清晰，每段一个要点
4. 保持简洁但信息丰富"""

    messages.insert(0, ("system", system_prompt))
    messages.append(("human", request.query))

    # 生成回答
    response = llm.invoke(messages)
    final_answer = response.content

    return {
        "session_id": request.session_id or "default",
        "final_answer": final_answer,
        "execution_trace": [{"mode": "normal"}]
    }


@router.get("/status/{thread_id}", response_model=AgentStatusResponse)
async def get_agent_status(thread_id: str):
    """
    获取 Agent 执行状态

    Args:
        thread_id: 线程 ID

    Returns:
        AgentStatusResponse: 当前状态
    """
    # TODO: 实现状态查询逻辑 (需要持久化执行状态)
    return AgentStatusResponse(
        thread_id=thread_id,
        status="running",
        current_step="Supervisor",
        progress=0.5
    )


@router.get("/history")
async def get_agent_history(
    skip: int = 0,
    limit: int = 10
):
    """
    获取 Agent 执行历史

    Args:
        skip: 跳过的记录数
        limit: 返回的记录数

    Returns:
        List[Dict]: 历史记录列表
    """
    # TODO: 实现历史记录查询 (需要数据库支持)
    return {
        "total": 0,
        "items": []
    }


@router.post("/stream")
async def execute_agent_stream(
    request: AgentExecuteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    流式执行多智能体任务

    使用 Server-Sent Events (SSE) 返回实时进度

    支持三种模式:
    1. agent模式 (默认): 完整的多智能体协作系统
    2. rag模式: 仅使用知识库检索
    3. normal模式: 普通对话

    Args:
        request: 包含用户查询、会话 ID、模式和对话历史
        current_user: 当前认证用户
        db: 数据库会话

    Returns:
        StreamingResponse: 流式响应

    示例:
        ```python
        async for event in execute_agent_stream(
            AgentExecuteRequest(
                query="分析人工智能在医疗领域的最新进展",
                session_id="session-123",
                mode="agent"
            )
        ):
            print(event)
        ```
    """
    from fastapi.responses import StreamingResponse
    import json

    async def event_generator():
        """生成 SSE 事件"""
        session_id = None
        db_session = None
        final_answer = ""

        try:
            # 获取或创建会话
            session_id, db_session = get_or_create_session(
                db=db,
                user_id=current_user.id,
                session_id=request.session_id,
                mode=request.mode
            )

            # 保存用户消息到会话
            add_message_to_session(
                db=db,
                db_session=db_session,
                role="user",
                content=request.query,
                metadata={"mode": request.mode}
            )

            # 根据模式选择不同的处理逻辑
            if request.mode == "agent":
                # Agent模式: 完整的多智能体系统（支持流式）
                for event in stream_multi_agent(
                    query=request.query,
                    session_id=session_id,
                    history=request.history
                ):
                    # 将事件转换为 JSON
                    event_data = json.dumps(event, ensure_ascii=False)
                    yield f"data: {event_data}\n\n"

                    # 收集最终答案
                    if event.get("type") == "complete":
                        final_answer = event.get("data", {}).get("final_answer", "")

            else:
                # RAG模式和Normal模式暂不支持流式，回退到普通模式
                logger.info(f"模式 {request.mode} 不支持流式，使用普通执行")

                # 执行普通模式
                if request.mode == "rag":
                    result = await _execute_rag_mode(request)
                else:
                    result = await _execute_normal_mode(request)

                final_answer = result["final_answer"]

                # 返回完整结果
                event_data = json.dumps({
                    "type": "complete",
                    "message": "处理完成",
                    "data": result
                }, ensure_ascii=False)
                yield f"data: {event_data}\n\n"

            # 保存助手响应到会话
            if final_answer and db_session:
                add_message_to_session(
                    db=db,
                    db_session=db_session,
                    role="assistant",
                    content=final_answer,
                    metadata={"mode": request.mode}
                )

        except Exception as e:
            logger.error(f"流式执行失败: {e}")
            import traceback
            error_data = json.dumps({
                "type": "error",
                "message": f"处理出错: {str(e)}",
                "data": {"error": str(e), "traceback": traceback.format_exc()}
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
