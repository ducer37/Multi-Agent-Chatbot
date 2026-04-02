from agent.prompts import WORKSPACE_PROMPT
from langchain_core.messages import SystemMessage
from agent.utils import get_trimmed_messages

async def workspace_agent_node(state, llm):
    print("📁 [Workspace Agent] Đang xử lý...")
    messages = [SystemMessage(content=WORKSPACE_PROMPT)] + list(state["messages"])
    messages = get_trimmed_messages(messages)
    response = await llm.ainvoke(messages)
    if hasattr(response, 'tool_calls') and response.tool_calls:
        tool_names = [tc['name'] for tc in response.tool_calls]
        print(f"📁 [Workspace Agent] → Gọi tools: {tool_names}")
    else:
        print(f"📁 [Workspace Agent] → Trả lời trực tiếp")
    return {"messages": [response]}
