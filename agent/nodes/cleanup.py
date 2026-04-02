from langchain_core.messages import RemoveMessage

def cleanup_node(state):
    """
    Node này chạy cuối cùng trước khi END.
    1. Trích xuất text từ ToolMessage của RAG nhét vào rag_data.
    2. Xoá vĩnh viễn các ToolMessage và ToolCall khỏi Database.
    """
    messages_to_remove = []
    new_rag_data = {}
    
    for msg in state["messages"]:
        
        if msg.type == "tool":
            new_rag_data[msg.name] = msg.content
            
            messages_to_remove.append(RemoveMessage(id=msg.id))
            
        elif msg.type == "ai" and not msg.content and hasattr(msg, 'tool_calls') and msg.tool_calls:
            messages_to_remove.append(RemoveMessage(id=msg.id))
            
    return {
        "messages": messages_to_remove,
        "rag_data": new_rag_data
    }