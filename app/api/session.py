import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.session import ChatSession
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse, SessionListResponse, Message
from app.core.security import get_current_active_user

router = APIRouter(prefix="/sessions", tags=["会话管理"])


def generate_session_id() -> str:
    """生成唯一的会话ID"""
    return str(uuid.uuid4())


def generate_title_from_message(message: str, max_length: int = 50) -> str:
    """从第一条消息生成会话标题"""
    # 移除换行和多余空格
    title = message.strip().replace("\n", " ")
    # 截断到指定长度
    if len(title) > max_length:
        title = title[:max_length] + "..."
    return title or "新会话"


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_in: SessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新会话"""
    # 生成唯一session_id
    session_id = generate_session_id()

    # 检查session_id是否已存在（极小概率）
    while db.query(ChatSession).filter(ChatSession.session_id == session_id).first():
        session_id = generate_session_id()

    # 创建会话
    db_session = ChatSession(
        user_id=current_user.id,
        session_id=session_id,
        mode=session_in.mode,
        messages=[],
        meta={}
    )

    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return SessionResponse.from_orm(db_session)


@router.get("", response_model=SessionListResponse)
async def get_sessions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有会话（分页）"""
    # 查询总数
    total = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).count()

    # 分页查询
    sessions = db.query(ChatSession)\
        .filter(ChatSession.user_id == current_user.id)\
        .order_by(ChatSession.updated_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()

    return SessionListResponse(
        sessions=[SessionResponse.from_orm(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取指定会话的详细信息"""
    db_session = db.query(ChatSession)\
        .filter(ChatSession.session_id == session_id)\
        .filter(ChatSession.user_id == current_user.id)\
        .first()

    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    return SessionResponse.from_orm(db_session)


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_update: SessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新会话（标题或消息）"""
    db_session = db.query(ChatSession)\
        .filter(ChatSession.session_id == session_id)\
        .filter(ChatSession.user_id == current_user.id)\
        .first()

    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    # 更新字段
    if session_update.title is not None:
        db_session.title = session_update.title

    if session_update.messages is not None:
        db_session.messages = [m.dict() for m in session_update.messages]

    db_session.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_session)

    return SessionResponse.from_orm(db_session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除指定会话"""
    db_session = db.query(ChatSession)\
        .filter(ChatSession.session_id == session_id)\
        .filter(ChatSession.user_id == current_user.id)\
        .first()

    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    db.delete(db_session)
    db.commit()

    return None


@router.post("/{session_id}/messages", response_model=SessionResponse)
async def add_message(
    session_id: str,
    message: Message,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """向会话添加新消息"""
    db_session = db.query(ChatSession)\
        .filter(ChatSession.session_id == session_id)\
        .filter(ChatSession.user_id == current_user.id)\
        .first()

    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    # 初始化messages列表
    if db_session.messages is None:
        db_session.messages = []

    # 添加消息
    message_dict = message.dict()
    message_dict["timestamp"] = datetime.utcnow().isoformat()
    db_session.messages.append(message_dict)

    # 如果是第一条消息且没有标题，自动生成标题
    if not db_session.title and message.role == "user":
        db_session.title = generate_title_from_message(message.content)

    db_session.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_session)

    return SessionResponse.from_orm(db_session)


@router.get("/{session_id}/messages", response_model=List[Message])
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取会话的所有消息"""
    db_session = db.query(ChatSession)\
        .filter(ChatSession.session_id == session_id)\
        .filter(ChatSession.user_id == current_user.id)\
        .first()

    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    messages = db_session.messages or []
    return [Message(**m) if isinstance(m, dict) else m for m in messages]
