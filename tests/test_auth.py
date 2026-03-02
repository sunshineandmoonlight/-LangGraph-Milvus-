"""
认证模块集成测试

测试用户注册、登录、认证等功能
"""
import pytest
from fastapi.testclient import TestClient


class TestUserRegistration:
    """用户注册功能测试"""

    def test_register_new_user_successfully(self, client: TestClient):
        """测试成功注册新用户"""
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["username"] == "newuser"

    def test_register_duplicate_email_fails(self, client: TestClient):
        """测试重复邮箱注册应该失败"""
        user_data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "pass123"
        }

        # 第一次注册
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 200

        # 第二次注册相同邮箱
        response2 = client.post("/api/v1/auth/register", json={
            "email": "duplicate@example.com",
            "username": "user2",
            "password": "pass456"
        })

        assert response2.status_code == 400
        assert "已被注册" in response2.json()["detail"]

    def test_register_duplicate_username_fails(self, client: TestClient):
        """测试重复用户名注册应该失败"""
        # 第一次注册
        client.post("/api/v1/auth/register", json={
            "email": "user1@example.com",
            "username": "sameuser",
            "password": "pass123"
        })

        # 第二次注册相同用户名
        response = client.post("/api/v1/auth/register", json={
            "email": "user2@example.com",
            "username": "sameuser",
            "password": "pass456"
        })

        assert response.status_code == 400
        assert "已被使用" in response.json()["detail"]

    def test_register_with_invalid_email(self, client: TestClient):
        """测试使用无效邮箱注册"""
        response = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "username": "testuser",
            "password": "password123"
        })

        assert response.status_code == 422  # Validation error

    def test_register_with_short_password(self, client: TestClient):
        """测试使用过短密码注册"""
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "12345"  # 少于6位
        })

        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """用户登录功能测试"""

    def test_login_with_correct_credentials(self, client: TestClient):
        """测试使用正确的凭据登录"""
        # 先注册用户
        client.post("/api/v1/auth/register", json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "password123"
        })

        # 登录
        response = client.post("/api/v1/auth/login-json", json={
            "email": "login@example.com",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data

    def test_login_with_wrong_email(self, client: TestClient):
        """测试使用不存在的邮箱登录"""
        response = client.post("/api/v1/auth/login-json", json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })

        assert response.status_code == 401
        assert "错误" in response.json()["detail"]

    def test_login_with_wrong_password(self, client: TestClient):
        """测试使用错误的密码登录"""
        # 先注册用户
        client.post("/api/v1/auth/register", json={
            "email": "user@example.com",
            "username": "testuser",
            "password": "correct_password"
        })

        # 使用错误密码登录
        response = client.post("/api/v1/auth/login-json", json={
            "email": "user@example.com",
            "password": "wrong_password"
        })

        assert response.status_code == 401


class TestDemoLogin:
    """演示模式快速登录测试"""

    def test_demo_login_creates_user(self, client: TestClient):
        """测试演示登录创建演示账号"""
        response = client.post("/api/v1/auth/demo-login")

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "demo@enterprise.ai"

    def test_demo_login_reuses_existing_user(self, client: TestClient):
        """测试演示登录复用已存在的演示账号"""
        # 第一次演示登录
        response1 = client.post("/api/v1/auth/demo-login")
        user1 = response1.json()["user"]

        # 第二次演示登录
        response2 = client.post("/api/v1/auth/demo-login")
        user2 = response2.json()["user"]

        # 应该是同一个用户
        assert user1["email"] == user2["email"]


class TestAuthentication:
    """认证保护测试"""

    def test_access_protected_endpoint_without_token(self, client: TestClient):
        """测试未登录访问受保护端点应该失败"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_access_protected_endpoint_with_valid_token(self, client: TestClient, test_user_token: str):
        """测试使用有效 token 访问受保护端点"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "email" in data

    def test_access_protected_endpoint_with_invalid_token(self, client: TestClient):
        """测试使用无效 token 访问受保护端点"""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 401

    def test_access_protected_endpoint_with_expired_token(self, client: TestClient):
        """测试使用过期 token 访问受保护端点（如果实现了过期机制）"""
        # 这个测试需要创建一个已过期的 token
        # 目前项目中的 token 有效期是 7 天，这里暂时跳过
        pass


class TestSessionManagement:
    """会话管理测试"""

    def test_create_session_with_authenticated_user(self, client: TestClient, auth_headers: dict):
        """测试已登录用户创建会话"""
        response = client.post(
            "/api/v1/sessions",
            headers=auth_headers,
            json={"mode": "agent"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert data["mode"] == "agent"

    def test_get_sessions_list(self, client: TestClient, auth_headers: dict):
        """测试获取会话列表"""
        # 先创建一个会话
        client.post("/api/v1/sessions", headers=auth_headers, json={"mode": "rag"})

        # 获取会话列表
        response = client.get("/api/v1/sessions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) >= 1

    def test_get_session_without_auth(self, client: TestClient):
        """测试未登录获取会话应该失败"""
        response = client.get("/api/v1/sessions")

        assert response.status_code == 401
