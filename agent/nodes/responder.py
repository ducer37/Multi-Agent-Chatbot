from agent.prompts import RESPONDER_PROMPT
from agent.utils import get_trimmed_messages

from agent.llm import responder_llm

async def responder_node(state):
    try:
        print("💬 [Responder] Đang tạo câu trả lời...")
        messages = [{"role": "system", "content": RESPONDER_PROMPT}] + list(state["messages"])
        messages = get_trimmed_messages(messages)
        response = await responder_llm.ainvoke(messages)
        if not response.content or response.content.strip() == "":
            print("❌ [Responder] LỖI: Output của LLM bị trống hoàn toàn.")
            return {"messages": [SystemMessage(content="Xin lỗi, tôi gặp sự cố khi tạo câu trả lời.")]}
        
        print(f"💬 [Responder] → Đã trả lời")
        return {"messages": [response]}
    except Exception as e:
        print(f"❌ [Responder] LỖI API: {str(e)}")
        return {"messages": [SystemMessage(content="Lỗi hệ thống khi tạo phản hồi.")]}