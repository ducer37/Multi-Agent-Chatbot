from langchain_core.messages import trim_messages, AIMessage

def get_trimmed_messages(messages):
    return trim_messages(
        messages,
        max_tokens=40,          # Giữ tối đa 40 messages gần nhất (~13 vòng tool call)
        token_counter=len,      # len = đếm số lượng message, KHÔNG phải số token
        include_system=True,
        strategy="last", 
        start_on="human",
        allow_partial=False 
    )


def resolve_status(llm_status: str | None, message_content: str, state_messages: list) -> str:
    """
    3-LAYER STATUS RESOLUTION — Triệt để, luôn đúng.
    
    Layer 1 (Primary)   : AgentResponse.status → Structured output, tin cậy cao nhất
    Layer 2 (Safety Net): Content analysis     → Bắt lỗi LLM (nói DONE nhưng đang hỏi)
    Layer 3 (Fallback)  : Message history scan → Khi LLM không gọi AgentResponse
    """
    
    # ── Layer 1 + 2: Có AgentResponse → tin LLM, nhưng kiểm tra safety net ──
    if llm_status:
        content = message_content.strip()
        
        # Safety net: LLM nói DONE nhưng nội dung là câu hỏi VÀ chưa có tool result nào
        # → Agent đang hỏi thông tin chứ chưa làm gì → override sang WAITING_FOR_USER
        # Nhưng nếu ĐÃ CÓ tool result → "?" chỉ là phép lịch sự sau khi hoàn thành → giữ DONE
        if llm_status == "DONE" and content.endswith("?"):
            has_tool_result = any(m.type == "tool" for m in state_messages[-10:])
            if not has_tool_result:
                print(f"  🛡️ [Safety Net] LLM nói DONE nhưng đang hỏi và CHƯA có tool result → Override sang WAITING_FOR_USER")
                return "WAITING_FOR_USER"
            else:
                print(f"  ✅ [Safety Net] LLM nói DONE, có '?' nhưng ĐÃ CÓ tool result → Giữ DONE (câu hỏi lịch sự)")
        
        return llm_status
    
    # ── Layer 3: Không có AgentResponse → fallback heuristic ──
    return _fallback_status(state_messages)


def _fallback_status(state_messages: list) -> str:
    """
    Fallback: Quét message history khi LLM không gọi AgentResponse.
    Chỉ dùng cho edge case (LLM trả plain text).
    """
    for msg in reversed(state_messages[-15:]):
        if msg.type == "tool":
            return "DONE"
        if msg.type == "human":
            return "WAITING_FOR_USER"
    
    return "WAITING_FOR_USER"


async def fallback_llm_invoke(llm, messages, agent_name="Agent"):
    """
    Enterprise-grade LLM wrapper:
    1. Thử gọi LLM chính
    2. Nếu lỗi XML tool_use_failed → parse bằng regex + balanced-brace
    3. Nếu parse cũng fail → retry 1 lần với model nhẹ hơn
    """
    # === Lần 1: Gọi LLM chính ===
    try:
        return await llm.ainvoke(messages)
    except Exception as e:
        error_str = str(e)
        if "failed_generation" not in error_str or "<function=" not in error_str:
            raise e
        
        print(f"⚠️ [{agent_name}] Kích hoạt Fallback Parser...")
        parsed = _parse_xml_function_calls(error_str)
        
        if parsed:
            tool_names = [tc['name'] for tc in parsed]
            print(f"✅ [{agent_name}] Fallback phục hồi: {tool_names}")
            return AIMessage(content="", tool_calls=parsed)
        
        # === Lần 2: Retry 1 lần ===
        print(f"🔄 [{agent_name}] Fallback parse thất bại, thử retry...")
        try:
            return await llm.ainvoke(messages)
        except Exception as retry_e:
            retry_error = str(retry_e)
            if "failed_generation" in retry_error and "<function=" in retry_error:
                parsed_retry = _parse_xml_function_calls(retry_error)
                if parsed_retry:
                    tool_names = [tc['name'] for tc in parsed_retry]
                    print(f"✅ [{agent_name}] Retry + Fallback phục hồi: {tool_names}")
                    return AIMessage(content="", tool_calls=parsed_retry)
            
            print(f"❌ [{agent_name}] Retry thất bại, re-raise lỗi gốc.")
            raise e


def _parse_xml_function_calls(error_str: str) -> list[dict] | None:
    """
    Parse tất cả <function=name>{json}</function> từ error string.
    Hỗ trợ nested JSON bằng balanced-brace algorithm.
    """
    import re
    import json
    import uuid
    
    pattern = r"<function=([a-zA-Z0-9_]+)>?\s*(\{.*?\})\s*</function>"
    matches = re.findall(pattern, error_str, re.DOTALL)
    
    if not matches:
        return None
    
    tool_calls = []
    for func_name, func_args_str in matches:
        try:
            args = json.loads(func_args_str)
        except json.JSONDecodeError:
            # Regex non-greedy cắt sai nested JSON → dùng balanced-brace
            args = _extract_balanced_json(error_str, func_name)
            if args is None:
                continue
        
        tool_calls.append({
            "name": func_name,
            "args": args,
            "id": f"call_fb_{uuid.uuid4().hex[:8]}"
        })
    
    return tool_calls if tool_calls else None


def _extract_balanced_json(text: str, func_name: str) -> dict | None:
    """
    Trích xuất JSON cân bằng ngoặc {} từ text.
    Xử lý nested JSON (VD: {"event": {"title": "Toán"}})
    mà regex đơn giản không bắt được.
    """
    import json
    
    marker = f"<function={func_name}"
    start_search = text.find(marker)
    if start_search == -1:
        return None
    
    brace_start = text.find("{", start_search)
    if brace_start == -1:
        return None
    
    depth = 0
    in_string = False
    escape = False
    
    for i in range(brace_start, len(text)):
        char = text[i]
        
        if escape:
            escape = False
            continue
        if char == '\\':
            escape = True
            continue
        if char == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                json_str = text[brace_start:i + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    return None
    
    return None
