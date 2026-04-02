from fastapi import APIRouter, Depends, HTTPException
from api.schema import ChatRequest, ChatResponse
from api.dependencies import get_agent
from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/api/v1", tags=["Chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    agent = Depends(get_agent)
):
    """
    Endpoint chính để user chat với HUST Agent.
    Sử dụng thread_id để duy trì ngữ cảnh hội thoại bền vững trong cơ sở dữ liệu PostgreSQL.
    """
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        
        input_data = {"messages": [HumanMessage(content=request.message)]}
        
        result = await agent.ainvoke(input_data, config=config)
        
        final_message = result["messages"][-1].content
        

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