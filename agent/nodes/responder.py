from agent.prompts import RESPONDER_PROMPT
from agent.utils import get_trimmed_messages
from langchain_core.messages import AIMessage, SystemMessage

from agent.llm import responder_llm

async def responder_node(state):
    try:
        print("💬 [Responder] Đang tạo câu trả lời...")
        
        status = state.get("status", "")
        
        # Auto-inject tool capabilities từ state (nếu có)
        tool_info = state.get("tool_descriptions", "")
        prompt = RESPONDER_PROMPT
        if tool_info:
            prompt += f"\n\nDANH SÁCH TOOLS THỰC TẾ CỦA HỆ THỐNG:\n{tool_info}"
        
        messages = [SystemMessage(content=prompt)] + list(state["messages"])
        
        # Xử lý khác nhau dựa trên status
        if messages and messages[-1].type == "ai":
            if status == "WAITING_FOR_USER":
                # Agent đang hỏi thêm info → CHUYỂN TIẾP câu hỏi, KHÔNG viết lại
                messages.append(SystemMessage(
                    content="[HƯỚNG DẪN] Nhân viên vừa hỏi người dùng một câu hỏi. "
                            "Hãy CHUYỂN TIẾP NGUYÊN VĂN câu hỏi đó cho user bằng giọng thân thiện. "
                            "KHÔNG tự trả lời, KHÔNG tổng hợp, KHÔNG thêm thông tin."
                ))
            else:
                # Agent đã xong → tổng hợp kết quả
                messages.append(SystemMessage(
                    content="[HƯỚNG DẪN] Dựa vào các kết quả từ nhân viên vừa rồi, hãy tổng hợp và trả lời câu hỏi gốc của người dùng."
                ))
        
        messages = get_trimmed_messages(messages)
            
        response = await responder_llm.ainvoke(messages)
        if not response.content or response.content.strip() == "":
            print("❌ [Responder] LỖI: Output của LLM bị trống hoàn toàn.")
            return {"messages": [AIMessage(content="Xin lỗi, tôi gặp sự cố khi tạo câu trả lời.")]}
        
        print(f"💬 [Responder] → Đã trả lời (mode: {'relay' if status == 'WAITING_FOR_USER' else 'summarize'})")
        return {"messages": [response]}
    except Exception as e:
        print(f"❌ [Responder] LỖI API: {str(e)}")
        return {"messages": [AIMessage(content="Xin lỗi, hệ thống đang gặp sự cố. Vui lòng thử lại sau.")]}