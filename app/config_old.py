"""
应用配置模块
负责管理所有环境变量和应用配置
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类

    使用 Pydantic Settings 进行配置管理
    支持从环境变量、.env 文件自动加载配置
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ============================
    # 应用基础配置
    # ============================
    APP_NAME: str = "Enterprise Multi-Agent System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # ============================
    # 数据库配置
    # ============================
    # PostgreSQL 数据库 URL (异步)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:C20041109@localhost:5432/enterprise_agent"

    # ============================
    # Milvus 向量数据库配置
    # ============================
    # Milvus 服务器地址
    MILVUS_HOST: str = "localhost"
    # Milvus 端口 (默认 19530)
    MILVUS_PORT: int = 19530
    # Milvus Collection 名称
    MILVUS_COLLECTION_NAME: str = "enterprise_knowledge"
    # 向量维度 (GLM Embedding 模型是 1024 维)
    EMBEDDING_DIMENSION: int = 1024
    # 索引类型 (HNSW 是一种高效的近似最近邻索引)
    INDEX_TYPE: str = "HNSW"
    # 相似度度量类型 (IP = Inner Product, L2 = Euclidean Distance)
    METRIC_TYPE: str = "IP"
    # 搜索返回的 Top-K 结果数量
    SEARCH_TOP_K: int = 5

    # ============================
    # Milvus 连接重试配置
    # ============================
    # 最大重试次数
    MILVUS_MAX_RETRIES: int = 5
    # 重试间隔 (秒)
    MILVUS_RETRY_INTERVAL: int = 5
    # 连接超时时间 (秒)
    MILVUS_CONNECTION_TIMEOUT: int = 30

    # ============================
    # GLM (智谱 AI) 配置
    # ============================
    # GLM API Key
    GLM_API_KEY: str = "ff7a0896e39a4288ba9eb4d74572b03c.kGv8pVq3ou2v3II5"
    # 使用的 Embedding 模型
    GLM_EMBEDDING_MODEL: str = "embedding-2"
    # 使用的 Chat 模型
    GLM_CHAT_MODEL: str = "glm-4-flash"
    # Chat 模型温度 (0-1，越低越确定)
    GLM_TEMPERATURE: float = 0.7

    # ============================
    # Tavily 搜索配置
    # ============================
    # Tavily API Key (用于网络搜索)
    TAVILY_API_KEY: str = "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"
    # Tavily 搜索结果最大数量
    TAVILY_MAX_RESULTS: int = 10

    # ============================
    # LangGraph / LangSmith 配置
    # ============================
    # LangChain API Key (用于 LangSmith 追踪)
    LANGCHAIN_API_KEY: Optional[str] = None
    # 是否启用 LangSmith 追踪
    LANGCHAIN_TRACING_V2: bool = True
    # LangSmith 项目名称
    LANGCHAIN_PROJECT: str = "Enterprise-MultiAgent"

    # ============================
    # Agent 配置
    # ============================
    # Supervisor Agent 的系统提示词
    SUPERVISOR_SYSTEM_PROMPT: str = (
        "你是一个智能任务协调员。你负责管理一个研究团队，"
        "包括研究专家和写作专家。你的职责是根据用户需求，"
        "决定下一步应该调用哪个专家来完成任务。\n\n"
        "可用的专家有：\n"
        "- Researcher: 负责信息收集和研究，可以使用知识库搜索和网络搜索\n"
        "- Writer: 负责根据研究结果撰写报告\n\n"
        "请以 JSON 格式返回你的决定，格式为：{{\"next\": \"专家名称\"}}。"
        "如果任务完成，返回 {{\"next\": \"END\"}}。"
    )

    # Research Agent 的系统提示词
    RESEARCHER_SYSTEM_PROMPT: str = (
        "你是一个专业的研究专家。你有以下能力：\n"
        "1. 可以查询企业知识库获取相关信息\n"
        "2. 可以使用网络搜索获取最新信息\n\n"
        "你的任务是全面收集和研究用户提出的问题，"
        "并整理出详细的研究结果供写作专家使用。"
    )

    # Writer Agent 的系统提示词
    WRITER_SYSTEM_PROMPT: str = (
        "你是一个专业的写作专家。你的职责是：\n"
        "1. 理解研究专家提供的研究结果\n"
        "2. 将研究结果整理成清晰、专业、易读的报告\n"
        "3. 确保报告结构完整、逻辑清晰\n\n"
        "请撰写高质量的报告，确保内容准确且有价值。"
    )

    # ============================
    # 日志配置
    # ============================
    # 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_LEVEL: str = "INFO"
    # 日志文件路径
    LOG_FILE: str = "logs/app.log"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例

    使用 lru_cache 确保配置只被创建一次
    这对于性能优化和避免重复连接很有用

    Returns:
        Settings: 应用配置实例
    """
    return Settings()


# 导出配置实例，方便其他模块直接使用
settings = get_settings()
