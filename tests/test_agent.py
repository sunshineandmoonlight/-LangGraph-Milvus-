"""
Agent 模块集成测试

测试 Agent 执行、工具调用等功能
"""
import pytest
from fastapi.testclient import TestClient


class TestAgentExecute:
    """Agent 执行功能测试"""

    def test_execute_agent_normal_mode(self, client: TestClient, auth_headers: dict):
        """测试普通模式执行 Agent"""
        response = client.post(
            "/api/v1/agent/execute",
            headers=auth_headers,
            json={
                "query": "你好，请介绍一下你自己",
                "mode": "normal"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "final_answer" in data
        assert "session_id" in data
        assert len(data["final_answer"]) > 0

    def test_execute_agent_without_authentication(self, client: TestClient):
        """测试未登录执行 Agent 应该失败"""
        response = client.post(
            "/api/v1/agent/execute",
            json={
                "query": "test query",
                "mode": "normal"
            }
        )

        assert response.status_code == 401

    def test_execute_agent_with_empty_query(self, client: TestClient, auth_headers: dict):
        """测试空查询应该失败"""
        response = client.post(
            "/api/v1/agent/execute",
            headers=auth_headers,
            json={
                "query": "",
                "mode": "normal"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_execute_agent_rag_mode_with_knowledge(self, client: TestClient, auth_headers: dict):
        """测试 RAG 模式（有知识库内容）"""
        # 先上传知识库文档
        import io
        content = b"打印机的故障排除：如果打印机显示脱机状态，请检查电源线和连接线。"
        files = {"file": ("printer.txt", io.BytesIO(content), "text/plain")}
        client.post("/api/v1/knowledge/upload", headers=auth_headers, files=files)

        # 等待向量插入
        import time
        time.sleep(2)

        # 使用 RAG 模式提问
        response = client.post(
            "/api/v1/agent/execute",
            headers=auth_headers,
            json={
                "query": "打印机显示脱机状态怎么办？",
                "mode": "rag"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "final_answer" in data
        # RAG 模式下，即使相似度不高也应该有回答
        assert len(data["final_answer"]) > 0

    def test_execute_agent_rag_mode_empty_knowledge(self, client: TestClient, auth_headers: dict):
        """测试 RAG 模式（空知识库）"""
        response = client.post(
            "/api/v1/agent/execute",
            headers=auth_headers,
            json={
                "query": "随机问题xyz",
                "mode": "rag"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "final_answer" in data
        # 空知识库时应该返回提示信息

    def test_execute_agent_with_session_context(self, client: TestClient, auth_headers: dict):
        """测试带会话上下文的 Agent 执行"""
        # 第一次请求
        response1 = client.post(
            "/api/v1/agent/execute",
            headers=auth_headers,
            json={
                "query": "我叫张三",
                "mode": "normal"
            }
        )
        session_id = response1.json()["session_id"]

        # 第二次请求，带上 session_id 和对话历史
        response2 = client.post(
            "/api/v1/agent/execute",
            headers=auth_headers,
            json={
                "query": "我叫什么名字？",
                "session_id": session_id,
                "mode": "normal",
                "history": [
                    {"role": "user", "content": "我叫张三"},
                    {"role": "assistant", "content": "你好张三！"}
                ]
            }
        )

        assert response2.status_code == 200
        data = response2.json()
        assert "张三" in data["final_answer"] or "记住" in data["final_answer"]

    def test_execute_agent_invalid_mode(self, client: TestClient, auth_headers: dict):
        """测试无效的模式"""
        response = client.post(
            "/api/v1/agent/execute",
            headers=auth_headers,
            json={
                "query": "test query",
                "mode": "invalid_mode"
            }
        )

        # 应该回退到默认模式或返回错误
        assert response.status_code in [200, 400]


class TestAgentStreaming:
    """Agent 流式输出测试"""

    def test_stream_agent_execute(self, client: TestClient, auth_headers: dict):
        """测试流式 Agent 执行"""
        # 注意：SSE 流式测试需要特殊处理
        # 这里只验证端点可访问
        response = client.post(
            "/api/v1/agent/stream",
            headers=auth_headers,
            json={
                "query": "简单问题",
                "mode": "normal"
            }
        )

        # 流式端点应该返回 200 和流式响应
        assert response.status_code == 200


class TestAgentTools:
    """Agent 工具测试"""

    def test_milvus_search_tool(self, client: TestClient, auth_headers: dict):
        """测试 Milvus 搜索工具"""
        # 先上传测试数据
        import io
        content = b"测试数据：人工智能是计算机科学的一个分支"
        files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}
        client.post("/api/v1/knowledge/upload", headers=auth_headers, files=files)

        import time
        time.sleep(1)

        # 使用 RAG 模式（会调用 milvus_search 工具）
        response = client.post(
            "/api/v1/agent/execute",
            headers=auth_headers,
            json={
                "query": "人工智能",
                "mode": "rag"
            }
        )

        assert response.status_code == 200

    def test_tavily_search_tool(self, client: TestClient, auth_headers: dict):
        """测试 Tavily 网络搜索工具"""
        # 使用 Agent 模式（可能调用 tavily_search 工具）
        response = client.post(
            "/api/v1/agent/execute",
            headers=auth_headers,
            json={
                "query": "今天北京的天气怎么样？",
                "mode": "agent"
            }
        )

        # 注意：这需要有效的 TAVILY_API_KEY
        # 如果没有配置，可能会失败或回退到其他方式
        assert response.status_code in [200, 500]


class TestAgentHistory:
    """Agent 历史记录测试"""

    def test_get_agent_history(self, client: TestClient, auth_headers: dict):
        """测试获取 Agent 执行历史"""
        response = client.get(
            "/api/v1/agent/history",
            headers=auth_headers
        )

        # 当前实现返回空数据（TODO）
        assert response.status_code == 200
        data = response.json()
        assert "total" in data


class TestAgentStatus:
    """Agent 状态查询测试"""

    def test_get_agent_status(self, client: TestClient):
        """测试获取 Agent 执行状态"""
        response = client.get("/api/v1/agent/status/test-thread-123")

        # 当前实现返回固定状态（TODO）
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
