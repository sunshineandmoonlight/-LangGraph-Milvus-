"""
知识库模块集成测试

测试文档上传、搜索、统计等功能
"""
import pytest
import io
from fastapi.testclient import TestClient


class TestDocumentUpload:
    """文档上传功能测试"""

    def test_upload_text_file_successfully(self, client: TestClient, auth_headers: dict):
        """测试成功上传文本文件"""
        content = b"This is a test document about artificial intelligence."
        files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}

        response = client.post(
            "/api/v1/knowledge/upload",
            headers=auth_headers,
            files=files
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "records_inserted" in data

    def test_upload_markdown_file(self, client: TestClient, auth_headers: dict):
        """测试上传 Markdown 文件"""
        content = b"# Test Document\n\nThis is a **markdown** test."
        files = {"file": ("test.md", io.BytesIO(content), "text/markdown")}

        response = client.post(
            "/api/v1/knowledge/upload",
            headers=auth_headers,
            files=files
        )

        assert response.status_code == 200

    def test_upload_json_file(self, client: TestClient, auth_headers: dict):
        """测试上传 JSON 文件"""
        content = b'{"title": "Test", "content": "Test content"}'
        files = {"file": ("test.json", io.BytesIO(content), "application/json")}

        response = client.post(
            "/api/v1/knowledge/upload",
            headers=auth_headers,
            files=files
        )

        assert response.status_code == 200

    def test_upload_without_authentication(self, client: TestClient):
        """测试未登录上传文档应该失败"""
        content = b"Test content"
        files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}

        response = client.post(
            "/api/v1/knowledge/upload",
            files=files
        )

        assert response.status_code == 401

    def test_upload_empty_file_fails(self, client: TestClient, auth_headers: dict):
        """测试上传空文件应该失败"""
        content = b""
        files = {"file": ("empty.txt", io.BytesIO(content), "text/plain")}

        response = client.post(
            "/api/v1/knowledge/upload",
            headers=auth_headers,
            files=files
        )

        assert response.status_code == 400

    def test_upload_unsupported_file_format(self, client: TestClient, auth_headers: dict):
        """测试上传不支持的文件格式"""
        content = b"Test content"
        files = {"file": ("test.xyz", io.BytesIO(content), "application/octet-stream")}

        response = client.post(
            "/api/v1/knowledge/upload",
            headers=auth_headers,
            files=files
        )

        assert response.status_code == 400


class TestKnowledgeSearch:
    """知识库搜索功能测试"""

    def test_search_with_results(self, client: TestClient, auth_headers: dict):
        """测试搜索有结果的情况"""
        # 先上传文档
        content = b"Artificial intelligence is transforming the world."
        files = {"file": ("ai.txt", io.BytesIO(content), "text/plain")}
        client.post("/api/v1/knowledge/upload", headers=auth_headers, files=files)

        # 等待向量插入完成
        import time
        time.sleep(1)

        # 搜索
        response = client.post(
            "/api/v1/knowledge/search",
            headers=auth_headers,
            json={"query": "artificial intelligence", "top_k": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    def test_search_without_results(self, client: TestClient, auth_headers: dict):
        """测试搜索无结果的情况"""
        response = client.post(
            "/api/v1/knowledge/search",
            headers=auth_headers,
            json={"query": "xyzabc123notexist", "top_k": 5}
        )

        assert response.status_code == 200
        data = response.json()
        # 无结果时 results 可能为空或长度为0
        assert isinstance(data["results"], list)

    def test_search_without_authentication(self, client: TestClient):
        """测试未登录搜索应该失败"""
        response = client.post(
            "/api/v1/knowledge/search",
            json={"query": "test query", "top_k": 5}
        )

        assert response.status_code == 401

    def test_search_with_invalid_top_k(self, client: TestClient, auth_headers: dict):
        """测试使用无效的 top_k 参数"""
        response = client.post(
            "/api/v1/knowledge/search",
            headers=auth_headers,
            json={"query": "test", "top_k": 100}  # 超过最大限制
        )

        # 应该返回验证错误或限制到最大值
        assert response.status_code in [200, 422]


class TestKnowledgeStats:
    """知识库统计功能测试"""

    def test_get_stats_empty_database(self, client: TestClient, auth_headers: dict):
        """测试获取空数据库的统计信息"""
        response = client.get("/api/v1/knowledge/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "collection_name" in data
        assert "num_entities" in data
        assert "num_files" in data

    def test_get_stats_after_upload(self, client: TestClient, auth_headers: dict):
        """测试上传文档后的统计信息"""
        # 上传文档
        content = b"Test document for statistics."
        files = {"file": ("stats.txt", io.BytesIO(content), "text/plain")}
        client.post("/api/v1/knowledge/upload", headers=auth_headers, files=files)

        # 等待向量插入
        import time
        time.sleep(1)

        # 获取统计
        response = client.get("/api/v1/knowledge/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["num_files"] >= 1

    def test_get_stats_without_auth(self, client: TestClient):
        """测试未登录获取统计应该失败"""
        response = client.get("/api/v1/knowledge/stats")

        assert response.status_code == 401


class TestDocumentList:
    """文档列表功能测试"""

    def test_list_documents(self, client: TestClient, auth_headers: dict):
        """测试列出所有文档"""
        # 先上传几个文档
        for i in range(3):
            content = f"Test document {i}".encode()
            files = {"file": (f"test{i}.txt", io.BytesIO(content), "text/plain")}
            client.post("/api/v1/knowledge/upload", headers=auth_headers, files=files)

        # 等待向量插入
        import time
        time.sleep(1)

        # 获取文档列表
        response = client.get("/api/v1/knowledge/documents", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total_files" in data


class TestDocumentDelete:
    """文档删除功能测试"""

    def test_delete_document_by_id(self, client: TestClient, auth_headers: dict):
        """测试按 ID 删除文档"""
        # 先上传文档获取 ID
        content = b"Document to be deleted."
        files = {"file": ("delete_test.txt", io.BytesIO(content), "text/plain")}
        upload_response = client.post(
            "/api/v1/knowledge/upload",
            headers=auth_headers,
            files=files
        )

        # 注意：当前实现可能不返回文档 ID，这个测试需要根据实际 API 调整
        # 这里只是演示测试结构

    def test_delete_document_without_auth(self, client: TestClient):
        """测试未登录删除文档应该失败"""
        response = client.delete("/api/v1/knowledge/documents/1")

        assert response.status_code == 401
