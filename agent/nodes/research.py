from agent.prompts import RESEARCH_PROMPT
from agent.utils import get_trimmed_messages, fallback_llm_invoke, resolve_status, _fallback_status
from langchain_core.messages import SystemMessage, AIMessage

async def research_agent_node(state, llm):
    print("🔬 [Research Agent] Đang xử lý...")
    
    user_id = state.get("user_id", "unknown")
    dynamic_prompt = RESEARCH_PROMPT + f"\n\nLƯU Ý QUAN TRỌNG: ID người dùng hiện tại là `{user_id}`. Truyền chính xác chuỗi `{user_id}` này vào tham số `user_id` khi gọi tool `download_paper_pdf`.\n\nNẾU BẠN CẦN TRẢ LỜI NGƯỜI DÙNG, BẮT BUỘC PHẢI GỌI TOOL `AgentResponse`!"

    messages = [SystemMessage(content=dynamic_prompt)] + list(state["messages"])
    messages = get_trimmed_messages(messages)
    
    response = await fallback_llm_invoke(llm, messages, agent_name="Research Agent")
    response.name = "research_agent"
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        real_tools = [tc for tc in response.tool_calls if tc['name'] != 'AgentResponse']
        agent_responses = [tc for tc in response.tool_calls if tc['name'] == 'AgentResponse']
        
        if real_tools:
            response.tool_calls = real_tools
            status = "PROCESSING"
            tool_names = [tc['name'] for tc in real_tools]
            print(f"🔬 [Research Agent] → Gọi tools: {tool_names}")
        elif agent_responses:
            tc = agent_responses[0]
            msg = tc['args'].get('message', '')
            llm_status = tc['args'].get('status', None)
            # 3-LAYER: Tin LLM structured output + safety net + fallback
            status = resolve_status(llm_status, msg, state["messages"])
            response = AIMessage(content=msg, name="research_agent")
            print(f"🔬 [Research Agent] → Cờ hiệu (3-layer): {status} (LLM chọn: {llm_status})")
    else:
        # Failsafe: LLM trả plain text
        status = _fallback_status(state["messages"])
        print(f"🔬 [Research Agent] → Trả lời trực tiếp (Fallback, status={status})")
        
    return {"messages": [response], "status": status}
