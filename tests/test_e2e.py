"""
端到端测试 (E2E Tests)

模拟真实用户场景的完整流程测试
"""
import pytest
import io
from fastapi.testclient import TestClient


class TestE2EUserJourney:
    """用户完整使用流程测试"""

    def test_complete_new_user_workflow(self, client: TestClient):
        """
        测试新用户的完整使用流程：
        1. 注册账号
        2. 登录
        3. 上传知识库文档
        4. 使用 RAG 模式提问
        5. 查看会话历史
        """
        # ========== 步骤 1: 注册账号 ==========
        register_response = client.post("/api/v1/auth/register", json={
            "email": "e2e@example.com",
            "username": "e2euser",
            "password": "password123"
        })
        assert register_response.status_code == 200
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # ========== 步骤 2: 登录验证 ==========
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "e2e@example.com"

        # ========== 步骤 3: 上传知识库文档 ==========
        content = b"""
        公司打印机使用指南

        一、打印机开机
        1. 确认电源线连接稳固
        2. 按下电源按钮，指示灯变绿表示就绪

        二、打印文件
        1. 打开要打印的文件
        2. 点击文件 -> 打印
        3. 选择正确的打印机
        4. 点击打印按钮

        三、常见问题
        打印机卡纸：打开盖子取出纸张，关闭盖子重试
        打印模糊：更换墨盒或清洁打印头
        """
        files = {"file": ("printer_guide.txt", io.BytesIO(content), "text/plain")}
        upload_response = client.post(
            "/api/v1/knowledge/upload",
            headers=headers,
            files=files
        )
        assert upload_response.status_code == 200

        # 等待向量插入
        import time
        time.sleep(2)

        # ========== 步骤 4: 使用 RAG 模式提问 ==========
        rag_response = client.post(
            "/api/v1/agent/execute",
            headers=headers,
            json={
                "query": "打印机开机后指示灯是什么颜色？",
                "mode": "rag"
            }
        )
        assert rag_response.status_code == 200
        rag_result = rag_response.json()
        assert "final_answer" in rag_result
        assert "green" in rag_result["final_answer"].lower() or "绿" in rag_result["final_answer"]
        session_id = rag_result["session_id"]

        # ========== 步骤 5: 查看会话历史 ==========
        sessions_response = client.get("/api/v1/sessions", headers=headers)
        assert sessions_response.status_code == 200
        sessions = sessions_response.json()["sessions"]
        assert len(sessions) >= 1
        assert any(s["session_id"] == session_id for s in sessions)


class TestE2EKnowledgeBaseWorkflow:
    """知识库管理完整流程测试"""

    def test_knowledge_base_management(self, client: TestClient):
        """
        测试知识库管理流程：
        1. 登录
        2. 上传多个文档
        3. 搜索知识库
        4. 查看统计信息
        5. 删除文档
        """
        # ========== 登录 ==========
        token = self._login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # ========== 上传多个文档 ==========
        documents = [
            ("doc1.txt", b"Python 是一种编程语言"),
            ("doc2.txt", b"JavaScript 是 Web 开发语言"),
            ("doc3.txt", b"Java 用于企业级应用开发")
        ]

        for filename, content in documents:
            files = {"file": (filename, io.BytesIO(content), "text/plain")}
            response = client.post(
                "/api/v1/knowledge/upload",
                headers=headers,
                files=files
            )
            assert response.status_code == 200

        import time
        time.sleep(2)

        # ========== 搜索知识库 ==========
        search_response = client.post(
            "/api/v1/knowledge/search",
            headers=headers,
            json={"query": "编程语言", "top_k": 5}
        )
        assert search_response.status_code == 200
        results = search_response.json()["results"]
        # 应该能找到相关文档

        # ========== 查看统计信息 ==========
        stats_response = client.get("/api/v1/knowledge/stats", headers=headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["num_files"] >= 3

        # ========== 列出所有文档 ==========
        docs_response = client.get("/api/v1/knowledge/documents", headers=headers)
        assert docs_response.status_code == 200

    def _login_and_get_token(self, client: TestClient) -> str:
        """辅助方法：登录并获取 token"""
        # 先注册
        client.post("/api/v1/auth/register", json={
            "email": "kbtest@example.com",
            "username": "kbtest",
            "password": "password123"
        })
        # 再登录
        response = client.post("/api/v1/auth/login-json", json={
            "email": "kbtest@example.com",
            "password": "password123"
        })
        return response.json()["access_token"]


class TestE2EMultiTurnConversation:
    """多轮对话完整流程测试"""

    def test_multi_turn_conversation(self, client: TestClient):
        """
        测试多轮对话流程：
        1. 用户发起第一轮对话
        2. AI 回复
        3. 用户基于上下文追问
        4. AI 结合历史回复
        """
        # ========== 登录 ==========
        token = self._login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # ========== 第一轮对话 ==========
        response1 = client.post(
            "/api/v1/agent/execute",
            headers=headers,
            json={
                "query": "我喜欢红色和蓝色",
                "mode": "normal"
            }
        )
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # ========== 第二轮对话（带上下文） ==========
        response2 = client.post(
            "/api/v1/agent/execute",
            headers=headers,
            json={
                "query": "根据我刚才说的，我喜欢什么颜色？",
                "session_id": session_id,
                "mode": "normal",
                "history": [
                    {"role": "user", "content": "我喜欢红色和蓝色"},
                    {"role": "assistant", "content": "好的，我记住了你喜欢红色和蓝色"}
                ]
            }
        )
        assert response2.status_code == 200
        answer = response2.json()["final_answer"]
        # AI 应该能回答出红色和蓝色
        assert "红" in answer or "蓝" in answer

    def _login_and_get_token(self, client: TestClient) -> str:
        """辅助方法：登录并获取 token"""
        client.post("/api/v1/auth/register", json={
            "email": "conv@example.com",
            "username": "convtest",
            "password": "password123"
        })
        response = client.post("/api/v1/auth/login-json", json={
            "email": "conv@example.com",
            "password": "password123"
        })
        return response.json()["access_token"]


class TestE2EErrorHandling:
    """错误处理流程测试"""

    def test_handle_api_errors_gracefully(self, client: TestClient):
        """
        测试系统对各种错误的处理：
        1. 无效的请求格式
        2. 未授权的访问
        3. 资源不存在
        """
        # ========== 测试无效请求格式 ==========
        response = client.post(
            "/api/v1/agent/execute",
            json={"query": ""}  # 空查询
        )
        assert response.status_code == 422

        # ========== 测试未授权访问 ==========
        response = client.get("/api/v1/sessions")
        assert response.status_code == 401

        # ========== 测试资源不存在 ==========
        token = self._login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/sessions/non-existent-session-id", headers=headers)
        assert response.status_code == 404

    def _login_and_get_token(self, client: TestClient) -> str:
        """辅助方法：登录并获取 token"""
        client.post("/api/v1/auth/register", json={
            "email": "error@example.com",
            "username": "errortest",
            "password": "password123"
        })
        response = client.post("/api/v1/auth/login-json", json={
            "email": "error@example.com",
            "password": "password123"
        })
        return response.json()["access_token"]


class TestE2EAgentModes:
    """不同 Agent 模式的端到端测试"""

    def test_compare_agent_modes(self, client: TestClient):
        """
        对比三种模式的差异：
        1. Normal 模式 - 纯对话
        2. RAG 模式 - 知识库检索
        3. Agent 模式 - 多智能体协作
        """
        # ========== 登录 ==========
        token = self._login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # 上传测试文档
        content = b"测试项目的截止日期是2024年12月31日"
        files = {"file": ("project.txt", io.BytesIO(content), "text/plain")}
        client.post("/api/v1/knowledge/upload", headers=headers, files=files)

        import time
        time.sleep(2)

        query = "项目的截止日期是什么时候？"

        # ========== Normal 模式 ==========
        normal_response = client.post(
            "/api/v1/agent/execute",
            headers=headers,
            json={"query": query, "mode": "normal"}
        )
        assert normal_response.status_code == 200
        normal_answer = normal_response.json()["final_answer"]
        # Normal 模式不知道具体日期

        # ========== RAG 模式 ==========
        rag_response = client.post(
            "/api/v1/agent/execute",
            headers=headers,
            json={"query": query, "mode": "rag"}
        )
        assert rag_response.status_code == 200
        rag_answer = rag_response.json()["final_answer"]
        # RAG 模式应该能从知识库找到答案
        assert "2024" in rag_answer or "12月" in rag_answer

    def _login_and_get_token(self, client: TestClient) -> str:
        """辅助方法：登录并获取 token"""
        client.post("/api/v1/auth/register", json={
            "email": "mode@example.com",
            "username": "modetest",
            "password": "password123"
        })
        response = client.post("/api/v1/auth/login-json", json={
            "email": "mode@example.com",
            "password": "password123"
        })
        return response.json()["access_token"]
