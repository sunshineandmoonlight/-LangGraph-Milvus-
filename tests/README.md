# 测试模块说明

本目录包含项目的所有测试代码，包括单元测试、集成测试和端到端测试。

## 目录结构

```
tests/
├── __init__.py          # 包初始化文件
├── conftest.py          # Pytest 配置和 fixtures
├── test_unit.py         # 单元测试示例
├── test_auth.py         # 认证模块集成测试
├── test_knowledge.py    # 知识库模块集成测试
├── test_agent.py        # Agent 模块集成测试
└── test_e2e.py          # 端到端测试
```

## 安装测试依赖

```bash
pip install -r requirements-test.txt
```

## 运行测试

### 运行所有测试
```bash
pytest
```

### 运行特定类型的测试
```bash
# 只运行单元测试
pytest tests/test_unit.py

# 只运行集成测试
pytest tests/test_auth.py tests/test_knowledge.py tests/test_agent.py

# 只运行端到端测试
pytest tests/test_e2e.py
```

### 运行特定测试类或函数
```bash
# 运行特定测试类
pytest tests/test_auth.py::TestUserRegistration

# 运行特定测试函数
pytest tests/test_auth.py::TestUserRegistration::test_register_new_user_successfully
```

### 使用标记运行
```bash
# 只运行认证相关测试
pytest -m auth

# 只运行知识库相关测试
pytest -m knowledge

# 排除慢速测试
pytest -m "not slow"
```

### 生成测试报告
```bash
# 生成 HTML 覆盖率报告
pytest --cov=app --cov-report=html

# 生成详细报告
pytest -v --tb=long
```

## 测试类型说明

### 1. 单元测试 (test_unit.py)
对单个函数或类进行测试，不依赖外部系统。

**示例**:
```python
def test_add_positive_numbers():
    result = add(2, 3)
    assert result == 5
```

### 2. 集成测试 (test_auth.py, test_knowledge.py, test_agent.py)
测试多个模块协同工作，可能涉及数据库。

**示例**:
```python
def test_user_registration_flow():
    response = client.post("/api/v1/auth/register", json={...})
    assert response.status_code == 200
```

### 3. 端到端测试 (test_e2e.py)
模拟真实用户场景的完整流程。

**示例**:
```python
def test_complete_new_user_workflow():
    # 1. 注册
    # 2. 登录
    # 3. 上传文档
    # 4. 提问
    # 5. 验证结果
```

## Fixtures 说明

测试文件中使用了以下 fixtures（在 conftest.py 中定义）：

| Fixture | 说明 |
|---------|------|
| `db_session` | 测试数据库会话（每个测试独立） |
| `client` | FastAPI 测试客户端 |
| `test_user` | 创建测试用户 |
| `test_user_token` | 测试用户的 JWT token |
| `auth_headers` | 带认证的请求头 |
| `temp_file` | 临时文件 |

## 添加新测试

1. **确定测试类型**：单元测试、集成测试还是端到端测试

2. **创建测试文件**：
   ```python
   # tests/test_new_feature.py

   def test_new_feature():
       assert True
   ```

3. **使用 fixtures**：
   ```python
   def test_with_client(client: TestClient, auth_headers: dict):
       response = client.get("/api/v1/endpoint", headers=auth_headers)
       assert response.status_code == 200
   ```

4. **运行测试验证**：
   ```bash
   pytest tests/test_new_feature.py
   ```

## 注意事项

1. **测试独立性**：每个测试应该独立运行，不依赖其他测试
2. **清理数据**：测试结束后自动清理（使用 fixtures）
3. **Mock 外部服务**：对于真实 API 调用，考虑使用 mock
4. **测试命名**：使用描述性的名称，如 `test_register_with_duplicate_email_fails`

## 常见问题

### Q: 测试失败，提示数据库连接错误
A: 确保 Milvus 和 PostgreSQL 正在运行，或使用 Mock

### Q: 某些测试需要真实的 API Key
A: 在 `.env` 文件中配置，或跳过需要真实 API 的测试

### Q: 测试太慢
A: 使用 `-m "not slow"` 跳过慢速测试，或并行运行测试 `pytest -n auto`
