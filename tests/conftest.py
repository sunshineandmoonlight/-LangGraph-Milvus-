"""
Pytest 配置文件

提供测试所需的 fixtures 和测试工具
"""
import os
import sys
import pytest
import tempfile
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.models.user import User


# ============================
# 测试数据库配置
# ============================

# 使用 SQLite 内存数据库进行测试
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================
# Fixtures
# ============================

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    创建测试数据库会话

    每个测试函数使用独立的数据库，测试结束后自动清理
    """
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建会话
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # 清理所有表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """
    创建测试客户端

    使用测试数据库覆盖默认的数据库依赖
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """
    创建测试用户

    Returns:
        User: 测试用户对象
    """
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """
    创建测试用户的 JWT token

    Returns:
        str: JWT access token
    """
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def auth_headers(test_user_token: str) -> dict:
    """
    创建带认证的请求头

    Returns:
        dict: 包含 Authorization header 的字典
    """
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def temp_file() -> Generator[tempfile.TemporaryFile, None, None]:
    """
    创建临时文件 fixture

    用于测试文件上传功能
    """
    tmp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    tmp_file.write("This is a test document content.")
    tmp_file.close()

    yield tmp_file

    # 清理临时文件
    os.unlink(tmp_file.name)


# ============================
# 测试辅助函数
# ============================

def create_test_user(db: Session, email: str, username: str, password: str = "password123") -> User:
    """
    创建测试用户的辅助函数

    Args:
        db: 数据库会话
        email: 邮箱
        username: 用户名
        password: 密码

    Returns:
        User: 创建的用户对象
    """
    user = User(
        email=email,
        username=username,
        full_name=username,
        hashed_password=get_password_hash(password),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_and_get_token(client: TestClient, email: str, password: str) -> str:
    """
    登录并获取 token 的辅助函数

    Args:
        client: 测试客户端
        email: 邮箱
        password: 密码

    Returns:
        str: JWT access token
    """
    # 先注册用户
    client.post("/api/v1/auth/register", json={
        "email": email,
        "username": email.split("@")[0],
        "password": password
    })

    # 登录获取 token
    response = client.post("/api/v1/auth/login-json", json={
        "email": email,
        "password": password
    })

    return response.json()["access_token"]
