import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from agent.schema import EventSchedule, TravelSchedule

load_dotenv()

mcp = FastMCP("HUST-Schedule-Master")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.path.join(BASE_DIR, os.getenv("WORKSPACE_DIR", "workspace"))
os.makedirs(WORKSPACE, exist_ok=True)

def get_safe_path(filename: str) -> str:
    safe_path = os.path.abspath(os.path.join(WORKSPACE, filename))
    if not safe_path.startswith(os.path.abspath(WORKSPACE)):
        raise ValueError("Truy cập ngoài workspace bị từ chối!")
    return safe_path

@mcp.tool()
def create_event_schedule(event: EventSchedule) -> str:
    """
    Tạo lịch trình sự kiện dựa trên schema chuẩn.
    Gọi tool này khi người dùng cung cấp thông tin về hoạt động, tiêu đề, ngày, giờ, địa điểm.
    """
    filename = f"lich_{event.activity_type}_{event.title.replace(' ', '_')}.txt"
    content = (
        f"--- 📅 LỊCH SỰ KIỆN: {event.title.upper()} ---\n"
        f"🔹 Loại: {event.activity_type}\n"
        f"📆 Ngày: {event.date}\n"
        f"⏰ Giờ: {event.time}\n"
        f"📍 Địa điểm: {event.location}\n"
        f"✅ Trạng thái: Đã lên lịch"
    )
    path = get_safe_path(filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✅ Đã tạo lịch sự kiện: {filename}"

@mcp.tool()
def create_travel_schedule(travel: TravelSchedule) -> str:
    """
    Tạo lịch trình di chuyển dựa trên schema chuẩn.
    Sử dụng khi có thông tin về phương tiện, điểm đi, điểm đến và ngày tháng.
    """
    filename = f"chuyen_di_{travel.destination.replace(' ', '_')}.txt"
    content = (
        f"--- ✈️ LỊCH DI CHUYỂN: {travel.destination.upper()} ---\n"
        f"🚌 Phương tiện: {travel.transport_type}\n"
        f"🛫 Điểm đi: {travel.departure}\n"
        f"🛬 Điểm đến: {travel.destination}\n"
        f"📅 Ngày: {travel.date}\n"
        f"🕒 Giờ khởi hành: {travel.time}\n"
    )
    path = get_safe_path(filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✅ Đã tạo lịch di chuyển: {filename}"

if __name__ == "__main__":
    mcp.run()
