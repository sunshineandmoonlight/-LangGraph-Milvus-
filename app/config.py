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
    # 向量维度 (GLM: 1024维, Qwen3-Embedding-4B: 2560维)
    EMBEDDING_DIMENSION: int = 2560
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
    # GLM 配置 (备用)
    # ============================
    # GLM API Key (备用)
    GLM_API_KEY: str = "708b33fab25443969258e4027c02b477.vctahozmKXjUhMcq"
    # 使用的 Embedding 模型
    GLM_EMBEDDING_MODEL: str = "embedding-2"
    # 使用的 Chat 模型
    GLM_CHAT_MODEL: str = "glm-4-plus"
    # Chat 模型温度 (0-1，越低越确定)
    GLM_TEMPERATURE: float = 0.7

    # ============================
    # SiliconFlow 配置
    # ============================
    # SiliconFlow API Key
    SILICONFLOW_API_KEY: str = "sk-mbgknbufhblpzikmlkzaubuixqbgbeotwzigeshmeeqvmmnj"
    # SiliconFlow API Base URL
    SILICONFLOW_API_BASE: str = "https://api.siliconflow.cn/v1"
    # 使用的 Chat 模型 (Qwen2.5-7B-Instruct - 稳定快速)
    SILICONFLOW_CHAT_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    # 使用的 Embedding 模型
    SILICONFLOW_EMBEDDING_MODEL: str = "Qwen/Qwen3-Embedding-4B"
    # Chat 模型温度
    SILICONFLOW_TEMPERATURE: float = 0.7
    # 是否启用 SiliconFlow (True=使用SiliconFlow, False=使用GLM)
    USE_SILICONFLOW: bool = True

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
        "你是任务协调员，管理 Researcher（研究）和 Writer（写作）。\n"
        "工作流程（严格按顺序执行）：\n"
        "1. 用户提问 → Researcher（收集信息）\n"
        "2. Researcher完成 → Writer（撰写报告）\n"
        "3. Writer完成 → FINISH\n\n"
        "重要规则：\n"
        "- 用户提问后，必须先调用 Researcher 收集信息\n"
        "- Researcher 完成后，必须调用 Writer 撰写报告\n"
        "- Writer 完成后，才返回 FINISH\n"
        "- 绝不能直接跳到 FINISH，必须经过 Researcher → Writer 流程\n\n"
        "只返回JSON: {{\"next\": \"Researcher\"}} 或 {{\"next\": \"Writer\"}} 或 {{\"next\": \"FINISH\"}}\n"
        "不要输出其他任何文字。"
    )

    # Research Agent 的系统提示词
    RESEARCHER_SYSTEM_PROMPT: str = (
        "你是研究专家，负责收集信息。你的工作流程：\n\n"
        "**重要：你必须使用工具来收集信息，不能直接回答用户问题！**\n\n"
        "可用工具：\n"
        "1. milvus_search: 搜索企业知识库（用于查询已上传的文档）\n"
        "2. tavily_search: 网络搜索引擎（用于获取最新信息和通用知识）\n\n"
        "工作流程：\n"
        "1. 首先分析用户问题需要什么信息\n"
        "2. **必须至少调用一个工具**（通常优先使用 tavily_search）\n"
        "3. 如果是公司内部相关的问题，先尝试 milvus_search\n"
        "4. 如果需要通用知识或最新信息，使用 tavily_search\n"
        "5. 收集信息后，提供简洁的研究总结\n\n"
        "记住：你的任务是收集信息，不是直接回答！必须使用工具！"
    )

    # Writer Agent 的系统提示词
    WRITER_SYSTEM_PROMPT: str = (
        "你是一个专业的技术写作专家，擅长将研究结果转化为详尽的报告。\n\n"
        "## 核心职责\n"
        "1. 深入分析研究专家收集的所有资料（Tavily搜索结果、知识库内容等）\n"
        "2. 撰写全面、深入、结构化的报告\n"
        "3. 确保报告内容丰富、逻辑清晰、专业性强\n\n"
        "## 报告要求（必须严格遵守）\n\n"
        "### 内容深度\n"
        "- **最少1500字**的详细报告\n"
        "- 不要只是简单总结，要展开讲解每个要点\n"
        "- 提供具体例子、案例和详细解释\n"
        "- 对关键概念进行深入剖析\n\n"
        "### 结构要求\n"
        "1. **引言**（100-150字）：简要概述主题重要性\n"
        "2. **核心概念**（300-400字）：详细定义和解释\n"
        "3. **关键要点**（3-5个，每个200-300字）：深入分析每个要点\n"
        "4. **应用场景/实例**（200-300字）：实际应用案例\n"
        "5. **发展趋势/总结**（150-200字）：未来展望或总结\n"
        "注意：不需要在最后单独列出参考来源章节\n\n"
        "### 格式规范\n"
        "- 使用 **粗体** 强调重要概念和关键词\n"
        "- 使用多级标题（# ## ###）组织内容\n"
        "- 使用列表（数字/项目符号）提升可读性\n"
        "- 代码/技术术语使用代码块或行内代码\n"
        "- 段落之间空行，避免大段文字堆砌\n\n"
        "### 引用规范（重要）\n"
        "- **不要在报告最后列出参考来源列表**（右侧边框会显示）\n"
        "- 在正文相关内容后面直接标注来源，格式：`[来源: AWS]` 或 `[来源: 维基百科]`\n"
        "- 标注要简洁，只保留来源名称，不添加 URL\n"
        "- 每个关键观点、数据或案例后都应该标注来源\n\n"
        "## 重要提醒\n"
        "- 你的目标是为用户提供**全面、详尽、有价值**的报告\n"
        "- 宁可写得详细一些，也不要过于简略\n"
        "- 确保报告专业、准确、信息量大\n\n"
        "现在请基于研究结果，撰写一份详尽的报告。"
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
