"""
LangGraph Agent 的工具定义 (简化版)

为 Research Agent 提供工具：
1. Milvus Search Tool: 搜索向量知识库
2. Tavily Search Tool: 网络搜索
"""
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Optional
from app.services.milvus_service import milvus_service
from app.services.embedding_service import get_embedding
from tavily import TavilyClient
from app.config import settings
import json


# ============================
# Milvus 搜索工具
# ============================

class MilvusSearchInput(BaseModel):
    """Milvus 搜索工具的输入参数"""
    query: str = Field(description="搜索查询，例如: '人工智能在医疗领域的应用'")
    top_k: Optional[int] = Field(
        default=5,
        description="返回结果数量，默认 5，最多 20"
    )


def milvus_search_func(query: str, top_k: int = 5) -> str:
    """Milvus 向量搜索函数

    Args:
        query: 搜索查询
        top_k: 返回结果数量

    Returns:
        str: 搜索结果的文本摘要
    """
    try:
        # 1. 将查询文本转换为向量
        query_vector = get_embedding(query)

        # 2. 执行向量搜索
        results = milvus_service.search(
            query_vector=query_vector,
            top_k=min(top_k, 20)
        )

        # 3. 格式化搜索结果
        if not results:
            return "未找到相关文档。"

        output_lines = []
        for i, doc in enumerate(results, 1):
            output_lines.append(
                f"\n【文档 {i}】\n"
                f"相似度: {doc['score']:.4f}\n"
                f"内容: {doc['text'][:500]}...\n"
                f"元数据: {json.dumps(doc['metadata'], ensure_ascii=False)}"
            )

        return "\n".join(output_lines)

    except Exception as e:
        return f"搜索失败: {str(e)}"


# 创建 Milvus 搜索工具
milvus_search_tool = StructuredTool.from_function(
    func=milvus_search_func,
    name="milvus_search",
    description="用于搜索企业知识库的工具。当需要查找企业内部的文档、政策、技术资料时使用此工具。",
    args_schema=MilvusSearchInput
)


# ============================
# Tavily 网络搜索工具
# ============================

class TavilySearchInput(BaseModel):
    """Tavily 搜索工具的输入参数"""
    query: str = Field(description="搜索查询，例如: '最新的 AI 技术趋势'")
    max_results: Optional[int] = Field(
        default=10,
        description="返回结果数量，默认 10"
    )


def tavily_search_func(query: str, max_results: int = 10) -> str:
    """Tavily 网络搜索函数

    Args:
        query: 搜索查询
        max_results: 返回结果数量

    Returns:
        str: 搜索结果的文本摘要
    """
    try:
        # 创建 Tavily 客户端
        tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)

        # 执行搜索
        search_results = tavily_client.search(
            query=query,
            max_results=min(max_results, 10),
            search_depth="advanced",  # 深度搜索
            include_domains=[],
            exclude_domains=[]
        )

        # 格式化搜索结果
        if not search_results.get("results"):
            return "未找到相关结果。"

        output_lines = []
        for i, result in enumerate(search_results["results"], 1):
            # 使用markdown格式的链接：[标题](URL)
            output_lines.append(
                f"\n【结果 {i}】\n"
                f"标题: {result['title']}\n"
                f"链接: [{result['title']}]({result['url']})\n"
                f"内容: {result['content'][:300]}...\n"
            )

        return "\n".join(output_lines)

    except Exception as e:
        return f"搜索失败: {str(e)}"


# 创建 Tavily 搜索工具
tavily_search_tool = StructuredTool.from_function(
    func=tavily_search_func,
    name="tavily_search",
    description="用于搜索互联网的工具。当需要获取最新信息、新闻、数据时使用此工具。",
    args_schema=TavilySearchInput
)


# ============================
# 工具列表
# ============================

def get_research_tools() -> list:
    """获取 Research Agent 可以使用的工具列表

    Returns:
        list: 工具列表
    """
    return [
        milvus_search_tool,
        tavily_search_tool
    ]
