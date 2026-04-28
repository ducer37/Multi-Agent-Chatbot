from agent.prompts import SCHEDULE_PROMPT
from langchain_core.messages import SystemMessage, AIMessage
from agent.utils import get_trimmed_messages, fallback_llm_invoke, resolve_status, _fallback_status
from datetime import datetime, timedelta

async def schedule_agent_node(state, llm):
    print("📅 [Schedule Agent] Đang xử lý...")
    
    user_id = state.get("user_id", "unknown")
    
    # Tiêm thời gian thực và Bảng tra cứu lịch vào prompt để LLM không phải tự cộng trừ ngày tháng
    now = datetime.now()
    days_vi = ["Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"]
    
    current_day_name = days_vi[int(now.strftime("%w"))]
    current_time_str = now.strftime(f"Hôm nay là {current_day_name}, ngày %d/%m/%Y, %H:%M")
    
    calendar_context = "BẢNG TRA CỨU LỊCH 8 NGÀY TỚI (Dùng để tra cứu khi User nói 'ngày mai', 'thứ 7', v.v. TUYỆT ĐỐI KHÔNG TỰ CỘNG TRỪ):\n"
    for i in range(8):
        d = now + timedelta(days=i)
        day_name = days_vi[int(d.strftime("%w"))]
        if i == 0:
            day_name += " (Hôm nay)"
        elif i == 1:
            day_name += " (Ngày mai)"
        calendar_context += f"- {day_name}: {d.strftime('%Y-%m-%d')}\n"

    dynamic_prompt = SCHEDULE_PROMPT + f"\n\nLƯU Ý QUAN TRỌNG:\n1. ID người dùng hiện tại là `{user_id}`. BẠN BẮT BUỘC PHẢI truyền chuỗi `{user_id}` này vào tham số `user_id` khi gọi TẤT CẢ các công cụ (kể cả tạo file local hay Google Calendar).\n2. [THỜI GIAN THỰC TẾ]: {current_time_str}.\n{calendar_context}\nNẾU BẠN CẦN TRẢ LỜI NGƯỜI DÙNG HOẶC HỎI THÔNG TIN, BẮT BUỘC PHẢI GỌI TOOL `AgentResponse`!"

    messages = [SystemMessage(content=dynamic_prompt)] + list(state["messages"])
    messages = get_trimmed_messages(messages)
    
    response = await fallback_llm_invoke(llm, messages, agent_name="Schedule Agent")
    response.name = "schedule_agent"
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        real_tools = [tc for tc in response.tool_calls if tc['name'] != 'AgentResponse']
        agent_responses = [tc for tc in response.tool_calls if tc['name'] == 'AgentResponse']
        
        if real_tools:
            response.tool_calls = real_tools
            status = "PROCESSING"
            tool_names = [tc['name'] for tc in real_tools]
            print(f"📅 [Schedule Agent] → Gọi tools: {tool_names} cho user {user_id}")
        elif agent_responses:
            tc = agent_responses[0]
            msg = tc['args'].get('message', '')
            llm_status = tc['args'].get('status', None)
            # 3-LAYER: Tin LLM structured output + safety net + fallback
            status = resolve_status(llm_status, msg, state["messages"])
            response = AIMessage(content=msg, name="schedule_agent")
            print(f"📅 [Schedule Agent] → Cờ hiệu (3-layer): {status} (LLM chọn: {llm_status})")
    else:
        status = _fallback_status(state["messages"])
        print(f"📅 [Schedule Agent] → Trả lời trực tiếp (Fallback, status={status})")
        
    return {"messages": [response], "status": status}
