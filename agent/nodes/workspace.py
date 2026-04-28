from agent.prompts import WORKSPACE_PROMPT
from langchain_core.messages import SystemMessage, AIMessage
from agent.utils import get_trimmed_messages, fallback_llm_invoke, resolve_status, _fallback_status

async def workspace_agent_node(state, llm):
    print("📁 [Workspace Agent] Đang xử lý...")
    
    user_id = state.get("user_id", "unknown")
    dynamic_prompt = WORKSPACE_PROMPT + f"\n\nLƯU Ý QUAN TRỌNG: ID người dùng hiện tại của bạn là `{user_id}`. BẠN BẮT BUỘC PHẢI truyền chính xác chuỗi `{user_id}` này vào tham số `user_id` khi gọi BẤT KỲ CÔNG CỤ NÀO (kể cả thao tác file local hay Google Drive).\n\nNẾU BẠN CẦN TRẢ LỜI NGƯỜI DÙNG, BẮT BUỘC PHẢI GỌI TOOL `AgentResponse`!"

    messages = [SystemMessage(content=dynamic_prompt)] + list(state["messages"])
    messages = get_trimmed_messages(messages)
    
    response = await fallback_llm_invoke(llm, messages, agent_name="Workspace Agent")
    response.name = "workspace_agent"
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        real_tools = [tc for tc in response.tool_calls if tc['name'] != 'AgentResponse']
        agent_responses = [tc for tc in response.tool_calls if tc['name'] == 'AgentResponse']
        
        if real_tools:
            response.tool_calls = real_tools
            status = "PROCESSING"
            tool_names = [tc['name'] for tc in real_tools]
            print(f"📁 [Workspace Agent] → Gọi tools: {tool_names} cho user {user_id}")
        elif agent_responses:
            tc = agent_responses[0]
            msg = tc['args'].get('message', '')
            llm_status = tc['args'].get('status', None)
            # 3-LAYER: Tin LLM structured output + safety net + fallback
            status = resolve_status(llm_status, msg, state["messages"])
            response = AIMessage(content=msg, name="workspace_agent")
            print(f"📁 [Workspace Agent] → Cờ hiệu (3-layer): {status} (LLM chọn: {llm_status})")
    else:
        status = _fallback_status(state["messages"])
        print(f"📁 [Workspace Agent] → Trả lời trực tiếp (Fallback, status={status})")
        
    return {"messages": [response], "status": status}
