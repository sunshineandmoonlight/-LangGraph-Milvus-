"""
LangGraph 多智能体系统的状态定义

定义了 Agent 之间传递的数据结构，包括：
1. AgentState: 智能体之间的共享状态
2. Agent 节点的输入输出类型
"""
from typing import TypedDict, Annotated, Sequence, List, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import add_messages
import operator


class AgentState(TypedDict):
    """Agent 之间的共享状态

    这个状态会在多个 Agent 之间传递，每个 Agent 可以读取和更新状态

    字段说明:
        messages: 消息历史，使用 add_messages 函数进行合并
                 (Annotated 表示使用特殊的合并函数)
        next: 下一个要执行的 Agent 名称
              (可以是 "Researcher", "Writer", 或 "END")
        research_data: Research Agent 收集的数据
        final_report: Writer Agent 生成的最终报告
    """

    # 消息历史 (使用 add_messages 函数合并消息)
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # 下一个要调用的 Agent
    next: Literal["Researcher", "Writer", "END"]

    # Research Agent 收集的研究数据
    research_data: List[str]

    # Writer Agent 生成的最终报告
    final_report: str


class ResearchAgentInput(TypedDict):
    """Research Agent 的输入"""
    messages: Sequence[BaseMessage]


class ResearchAgentOutput(TypedDict):
    """Research Agent 的输出"""
    messages: Sequence[BaseMessage]
    research_data: List[str]


class SupervisorOutput(TypedDict):
    """Supervisor 的输出"""
    next: Literal["Researcher", "Writer", "END"]
    reasoning: str  # 决策推理过程
