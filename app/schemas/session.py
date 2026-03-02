from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    """消息模型"""
    role: str = Field(..., description="消息角色：user/assistant/system")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None  # 存储额外的元数据（如tokens、模型等）


class SessionBase(BaseModel):
    """会话基础模型"""
    title: Optional[str] = Field(None, max_length=200, description="会话标题")
    mode: Optional[str] = Field(None, pattern="^(agent|rag|normal)$", description="执行模式")


class SessionCreate(SessionBase):
    """创建会话"""
    pass


class SessionUpdate(BaseModel):
    """更新会话"""
    title: Optional[str] = Field(None, max_length=200)
    messages: Optional[List[Message]] = None


class SessionResponse(SessionBase):
    """会话响应"""
    id: int
    session_id: str
    user_id: int
    messages: Optional[List[Message]] = []
    meta: Optional[Dict[str, Any]] = None  # 改为 meta，与数据库模型一致
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[SessionResponse]
    total: int
    page: int
    page_size: int
