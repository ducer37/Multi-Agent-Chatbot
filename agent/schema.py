from pydantic import BaseModel, Field
from typing import Literal, Optional

class AgentResponse(BaseModel):
    """Sử dụng công cụ này ĐỂ TRẢ LỜI NGƯỜI DÙNG khi bạn không cần gọi các công cụ (tools) khác nữa.
    Ví dụ: khi bạn cần hỏi thêm thông tin, hoặc khi bạn đã hoàn thành nhiệm vụ và muốn trả kết quả."""
    message: str = Field(description="Nội dung câu trả lời hoặc câu hỏi gửi cho người dùng. PHẢI dùng tiếng Việt thân thiện.")
    status: Literal["WAITING_FOR_USER", "DONE"] = Field(description="Chọn 'WAITING_FOR_USER' nếu bạn ĐANG ĐẶT CÂU HỎI và cần người dùng cung cấp thêm thông tin. Chọn 'DONE' nếu bạn đã hoàn thành câu trả lời và không cần hỏi thêm gì.")

# Nhóm 1: Lịch Sự kiện (Học, Họp, Khám bệnh, Hẹn hò...)
class EventSchedule(BaseModel):
    activity_type: str = Field(description="Loại sự kiện")
    title: str = Field(description="Tiêu đề")
    date: str = Field(description="Ngày diễn ra")
    time: str = Field(description="Giờ bắt đầu")
    location: str = Field(description="Địa điểm")
    repeat_weeks: Optional[int] = Field(
        description="Số tuần lặp lại nếu lịch cố định hàng tuần. VD: 15 = lặp 15 tuần. Bỏ trống = chỉ 1 buổi.",
        default=None
    )

# Nhóm 2: Lịch Di chuyển (Máy bay, Tàu hỏa, Xe khách...)
class TravelSchedule(BaseModel):
    transport_type: str = Field(description="Loại phương tiện")
    departure: str = Field(description="Điểm đi")
    destination: str = Field(description="Điểm đến")
    date: str = Field(description="Ngày đi")
    time: Optional[str] = Field(description="Giờ khởi hành", default="Chưa rõ")

# Nhóm 3: Lịch Dạy Gia sư
class TeachingSchedule(BaseModel):
    title: str = Field(description="Tên môn dạy (VD: 'Toán lớp 10', 'Tiếng Anh IELTS')")
    student_name: str = Field(description="Tên học sinh hoặc nhóm học sinh", default="Chưa rõ")
    date: str = Field(description="Ngày bắt đầu dạy (YYYY-MM-DD)")
    time: str = Field(description="Giờ dạy (HH:MM)")
    location: str = Field(description="Địa điểm dạy")
    repeat_weeks: Optional[int] = Field(
        description="Số tuần lặp lại nếu dạy cố định hàng tuần. VD: 15 = dạy 15 tuần liên tiếp. Bỏ trống = chỉ 1 buổi.",
        default=None
    )