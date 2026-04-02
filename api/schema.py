from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    """Khuôn mẫu dữ liệu gửi từ Client lên Server."""
    message: str = Field(
        ..., 
        description="Câu lệnh hoặc câu hỏi của ducer gửi cho Agent",
        example="Đặt lịch học môn Giải tích sáng thứ 4"
    )
    thread_id: str = Field(
        default="hust_default_session",
        description="ID phiên chat để AI ghi nhớ ngữ cảnh (In-memory)",
        example="ducer_session_101"
    )

class ChatResponse(BaseModel):
    """Khuôn mẫu dữ liệu Server trả về cho Client."""
    answer: str = Field(
        ..., 
        description="Câu trả lời cuối cùng của AI sau khi xử lý logic"
    )
    files_affected: List[str] = Field(
        default=[], 
        description="Danh sách các file đã được tạo hoặc tác động trong workspace",
        example=["lich_hoc_Giai_tich.txt"]
    )
    status: str = Field(
        default="success",
        description="Trạng thái của yêu cầu (success/error)"
    )