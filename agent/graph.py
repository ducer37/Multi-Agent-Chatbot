from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from functools import partial

from agent.nodes import supervisor_node, workspace_agent_node, schedule_agent_node, rag_agent_node, research_agent_node, responder_node
from agent.state import AgentState
from agent.edges import agent_should_continue

from agent.llm import rag_llm, workspace_llm, schedule_llm, research_llm
from agent.schema import AgentResponse

def create_multi_agent_graph(workspace_tools, schedule_tools, rag_tools, research_tools, checkpointer):
    workflow = StateGraph(AgentState)

    rag_agent_llm = rag_llm.bind_tools(rag_tools + [AgentResponse])
    workspace_agent_llm = workspace_llm.bind_tools(workspace_tools + [AgentResponse])
    schedule_agent_llm = schedule_llm.bind_tools(schedule_tools + [AgentResponse])
    research_agent_llm = research_llm.bind_tools(research_tools + [AgentResponse])

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("responder", responder_node)

    workflow.add_node("workspace_agent", partial(workspace_agent_node, llm=workspace_agent_llm))
    workflow.add_node("workspace_tools", ToolNode(workspace_tools))

    workflow.add_node("schedule_agent", partial(schedule_agent_node, llm=schedule_agent_llm))
    workflow.add_node("schedule_tools", ToolNode(schedule_tools))

    workflow.add_node("rag_agent", partial(rag_agent_node, llm=rag_agent_llm))
    workflow.add_node("rag_tools", ToolNode(rag_tools))

    workflow.add_node("research_agent", partial(research_agent_node, llm=research_agent_llm))
    workflow.add_node("research_tools", ToolNode(research_tools))

    workflow.add_edge(START, "supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state["next_agent"],
        {
            "workspace_agent": "workspace_agent",
            "schedule_agent": "schedule_agent",
            "rag_agent": "rag_agent",
            "research_agent": "research_agent",
            "responder": "responder",
            "END": END
        }
    )

    workflow.add_conditional_edges(
        "workspace_agent", agent_should_continue,
        {"continue": "workspace_tools", "supervisor": "supervisor", "responder": "responder"}
    )
    workflow.add_edge("workspace_tools", "workspace_agent")

    workflow.add_conditional_edges(
        "schedule_agent", agent_should_continue,
        {"continue": "schedule_tools", "supervisor": "supervisor", "responder": "responder"}
    )
    workflow.add_edge("schedule_tools", "schedule_agent")

    workflow.add_conditional_edges(
        "rag_agent", agent_should_continue,
        {"continue": "rag_tools", "supervisor": "supervisor", "responder": "responder"}
    )
    workflow.add_edge("rag_tools", "rag_agent")

    workflow.add_conditional_edges(
        "research_agent", agent_should_continue,
        {"continue": "research_tools", "supervisor": "supervisor", "responder": "responder"}
    )
    workflow.add_edge("research_tools", "research_agent")

    workflow.add_edge("responder", END)
    
    return workflow.compile(checkpointer=checkpointer)