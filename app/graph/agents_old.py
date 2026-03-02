"""
LangGraph 多智能体系统的 Agent 定义 (完整版，带工具调用)

使用 GLM 原生 Function Calling 实现工具调用
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.chat_models import ChatZhipuAI
from app.config import settings
from app.graph.state import AgentState, SupervisorOutput
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from app.graph.tools import milvus_search_tool, tavily_search_tool
import json


# ============================
# LLM 初始化
# ============================

def create_llm(temperature: float = None):
    """创建 LLM 实例 (使用智谱 GLM)

    Args:
        temperature: 温度参数，控制随机性 (0-1)

    Returns:
        ChatZhipuAI: GLM LLM 实例
    """
    return ChatZhipuAI(
        model=settings.GLM_CHAT_MODEL,
        temperature=temperature or settings.GLM_TEMPERATURE,
        api_key=settings.GLM_API_KEY
    )


# ============================
# Supervisor Agent
# ============================

def create_supervisor_agent() -> callable:
    """创建 Supervisor Agent

    Supervisor 是任务协调员，负责：
    1. 分析用户的请求
    2. 决定下一步调用哪个 Worker Agent (Researcher 或 Writer)
    3. 判断任务是否完成

    Returns:
        callable: Supervisor 节点函数
    """
    llm = create_llm(temperature=0.3)

    # Supervisor 的 Prompt 模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", settings.SUPERVISOR_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])

    # 使用 JsonOutputParser 确保输出 JSON 格式
    chain = prompt | llm | JsonOutputParser()

    def supervisor_node(state: AgentState) -> SupervisorOutput:
        """Supervisor 节点函数"""
        try:
            # 调用 LLM 做决策
            result = chain.invoke(state)

            # 记录决策日志
            print(f"Supervisor 决策: {result}")

            return result

        except Exception as e:
            # 如果 JSON 解析失败，使用备用逻辑
            print(f"JSON 解析失败，使用备用逻辑: {e}")

            messages = state.get("messages", [])
            # 简单规则：根据最后一条消息决定
            if len(messages) <= 2:  # 只有用户消息，调用 Researcher
                return {"next": "Researcher"}
            else:  # 已有研究结果，调用 Writer
                return {"next": "Writer"}

    return supervisor_node


# ============================
# Research Agent (完整版，带工具调用)
# ============================

def create_research_agent(tools=None) -> callable:
    """创建 Research Agent (完整版，支持工具调用)

    Research Agent 是研究专家，负责：
    1. 查询 Milvus 知识库获取相关信息
    2. 使用 Tavily 进行网络搜索
    3. 整理研究结果

    Args:
        tools: 工具列表 (可选，用于兼容)

    Returns:
        callable: Research 节点函数
    """
    # 绑定工具到 LLM (使用 GLM 原生 Function Calling)
    llm = create_llm(temperature=0.5).bind_tools(
        tools=[milvus_search_tool, tavily_search_tool]
    )

    # Research Agent 的 Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", settings.RESEARCHER_SYSTEM_PROMPT + "\n\n你有以下工具可以使用：\n1. milvus_search: 搜索企业知识库\n2. tavily_search: 网络搜索\n\n请根据需要选择合适的工具来收集信息。"),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm

    def research_node(state: AgentState) -> dict:
        """Research 节点函数（支持工具调用）"""
        messages = state["messages"]
        research_data = state.get("research_data", [])

        # 循环处理工具调用（最多 5 次迭代）
        max_iterations = 5
        for iteration in range(max_iterations):
            # 调用 LLM
            response = chain.invoke({"messages": messages})

            # 检查是否有工具调用
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # 有工具调用 - 执行工具
                print(f"Research Agent 调用工具: {[tool['name'] for tool in response.tool_calls]}")

                # 执行每个工具调用
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']

                    # 根据工具名称执行对应的工具
                    if tool_name == "milvus_search":
                        result = milvus_search_tool.invoke(tool_args)
                        print(f"  -> Milvus 搜索完成，返回 {len(result)} 字符")
                    elif tool_name == "tavily_search":
                        result = tavily_search_tool.invoke(tool_args)
                        print(f"  -> Tavily 搜索完成，返回 {len(result)} 字符")
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

                # 继续循环，让 LLM 根据工具结果继续处理
                continue

            else:
                # 没有工具调用 - 完成研究
                print(f"Research Agent 完成研究（迭代 {iteration + 1} 次）")

                # 构造返回消息
                response_message = AIMessage(
                    content=response.content,
                    name="Researcher"
                )

                return {
                    "messages": messages + [response_message],
                    "research_data": research_data
                }

        # 达到最大迭代次数
        print("Research Agent 达到最大迭代次数")

        response_message = AIMessage(
            content="研究过程完成（达到最大迭代次数）",
            name="Researcher"
        )

        return {
            "messages": messages + [response_message],
            "research_data": research_data
        }

    return research_node


# ============================
# Writer Agent
# ============================

def create_writer_agent() -> callable:
    """创建 Writer Agent

    Writer Agent 是写作专家，负责：
    1. 理解 Research Agent 提供的研究结果
    2. 撰写清晰、专业的报告
    3. 确保报告结构完整、逻辑清晰

    Returns:
        callable: Writer 节点函数
    """
    llm = create_llm(temperature=0.7)

    # Writer Agent 的 Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", settings.WRITER_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm

    def writer_node(state: AgentState) -> dict:
        """Writer 节点函数"""
        # 调用 LLM 生成报告
        result = chain.invoke(state)

        # 构造返回消息
        response_message = AIMessage(
            content=result.content,
            name="Writer"
        )

        print(f"Writer Agent 生成报告完成")

        return {
            "messages": [response_message],
            "final_report": result.content
        }

    return writer_node
