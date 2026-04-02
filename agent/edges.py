def agent_should_continue(state):
    """
    Quyết định của Nhân viên: Đi tiếp sang Tools hay quay về báo cáo Giám đốc.
    """
    last_message = state['messages'][-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print(f"  ⚙️  [Edge] → continue (thực thi tool)")
        return "continue"
    
    print(f"  ⚙️  [Edge] → cleanup")
    return "cleanup"