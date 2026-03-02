"""
Tavily 搜索工具

封装 Tavily API 用于网络搜索
"""
from tavily import TavilyClient
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from app.config import settings


class TavilySearchInput(BaseModel):
    """Tavily 搜索工具的输入参数"""
    query: str = Field(description="搜索查询，例如: '最新 AI 技术'")
    max_results: int = Field(default=10, description="返回结果数量")


def tavily_search_func(query: str, max_results: int = 10) -> str:
    """Tavily 网络搜索函数

    Args:
        query: 搜索查询
        max_results: 返回结果数量

    Returns:
        str: 搜索结果的文本摘要
    """
    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)

        # 执行搜索
        search_results = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_domains=[],
            exclude_domains=[]
        )

        # 格式化搜索结果
        if not search_results.get("results"):
            return "未找到相关结果。"

        output_lines = []
        for i, result in enumerate(search_results["results"], 1):
            output_lines.append(
                f"【结果 {i}】\n"
                f"标题: {result['title']}\n"
                f"URL: {result['url']}\n"
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
