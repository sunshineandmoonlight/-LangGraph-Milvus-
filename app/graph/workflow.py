"""
LangGraph 多智能体工作流定义

使用 StateGraph 将节点连接起来，并编译成可运行的 app
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from app.config import settings
from app.graph.state import AgentState
from app.graph.nodes import (
    create_research_agent_node,
    create_writer_node,
    create_supervisor_node
)


def create_multi_agent_workflow(checkpointer=None):
    """创建多智能体工作流

    构建 Supervisor-Worker 模式的协作流程

    Args:
        checkpointer: Checkpointer 实例 (可选，用于对话历史)

    Returns:
        StateGraph: 编译后的 LangGraph
    """
    # 创建 StateGraph
    workflow = StateGraph(AgentState)

    # 添加节点到图谱
    supervisor_node = create_supervisor_node()
    research_node = create_research_agent_node()
    writer_node = create_writer_node()

    workflow.add_node("Supervisor", supervisor_node["node"])
    workflow.add_node("Researcher", research_node["node"])
    workflow.add_node("Writer", writer_node["node"])

    # 设置入口点: 从 Supervisor 开始
    workflow.set_entry_point("Supervisor")

    # 定义条件路由: Supervisor → Researcher/Writer/END
    def route_supervisor(state: AgentState) -> str:
        """根据 Supervisor 的决策路由到下一个节点"""
        next_node = state.get("next", "END")
        return next_node

    # 添加条件边
    workflow.add_conditional_edges(
        "Supervisor",
        route_supervisor,
        {
            "Researcher": "Researcher",
            "Writer": "Writer",
            "FINISH": END
        }
    )

    # Researcher 和 Writer 完成后返回 Supervisor
    workflow.add_edge("Researcher", "Supervisor")
    workflow.add_edge("Writer", "Supervisor")

    # 编译图谱
    if checkpointer:
        # 如果提供了 checkpointer，添加对话历史功能
        workflow = workflow.compile(checkpointer=checkpointer)
    else:
        # 如果没有 checkpoint，直接编译
        workflow = workflow.compile()

    return workflow


def get_postgres_checkpointer():
    """获取 PostgreSQL Checkpointer

    Returns:
        PostgresSaver: PostgreSQL checkpointer 实例 (需要作为上下文管理器使用)
    """
    return PostgresSaver.from_conn_string(settings.DATABASE_URL)


# ============================
# 创建全局 Workflow 实例
# ============================

# 使用无 checkpoint 的版本（因为 checkpoint 需要异步上下文）
multi_agent_workflow = create_multi_agent_workflow()
print("使用无 checkpoint 模式 (checkpoint 需要在异步上下文中使用)")


def run_multi_agent(query: str, session_id: str = None) -> dict:
    """运行多智能体系统

    Args:
        query: 用户查询
        session_id: 会话 ID (可选)

    Returns:
        dict: 执行结果，包括:
            - final_answer: 最终答案
            - execution_trace: 执行轨迹
            - session_id: 会话 ID
    """
    from langchain_core.messages import HumanMessage

    # 构造初始状态
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "next": "Supervisor",
        "research_data": [],
        "final_report": ""
    }

    # 构造配置
    config = {}
    if session_id:
        config["configurable"] = {"thread_id": session_id}

    # 执行图谱
    result = multi_agent_workflow.invoke(initial_state, config)

    # 提取最终答案
    final_answer = ""
    if result.get("final_report"):
        final_answer = result["final_report"]
    elif result.get("messages"):
        final_answer = result["messages"][-1].content

    # 构造执行轨迹
    execution_trace = []
    for msg in result.get("messages", []):
        execution_trace.append({
            "role": msg.type if hasattr(msg, 'type') else "unknown",
            "name": getattr(msg, 'name', 'unknown'),
            "content": msg.content if hasattr(msg, 'content') else str(msg)
        })

    return {
        "final_answer": final_answer,
        "execution_trace": execution_trace,
        "session_id": session_id or "default"
    }


def stream_multi_agent(query: str, session_id: str = None):
    """流式执行多智能体系统

    Args:
        query: 用户查询
        session_id: 会话 ID (可选)

    Yields:
        dict: 每一步的执行结果
    """
    from langchain_core.messages import HumanMessage

    # 构造初始状态
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "next": "Supervisor",
        "research_data": [],
        "final_report": ""
    }

    # 构造配置
    config = {}
    if session_id:
        config["configurable"] = {"thread_id": session_id}

    # 流式执行图谱
    for event in multi_agent_workflow.stream(initial_state, config):
        yield event
