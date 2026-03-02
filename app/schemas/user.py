from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """用户注册模型"""
    password: str


class UserLogin(BaseModel):
    """用户登录模型"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    is_active: bool
    is_admin: bool
    api_quota: int
    api_used: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    """Token数据模型"""
    user_id: Optional[int] = None
