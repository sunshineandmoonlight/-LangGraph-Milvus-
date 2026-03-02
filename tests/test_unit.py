"""
单元测试示例

演示如何对单个函数进行测试
"""
import pytest
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token
)


class TestPasswordHashing:
    """密码加密功能测试"""

    def test_hash_password(self):
        """测试密码哈希生成"""
        password = "my_password_123"
        hashed = get_password_hash(password)

        # 哈希后的密码应该与原密码不同
        assert hashed != password
        # 哈希应该以 $2b$ 开头 (bcrypt 格式)
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self):
        """测试验证正确的密码"""
        password = "my_password_123"
        hashed = get_password_hash(password)

        # 应该返回 True
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """测试验证错误的密码"""
        password = "my_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)

        # 应该返回 False
        assert verify_password(wrong_password, hashed) is False


class TestTokenCreation:
    """JWT Token 生成测试"""

    def test_create_token_with_valid_data(self):
        """测试创建有效的 token"""
        data = {"sub": "123"}
        token = create_access_token(data)

        # Token 应该是字符串
        assert isinstance(token, str)
        # Token 应该包含三个部分 (header.payload.signature)
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_token_with_string_sub(self):
        """测试使用字符串类型的 sub (正确的做法)"""
        data = {"sub": "123"}  # 字符串类型
        token = create_access_token(data)

        # 应该成功创建 token
        assert isinstance(token, str)
        assert len(token) > 0


class TestTextProcessing:
    """文本处理功能测试示例"""

    def test_truncate_text(self):
        """测试文本截断功能"""
        def truncate_text(text: str, max_length: int) -> str:
            """截断文本到指定长度"""
            if len(text) <= max_length:
                return text
            return text[:max_length] + "..."

        # 测试不需要截断的情况
        short_text = "Hello"
        assert truncate_text(short_text, 10) == "Hello"

        # 测试需要截断的情况
        long_text = "This is a very long text that should be truncated"
        result = truncate_text(long_text, 20)
        assert len(result) == 23  # 20 + "..."
        assert result.endswith("...")

    def test_extract_keywords(self):
        """测试关键词提取功能"""
        def extract_keywords(text: str) -> list:
            """从文本中提取关键词（简单实现）"""
            # 移除标点符号并分词
            words = text.lower().replace(".", "").replace(",", "").split()
            # 返回长度大于3的词
            return [w for w in words if len(w) > 3]

        text = "Artificial intelligence is transforming the world."
        keywords = extract_keywords(text)

        assert "artificial" in keywords
        assert "intelligence" in keywords
        assert "transforming" in keywords
        assert "is" not in keywords  # 太短
        assert "the" not in keywords  # 太短


class TestDataValidation:
    """数据验证测试示例"""

    def test_validate_email(self):
        """测试邮箱验证"""
        import re

        def is_valid_email(email: str) -> bool:
            """验证邮箱格式"""
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, email))

        # 有效邮箱
        assert is_valid_email("test@example.com") is True
        assert is_valid_email("user.name@domain.co.uk") is True

        # 无效邮箱
        assert is_valid_email("invalid") is False
        assert is_valid_email("@example.com") is False
        assert is_valid_email("test@") is False

    def test_validate_password_strength(self):
        """测试密码强度验证"""
        def check_password_strength(password: str) -> dict:
            """检查密码强度"""
            result = {
                "valid": len(password) >= 6,
                "has_upper": any(c.isupper() for c in password),
                "has_lower": any(c.islower() for c in password),
                "has_digit": any(c.isdigit() for c in password)
            }
            return result

        # 强密码
        strong = check_password_strength("Pass123")
        assert strong["valid"] is True
        assert strong["has_upper"] is True
        assert strong["has_lower"] is True
        assert strong["has_digit"] is True

        # 弱密码
        weak = check_password_strength("123")
        assert weak["valid"] is False
