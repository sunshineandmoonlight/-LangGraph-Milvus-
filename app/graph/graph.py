"""
LangGraph 多智能体图谱定义

构建 Supervisor-Worker 模式的多智能体协作系统
"""
from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.agents import (
    create_supervisor_agent,
    create_research_agent,
    create_writer_agent
)
from app.graph.tools import get_research_tools


def create_multi_agent_graph():
    """创建多智能体协作图谱

    构建流程:
    1. 用户输入 → Supervisor
    2. Supervisor 决定 → Researcher 或 Writer
    3. Researcher 执行 → 返回 Supervisor
    4. Writer 执行 → 返回 Supervisor
    5. Supervisor 判断完成 → END

    Returns:
        StateGraph: 编译后的 LangGraph
    """
    # 创建 StateGraph
    workflow = StateGraph(AgentState)

    # ============================
    # 创建 Agent 节点
    # ============================

    # 1. Supervisor 节点
    supervisor_node = create_supervisor_agent()

    # 2. Research Agent 节点
    research_tools = get_research_tools()
    research_node = create_research_agent(tools=research_tools)

    # 3. Writer Agent 节点
    writer_node = create_writer_agent()

    # ============================
    # 添加节点到图谱
    # ============================

    workflow.add_node("Supervisor", supervisor_node)
    workflow.add_node("Researcher", research_node)
    workflow.add_node("Writer", writer_node)

    # ============================
    # 定义边 (Edges)
    # ============================

    # 设置入口点: 从 Supervisor 开始
    workflow.set_entry_point("Supervisor")

    # 定义条件路由: Supervisor → Researcher/Writer/END
    def route_supervisor(state: AgentState) -> str:
        """根据 Supervisor 的决定路由到下一个节点"""
        next_agent = state.get("next")

        # 如果没有明确的下一步，或者收到 FINISH，则结束
        if not next_agent or next_agent == "FINISH":
            return "END"

        # 只接受有效的节点名称
        if next_agent in ["Researcher", "Writer"]:
            return next_agent

        # 默认情况下结束
        return "END"

    # 添加条件边
    workflow.add_conditional_edges(
        "Supervisor",
        route_supervisor,
        {
            "Researcher": "Researcher",
            "Writer": "Writer",
            "END": END
        }
    )

    # Researcher 完成后返回 Supervisor
    workflow.add_edge("Researcher", "Supervisor")

    # Writer 完成后返回 Supervisor
    workflow.add_edge("Writer", "Supervisor")

    # ============================
    # 编译图谱
    # ============================

    app = workflow.compile()  # 移除 compile_config 参数

    return app


# ============================
# 创建全局 Graph 实例
# ============================

multi_agent_graph = create_multi_agent_graph()


def run_multi_agent(query: str, session_id: str = None, history: list = None) -> dict:
    """运行多智能体系统

    Args:
        query: 用户查询
        session_id: 会话 ID (可选)
        history: 对话历史 (可选)

    Returns:
        dict: 执行结果，包括:
            - final_answer: 最终答案
            - execution_trace: 执行轨迹
            - session_id: 会话 ID
    """
    # 构造初始状态
    from langchain_core.messages import HumanMessage, AIMessage

    # 构建消息列表，包含对话历史
    messages = []

    # 添加历史消息
    if history:
        for msg in history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content")))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg.get("content")))

    # 添加当前查询
    messages.append(HumanMessage(content=query))

    initial_state = {
        "messages": messages,
        "next": "Researcher",  # 从 Researcher 开始
        "research_data": [],
        "final_report": ""
    }

    try:
        # 执行图谱，增加递归限制并添加调试配置
        print(f"[Graph] 开始执行查询: {query}")
        print(f"[Graph] 初始状态: {list(initial_state.keys())}")

        config = {
            "recursion_limit": 20,  # 增加到20
            "debug": False
        }

        result = multi_agent_graph.invoke(initial_state, config)
        print(f"[Graph] 执行完成")

    except Exception as e:
        # 捕获并重新抛出更详细的错误
        import traceback
        error_msg = f"Graph execution failed: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"ERROR: {error_msg}")
        raise Exception(error_msg) from e

    # 提取最终答案
    final_answer = ""
    if result.get("final_report"):
        final_answer = result["final_report"]
    elif result.get("messages"):
        last_message = result["messages"][-1]
        # 检查最后一条消息是否是用户消息（说明Supervisor直接FINISH）
        if hasattr(last_message, 'type') and last_message.type == 'human':
            # Supervisor直接FINISH，没有进行任何研究
            # 使用LLM生成一个友好的回应
            print(f"[Graph] 检测到Supervisor直接FINISH，生成默认回应")
            final_answer = f"您好！关于您的问题「{query}」，我暂时无法找到相关信息。建议您：\n\n1. 检查问题是否清晰明确\n2. 尝试提供更多上下文信息\n3. 或者上传相关文档到知识库后再查询"
        else:
            final_answer = last_message.content

    # 如果最终答案为空，提供默认消息
    if not final_answer or final_answer.strip() == query.strip():
        final_answer = f"关于「{query}」，我暂时没有足够的信息来回答。请尝试上传相关文档到知识库，或者重新组织您的问题。"

    # 构造执行轨迹
    execution_trace = []
    for msg in result.get("messages", []):
        execution_trace.append({
            "role": msg.type if hasattr(msg, 'type') else "unknown",
            "content": msg.content if hasattr(msg, 'content') else str(msg),
            "name": getattr(msg, 'name', 'unknown')
        })

    # 提取参考链接（提取所有搜索结果）
    sources = []
    research_data_list = result.get("research_data", [])

    # 添加调试日志
    print(f"[Graph] research_data 类型: {type(research_data_list)}")
    print(f"[Graph] research_data 长度: {len(research_data_list)}")

    if len(research_data_list) > 0:
        first_item = research_data_list[0]
        print(f"[Graph] research_data[0] 类型: {type(first_item)}")
        print(f"[Graph] research_data[0] 内容前200字符: {str(first_item)[:200]}")

    seen_urls = set()  # 用于去重

    for research_item in research_data_list:
        # 确保转换为字符串
        research_item_str = str(research_item) if not isinstance(research_item, str) else research_item

        # 解析Tavily搜索结果 - 提取所有结果
        if "【结果" in research_item_str and "链接:" in research_item_str:
            # 按结果分割（每个【结果 X】是一个新的搜索结果）
            result_blocks = research_item_str.split("【结果")

            for block in result_blocks:
                if not block.strip():
                    continue

                # 初始化新的source
                source = {"title": "", "url": "", "snippet": "", "source": "", "favicon_url": ""}
                lines = block.split('\n')

                # 用于标记当前正在处理的字段
                current_field = None

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # 检查是否是新的字段开始
                    if line.startswith("标题:"):
                        current_field = "title"
                        title_text = line.split("标题:", 1)[-1].strip()
                        source["title"] = title_text

                    elif line.startswith("链接:"):
                        current_field = "url"
                        url_text = line.split("链接:", 1)[-1].strip()
                        # 移除markdown格式 [url](url)
                        if url_text.startswith("[") and "](" in url_text:
                            # 提取 ]() 中的 URL
                            url_start = url_text.index("](") + 2
                            url_end = url_text.index(")", url_start)
                            url_text = url_text[url_start:url_end]
                        source["url"] = url_text

                        # 从URL提取域名作为来源
                        try:
                            from urllib.parse import urlparse
                            parsed = urlparse(url_text)
                            domain = parsed.netloc  # 例如：www.wikipedia.org
                            # 移除www.前缀
                            if domain.startswith('www.'):
                                domain = domain[4:]
                            source["source"] = domain
                            # 添加favicon URL - 使用 DuckDuckGo（更可靠）
                            source["favicon_url"] = f"https://icons.duckduckgo.com/ip3/{domain}.ico"
                        except:
                            source["source"] = "未知来源"
                            source["favicon_url"] = ""

                    elif line.startswith("内容:"):
                        current_field = "snippet"
                        snippet_text = line.split("内容:", 1)[-1].strip()
                        source["snippet"] = snippet_text

                    # 如果内容跨多行，继续追加到snippet
                    elif current_field == "snippet" and not line.startswith(("标题:", "链接:", "内容:")):
                        source["snippet"] += " " + line

                # 只有当URL存在且未重复时才添加
                if source["url"] and source["url"] not in seen_urls:
                    seen_urls.add(source["url"])
                    sources.append(source)

    # 添加调试日志
    print(f"[Graph] 提取到的 sources 数量: {len(sources)}")
    if len(sources) > 0:
        print(f"[Graph] sources[0]: {sources[0]}")

    # 构建返回结果
    return_result = {
        "final_answer": final_answer,
        "execution_trace": execution_trace,
        "session_id": session_id or "default",
        "sources": sources
    }

    # 验证返回时的 sources
    print(f"[Graph] 返回前再次检查 sources 数量: {len(return_result['sources'])}")
    print(f"[Graph] 返回结果的所有键: {list(return_result.keys())}")

    return return_result


def stream_multi_agent(query: str, session_id: str = None, history: list = None):
    """流式执行多智能体系统

    Args:
        query: 用户查询
        session_id: 会话 ID (可选)
        history: 对话历史 (可选)

    Yields:
        dict: 每一步的执行结果，包含:
            - type: 事件类型 (start, agent_step, progress, complete, error)
            - agent: 当前代理名称
            - message: 进度消息
            - data: 相关数据
    """
    from langchain_core.messages import HumanMessage, AIMessage

    # 构建消息列表，包含对话历史
    messages = []

    # 添加历史消息
    if history:
        for msg in history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content")))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg.get("content")))

    # 添加当前查询
    messages.append(HumanMessage(content=query))

    # 构造初始状态
    initial_state = {
        "messages": messages,
        "next": "Researcher",  # 从 Researcher 开始
        "research_data": [],
        "final_report": ""
    }

    try:
        # 发送开始事件
        yield {
            "type": "start",
            "message": "开始处理您的请求...",
            "data": {"query": query}
        }

        # 流式执行图谱
        step_count = 0
        for event in multi_agent_graph.stream(initial_state, config={"recursion_limit": 50}):
            step_count += 1

            # 解析事件
            for node_name, node_output in event.items():
                if node_name == "__end__":
                    continue

                # 提取当前代理的消息
                if isinstance(node_output, dict):
                    current_messages = node_output.get("messages", [])
                    if current_messages:
                        last_message = current_messages[-1]

                        # 发送进度更新
                        yield {
                            "type": "agent_step",
                            "agent": node_name,
                            "step": step_count,
                            "message": f"[{node_name}] 正在工作...",
                            "data": {
                                "message_type": getattr(last_message, 'type', 'unknown'),
                                "content_preview": str(getattr(last_message, 'content', ''))[:200]
                            }
                        }

                        # 特殊处理：Researcher 完成工具调用
                        if node_name == "Researcher" and node_output.get("research_data"):
                            research_count = len(node_output["research_data"])
                            yield {
                                "type": "progress",
                                "agent": "Researcher",
                                "message": f"✓ Researcher 完成研究，收集了 {research_count} 条信息",
                                "data": {"research_count": research_count}
                            }

                        # 特殊处理：Writer 生成报告
                        if node_name == "Writer" and node_output.get("final_report"):
                            report_preview = node_output["final_report"][:300]
                            yield {
                                "type": "progress",
                                "agent": "Writer",
                                "message": "✓ Writer 正在生成最终报告...",
                                "data": {"report_preview": report_preview}
                            }

        # 发送完成事件
        yield {
            "type": "complete",
            "message": "✅ 处理完成！"
        }

    except Exception as e:
        # 发送错误事件
        import traceback
        yield {
            "type": "error",
            "message": f"❌ 处理出错: {str(e)}",
            "data": {"error": str(e), "traceback": traceback.format_exc()}
        }
