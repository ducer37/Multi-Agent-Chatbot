from agent.prompts import SCHEDULE_PROMPT
from langchain_core.messages import SystemMessage
from agent.utils import get_trimmed_messages

async def schedule_agent_node(state, llm):
    print("📅 [Schedule Agent] Đang xử lý...")
    messages = [SystemMessage(content=SCHEDULE_PROMPT)] + list(state["messages"])
    messages = get_trimmed_messages(messages)
    response = await llm.ainvoke(messages)
    if hasattr(response, 'tool_calls') and response.tool_calls:
        tool_names = [tc['name'] for tc in response.tool_calls]
        print(f"📅 [Schedule Agent] → Gọi tools: {tool_names}")
    else:
        print(f"📅 [Schedule Agent] → Trả lời trực tiếp")
    return {"messages": [response]}
