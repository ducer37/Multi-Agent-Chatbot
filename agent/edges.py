def agent_should_continue(state):
    """
    Định tuyến dựa trên Cờ hiệu (State Flags) thay vì đoán mò.
    """
    status = state.get("status", "")
    
    if status == "WAITING_FOR_USER":
        print(f"  ⚙️  [Edge] → responder (Human-in-the-loop: Chờ User trả lời)")
        return "responder"
        
    elif status == "DONE":
        print(f"  ⚙️  [Edge] → supervisor (Hoàn thành task, kiểm tra task tiếp theo)")
        return "supervisor"
        
    # Xử lý fallback cho các Tool thực sự
    last_message = state['messages'][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print(f"  ⚙️  [Edge] → continue (thực thi tool)")
        return "continue"
    
    print(f"  ⚙️  [Edge] → supervisor (Failsafe)")
    return "supervisor"