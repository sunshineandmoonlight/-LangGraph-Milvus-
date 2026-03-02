"""
LangGraph 多智能体系统的 Agent 定义

使用 GLM 原生 Function Calling 实现工具调用
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatZhipuAI
from langchain_openai import ChatOpenAI
from app.config import settings
from app.graph.state import AgentState, SupervisorOutput
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from app.graph.tools import milvus_search_tool, tavily_search_tool
import json
import re


# ============================
# LLM 初始化
# ============================

def create_llm(temperature: float = None):
    """创建 LLM 实例

    使用 SiliconFlow DeepSeek-V3 模型（最快且支持 Function Calling）

    Args:
        temperature: 温度参数，控制随机性 (0-1)

    Returns:
        ChatOpenAI: LLM 实例
    """
    if settings.USE_SILICONFLOW:
        print(f"[LLM] 使用 SiliconFlow ({settings.SILICONFLOW_CHAT_MODEL})")
        return ChatOpenAI(
            model=settings.SILICONFLOW_CHAT_MODEL,
            api_key=settings.SILICONFLOW_API_KEY,
            base_url=settings.SILICONFLOW_API_BASE,
            temperature=temperature or settings.SILICONFLOW_TEMPERATURE,
            max_tokens=4096,  # 增加到4096，支持更长回答
            timeout=120,  # 增加到120秒超时
            request_timeout=120
        )
    else:
        # 使用 GLM（备用）
        print(f"[LLM] 使用 GLM ({settings.GLM_CHAT_MODEL})")
        return ChatZhipuAI(
            model=settings.GLM_CHAT_MODEL,
            temperature=temperature or settings.GLM_TEMPERATURE,
            api_key=settings.GLM_API_KEY,
            max_tokens=4096,  # 增加到4096
            timeout=120,
            request_timeout=120
        )


# ============================
# Supervisor Agent
# ============================

def extract_json_from_text(text: str) -> dict:
    """从文本中提取 JSON 对象

    尝试多种方式提取 JSON：
    1. 使用 ast.literal_eval 解析Python字典（支持单引号）
    2. 直接解析标准JSON（双引号）
    3. 将单引号替换为双引号后解析
    4. 使用正则表达式查找 {...} 模式

    Args:
        text: 可能包含 JSON 的文本

    Returns:
        dict: 解析出的 JSON 对象
    """
    import ast

    # 尝试1: 使用 ast.literal_eval 解析整个文本（最优先，支持单引号）
    try:
        result = ast.literal_eval(text.strip())
        if isinstance(result, dict):
            return result
    except (ValueError, SyntaxError):
        pass

    # 尝试2: 直接解析标准JSON
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 尝试3: 查找字典对象并使用 ast.literal_eval 解析
    try:
        # 查找包含 'next' 或 "next" 的字典
        dict_pattern = r'\{[^{}]*["\']next["\'][^{}]*\}'
        matches = re.findall(dict_pattern, text, re.DOTALL)
        if matches:
            # 返回最后一个匹配的字典
            result = ast.literal_eval(matches[-1])
            if isinstance(result, dict):
                return result
    except (ValueError, SyntaxError):
        pass

    # 尝试4: 将单引号替换为双引号后解析
    try:
        text_fixed = text.strip().replace("'", '"')
        return json.loads(text_fixed)
    except json.JSONDecodeError:
        pass

    # 如果都失败了，检查文本是否包含 FINISH
    if 'FINISH' in text.upper():
        return {"next": "FINISH"}

    # 最后返回默认决策
    print(f"警告：无法从文本中提取 JSON: {text[:100]}")
    return {"next": "Researcher"}


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

    # 使用 StrOutputParser，手动解析JSON
    chain = prompt | llm | StrOutputParser()

    def supervisor_node(state: AgentState) -> SupervisorOutput:
        """Supervisor 节点函数"""
        # 获取当前消息历史数量
        msg_count = len(state.get("messages", []))
        print(f"\n[Supervisor] 第 {msg_count} 轮决策开始")

        # 如果已有 final_report，直接完成
        if state.get("final_report"):
            print(f"[Supervisor] 检测到已完成报告，直接 FINISH")
            return {"next": "FINISH"}

        # 调用 LLM 获取响应文本
        response_text = chain.invoke({"messages": state["messages"]})
        print(f"[Supervisor] LLM 输出长度: {len(response_text)}")
        print(f"[Supervisor] LLM 输出前200字符: {response_text[:200]}")

        # 手动解析 JSON
        result = extract_json_from_text(response_text)
        print(f"[Supervisor] 解析结果: {result}")

        # 记录决策日志
        print(f"[Supervisor] 最终决策: {result}")

        # 获取消息列表
        messages = state.get("messages", [])

        # **重要规则1：如果最后一条消息是 Researcher，必须调用 Writer**
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, 'name') and last_msg.name == 'Researcher':
                print(f"[Supervisor] 检测到 Researcher 完成，强制调用 Writer")
                return {"next": "Writer"}

        # 检查 Writer 是否已经生成了报告
        writer_messages = [msg for msg in messages if hasattr(msg, 'name') and msg.name == 'Writer']

        if writer_messages and result.get("next") != "FINISH":
            print(f"[Supervisor] 警告：已有 Writer 消息但未 FINISH，强制 FINISH")
            return {"next": "FINISH"}

        # 简单的循环检测：检查最近的消息是否都是来自同一个Agent
        if len(messages) >= 6:
            # 检查最近6条消息是否都是AI消息（说明在循环）
            recent_ai_count = sum(1 for msg in messages[-6:] if hasattr(msg, 'type') and msg.type == 'ai')
            if recent_ai_count >= 5:
                print(f"[Supervisor] 警告：检测到可能的循环，强制FINISH")
                result = {"next": "FINISH"}

        return result

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
        tools: 工具列表（可选，为了兼容性）

    Returns:
        callable: Research 节点函数
    """
    # 绑定工具到 LLM
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
        """Research 节点函数（直接调用工具）"""
        messages = state["messages"]
        research_data = state.get("research_data", [])

        print(f"[Research] 开始研究")

        # 获取原始用户查询（最后一条人类消息）
        user_query = ""
        for msg in reversed(messages):
            if hasattr(msg, 'type') and msg.type == 'human':
                user_query = msg.content
                break
        print(f"[Research] 用户查询: {user_query[:100]}...")

        # **直接调用 tavily_search**
        print(f"[Research] 主动调用 tavily_search 工具")
        search_result = tavily_search_tool.invoke({"query": user_query})
        research_data.append(search_result)
        print(f"[Research] tavily_search 返回数据长度: {len(str(search_result))}")

        # 返回简短确认消息，而不是整个搜索结果
        # 避免 Supervisor 把搜索结果误当作新的用户查询
        response_message = AIMessage(
            content=f"已完成研究，通过 Tavily 搜索收集到相关信息。",
            name="Researcher"
        )

        print(f"[Research] 研究完成")

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
    # Writer 使用更低的温度和更大的 token 限制，生成详细报告
    if settings.USE_SILICONFLOW:
        print(f"[LLM] Writer 使用 SiliconFlow ({settings.SILICONFLOW_CHAT_MODEL})")
        llm = ChatOpenAI(
            model=settings.SILICONFLOW_CHAT_MODEL,
            api_key=settings.SILICONFLOW_API_KEY,
            base_url=settings.SILICONFLOW_API_BASE,
            temperature=0.5,  # 降低温度，使内容更聚焦
            max_tokens=8192,  # 增加到8192，支持超长报告
            timeout=120,
            request_timeout=120
        )
    else:
        print(f"[LLM] Writer 使用 GLM ({settings.GLM_CHAT_MODEL})")
        from langchain_community.chat_models import ChatZhipuAI
        llm = ChatZhipuAI(
            model=settings.GLM_CHAT_MODEL,
            temperature=0.5,
            api_key=settings.GLM_API_KEY,
            max_tokens=8192,
            timeout=120,
            request_timeout=120
        )

    # Writer Agent 的 Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", settings.WRITER_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm

    def writer_node(state: AgentState) -> dict:
        """Writer 节点函数"""
        # 获取研究数据
        research_data = state.get("research_data", [])

        # 构建包含研究数据的提示
        research_context = ""
        if research_data:
            research_context = f"\n\n# 研究数据\n\n{''.join(research_data)}\n\n"

        # 构建消息：原始消息 + 研究数据
        writer_messages = []
        for msg in state["messages"]:
            writer_messages.append(msg)

        # 添加研究上下文到系统提示
        system_prompt = settings.WRITER_SYSTEM_PROMPT
        if research_context:
            system_prompt += f"\n\n{research_context}"

        # 创建新的消息列表，包含研究数据
        writer_state = {
            "messages": [
                ("system", system_prompt),
                *writer_messages[1:]  # 跳过默认的系统消息
            ]
        }

        # 调用 LLM 生成报告
        result = chain.invoke(writer_state)

        # 构造返回消息
        response_message = AIMessage(
            content=result.content,
            name="Writer"
        )

        # 追加到消息历史
        messages = state.get("messages", [])
        messages = messages + [response_message]

        print(f"Writer Agent 生成报告完成，长度: {len(result.content)} 字符")

        return {
            "messages": messages,
            "final_report": result.content
        }

    return writer_node
