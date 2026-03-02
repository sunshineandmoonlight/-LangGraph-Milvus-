from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_active_user
)
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=Token)
async def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查邮箱是否已存在
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user_in.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用"
        )

    # 创建新用户
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password)
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 生成Token (sub 必须是字符串)
    access_token = create_access_token(data={"sub": str(db_user.id)})

    # 更新最后登录时间
    db_user.last_login = datetime.utcnow()
    db.commit()

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(db_user)
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成Token (sub 必须是字符串)
    access_token = create_access_token(data={"sub": str(user.id)})

    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )


@router.post("/login-json", response_model=Token)
async def login_json(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """用户登录（JSON格式）"""
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成Token (sub 必须是字符串)
    access_token = create_access_token(data={"sub": str(user.id)})

    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return UserResponse.from_orm(current_user)


@router.post("/logout")
async def logout():
    """用户登出"""
    # 由于使用JWT，登出主要在前端处理（删除token）
    # 这里可以添加token黑名单等逻辑
    return {"message": "成功登出"}


@router.post("/demo-login", response_model=Token)
async def demo_login(db: Session = Depends(get_db)):
    """演示模式快速登录（跳过密码验证，仅用于测试/演示）"""
    demo_email = "demo@enterprise.ai"

    # 检查演示账号是否存在
    user = db.query(User).filter(User.email == demo_email).first()

    if not user:
        # 如果不存在，创建演示账号（密码是预哈希的，避免慢速bcrypt）
        user = User(
            email=demo_email,
            username="DemoUser",
            full_name="测试用户",
            hashed_password="$2b$02$dummy"  # 演示账号，不需要真实密码
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 生成Token（无需密码验证，极快，sub 必须是字符串）
    access_token = create_access_token(data={"sub": str(user.id)})

    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )
