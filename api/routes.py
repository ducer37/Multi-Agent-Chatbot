from fastapi import APIRouter, Depends, HTTPException, Request
from api.schema import ChatRequest, ChatResponse
from api.dependencies import get_agent
from langchain_core.messages import HumanMessage
from typing import Any

router = APIRouter(prefix="/api/v1", tags=["Chat"])


def _extract_final_answer(result: dict[str, Any]) -> str:
    """Lấy câu trả lời AI cuối cùng một cách an toàn từ graph state."""
    messages = result.get("messages", []) if isinstance(result, dict) else []

    for msg in reversed(messages):
        if getattr(msg, "type", None) != "ai":
            continue

        content = getattr(msg, "content", "")
        if isinstance(content, str) and content.strip():
            return content

        if isinstance(content, list):
            parts = [
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            text = "".join(parts).strip()
            if text:
                return text

    return "Xin lỗi, tôi chưa tạo được câu trả lời phù hợp."

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    req: Request,
    agent = Depends(get_agent)
):
    """
    Endpoint chính để user chat với HUST Agent.
    Sử dụng thread_id để duy trì ngữ cảnh hội thoại bền vững trong cơ sở dữ liệu PostgreSQL.
    """
    try:
        config = {"configurable": {"thread_id": request.thread_id}, "recursion_limit": 25}
        
        user_id = request.user_id if request.user_id else request.thread_id
        
        # Auto-inject: lấy tool descriptions đã build lúc startup
        tool_desc = getattr(req.app.state, 'tool_descriptions', '')
        
        input_data = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": user_id,
            "tool_descriptions": tool_desc
        }
        
        result = await agent.ainvoke(input_data, config=config)
        final_message = _extract_final_answer(result)
        

        affected_files = []
        
        return ChatResponse(
            answer=final_message,
            files_affected=affected_files,
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống Agent: {str(e)}")

@router.get("/status")
async def get_status():
    """Kiểm tra xem hệ thống có đang 'sống' không."""
    return {"status": "online", "message": "HUST Agent sẵn sàng phục vụ ducer!"}