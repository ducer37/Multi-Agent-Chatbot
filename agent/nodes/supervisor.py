from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel
from typing import Literal
from agent.prompts import SUPERVISOR_PROMPT
from agent.utils import get_trimmed_messages
from agent.llm import supervisor_llm

class RouteResponse(BaseModel):
    next_agent: Literal["workspace_agent", "schedule_agent", "rag_agent", "FINISH"]

async def supervisor_node(state):
    try:
        last_message = state["messages"][-1]
        if last_message.type == "ai" and not (hasattr(last_message, 'tool_calls') and last_message.tool_calls):
            print("🧠 [Supervisor] Nhân viên đang hỏi user. Kết thúc lượt.")
            return {"next_agent": "FINISH"}

        print("🧠 [Supervisor] Đang phân tích ý định user...")
        prompt = ChatPromptTemplate.from_messages([
            ("system", SUPERVISOR_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ])
        messages = get_trimmed_messages(state["messages"])
        chain = prompt | supervisor_llm.with_structured_output(RouteResponse)
        result = await chain.ainvoke({"messages": messages})
        if not result or not hasattr(result, 'next_agent'):
            print("❌ [Supervisor] LỖI: Không thể phân loại agent tiếp theo.")
            return {"next_agent": "FINISH"}
        print(f"🧠 [Supervisor] → Quyết định: {result.next_agent}")
        return {"next_agent": result.next_agent}
    except Exception as e:
        print(f"❌ [Supervisor] LỖI PHÂN LOẠI: {str(e)}")
        return {"next_agent": "FINISH"}