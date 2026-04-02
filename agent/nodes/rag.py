from agent.prompts import RAG_PROMPT
from agent.utils import get_trimmed_messages
from langchain_core.messages import SystemMessage

async def rag_agent_node(state, llm):
    print("📚 [RAG Agent] Đang xử lý...")
    rag_memory = state.get("rag_data", {})
    context_str = ""
    if rag_memory: 
        context_str = "\n\n📚 TÀI LIỆU BẠN ĐÃ ĐỌC TRƯỚC ĐÓ:\n"
        for doc_id, content in rag_memory.items():
            context_str += f"--- [{doc_id}] ---\n{content}\n\n"
    messages = [SystemMessage(content=RAG_PROMPT + context_str)] + get_trimmed_messages(list(state["messages"]))
    response = await llm.ainvoke(messages)
    if hasattr(response, 'tool_calls') and response.tool_calls:
        tool_names = [tc['name'] for tc in response.tool_calls]
        print(f"📚 [RAG Agent] → Gọi tools: {tool_names}")
    else:
        print(f"📚 [RAG Agent] → Trả lời trực tiếp")
    return {"messages": [response]}
