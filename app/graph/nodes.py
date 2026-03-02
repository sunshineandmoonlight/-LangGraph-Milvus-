"""
LangGraph 多智能体系统的节点定义

简化版本 - 直接实现节点功能
"""
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Dict, List, Any
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from app.config import settings
from app.graph.tools import milvus_search_tool, tavily_search_tool


# ============================
# Research Agent 节点
# ============================

def create_research_agent_node() -> Dict:
    """创建 Research Agent 节点

    直接实现研究功能，支持工具调用

    Returns:
        Dict: 包含节点函数和配置的字典
    """
    # 初始化 LLM
    llm = ChatZhipuAI(
        model=settings.GLM_CHAT_MODEL,
        temperature=0.5,
        api_key=settings.GLM_API_KEY
    ).bind_tools([milvus_search_tool, tavily_search_tool])

    # 定义 Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", settings.RESEARCHER_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm

    def research_node(state: Dict) -> Dict:
        """Research Agent 节点函数"""
        messages = state["messages"]
        research_data = state.get("research_data", [])

        # 循环处理工具调用
        max_iterations = 5
        for iteration in range(max_iterations):
            # 调用 LLM
            response = chain.invoke({"messages": messages})

            # 检查是否有工具调用
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # 执行工具调用
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']

                    # 根据工具名称执行对应的工具
                    if tool_name == "milvus_search_tool":
                        result = milvus_search_tool.invoke(tool_args)
                    elif tool_name == "tavily_search_tool":
                        result = tavily_search_tool.invoke(tool_args)
                    else:
                        result = f"未知工具: {tool_name}"

                    # 添加工具结果到消息列表
                    tool_result_message = ToolMessage(
                        content=result,
                        tool_call_id=tool_call['id'],
                        name=tool_name
                    )
                    messages.append(tool_result_message)

                    # 保存研究数据
                    research_data.append(result)

                # 继续循环
                continue
            else:
                # 没有工具调用 - 完成研究
                response_message = AIMessage(
                    content=response.content,
                    name="Researcher"
                )

                print(f"Research Agent 完成")

                return {
                    "messages": messages + [response_message],
                    "research_data": research_data
                }

        # 达到最大迭代次数
        response_message = AIMessage(
            content="研究过程完成（达到最大迭代次数）",
            name="Researcher"
        )

        return {
            "messages": messages + [response_message],
            "research_data": research_data
        }

    return {"node": research_node}


# ============================
# Writer Agent 节点
# ============================

def create_writer_node() -> Dict:
    """创建 Writer Agent 节点

    一个普通的 LLM 链，负责接收内容并撰写 Markdown 报告

    Returns:
        Dict: 包含节点函数和配置的字典
    """
    # 初始化 LLM
    llm = ChatZhipuAI(
        model=settings.GLM_CHAT_MODEL,
        temperature=0.7,
        api_key=settings.GLM_API_KEY
    )

    # 定义 Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", settings.WRITER_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm

    def writer_node(state: Dict) -> Dict:
        """Writer Agent 节点函数"""
        # 获取消息列表
        messages = state["messages"]

        # 调用 LLM 生成报告
        response = chain.invoke({"messages": messages})

        # 构造返回消息
        response_message = AIMessage(
            content=response.content,
            name="Writer"
        )

        print(f"Writer Agent 完成")

        return {
            "messages": [response_message],
            "final_report": response.content
        }

    return {"node": writer_node}


# ============================
# Supervisor Agent 节点
# ============================

def create_supervisor_node() -> Dict:
    """创建 Supervisor Agent 节点

    Supervisor 是任务协调员，负责决定下一步调用哪个 Agent

    Returns:
        Dict: 包含节点函数和配置的字典
    """
    import json
    import re

    # 初始化 LLM
    llm = ChatZhipuAI(
        model=settings.GLM_CHAT_MODEL,
        temperature=0.3,
        api_key=settings.GLM_API_KEY
    )

    # 定义 Prompt - 强调 JSON 格式
    prompt = ChatPromptTemplate.from_messages([
        ("system", settings.SUPERVISOR_SYSTEM_PROMPT + "\n\n请严格按照以下JSON格式回复，不要包含任何其他内容：\n```json\n{{\"next\": \"Researcher\"}}\n```"),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm

    def supervisor_node(state: Dict) -> Dict:
        """Supervisor 节点函数"""
        # 调用 LLM 做决策
        response = chain.invoke({"messages": state["messages"]})

        # 尝试解析 JSON
        content = response.content

        # 尝试从 markdown 代码块中提取 JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接查找 JSON 对象
            json_match = re.search(r'\{[^{}]*"next"[^{}]*\}', content)
            if json_match:
                json_str = json_match.group(0)
            else:
                # 如果都找不到，使用默认值
                json_str = '{"next": "Researcher"}'

        try:
            result = json.loads(json_str)
        except:
            # 解析失败，使用默认值
            result = {"next": "Researcher"}

        # 记录决策日志
        print(f"Supervisor 决策: {result}")

        return result

    return {"node": supervisor_node}
