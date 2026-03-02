"""
聊天对话接口

提供用户对话接口，使用 LangGraph 的 astream_events 实现流式输出
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
from loguru import logger

from app.graph.workflow import run_multi_agent, stream_multi_agent


class ChatRequest(BaseModel):
    """聊天请求"""
    query: str = Field(..., description="用户查询")
    session_id: Optional[str] = Field(None, description="会话 ID")


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str
    final_answer: str
    execution_trace: List[Dict[str, Any]]
    status: str


router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


@router.post("/execute", response_model=ChatResponse)
async def execute_chat(request: ChatRequest):
    """
    执行多智能体任务（非流式）

    Args:
        request: 聊天请求

    Returns:
        ChatResponse: 执行结果
    """
    try:
        logger.info(f"收到聊天请求: {request.query}")

        # 执行多智能体系统
        result = run_multi_agent(
            query=request.query,
            session_id=request.session_id
        )

        return ChatResponse(
            session_id=result["session_id"],
            final_answer=result["final_answer"],
            execution_trace=result["execution_trace"],
            status="completed"
        )

    except Exception as e:
        logger.error(f"聊天执行失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/stream")
async def stream_chat(request: ChatRequest):
    """
    流式执行多智能体任务

    使用 astream_events 实现实时流式输出

    Args:
        request: 聊天请求

    Returns:
        StreamingResponse: 流式响应
    """
    async def event_generator():
        """生成 SSE 事件流"""
        try:
            # 流式执行多智能体系统
            for event in stream_multi_agent(
                query=request.query,
                session_id=request.session_id
            ):
                # 将事件转换为 JSON 格式
                event_data = json.dumps(event, ensure_ascii=False)
                yield f"data: {event_data}\n\n"

        except Exception as e:
            # 发送错误事件
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.get("/sessions")
async def get_sessions(
    skip: int = 0,
    limit: int = 10
):
    """
    获取会话列表

    Args:
        skip: 跳过的记录数
        limit: 返回的记录数

    Returns:
        Dict: 会话列表
    """
    # TODO: 实现从 PostgreSQL 查询会话历史
    return {
        "total": 0,
        "items": []
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    获取会话详情

    Args:
        session_id: 会话 ID

    Returns:
        Dict: 会话详情
    """
    # TODO: 从 PostgreSQL 查询特定会话的完整历史
    return {
        "session_id": session_id,
        "messages": []
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    删除会话

    Args:
        session_id: 会话 ID

    Returns:
        Dict: 删除结果
    """
    # TODO: 从 PostgreSQL 删除会话数据
    return {
        "session_id": session_id,
        "deleted": True
    }
