from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class ChatSession(Base):
    """会话模型"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=True)  # 会话标题，从第一条消息自动生成
    mode = Column(String(50), nullable=True)  # agent/rag/normal
    messages = Column(JSON, nullable=True)  # 存储完整的对话历史
    meta = Column(JSON, nullable=True)  # 存储额外的会话元数据
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, session_id='{self.session_id}', title='{self.title}')>"
