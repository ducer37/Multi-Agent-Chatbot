import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from agent.schema import EventSchedule, TravelSchedule, TeachingSchedule
from services.calendar_service import (
    create_calendar_event, create_recurring_event,
    list_calendar_events, delete_calendar_event,
    mark_event_completed, count_completed_events
)
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from zoneinfo import ZoneInfo
from utils.path_security import get_safe_path, WORKSPACE

load_dotenv()

mcp = FastMCP("HUST-Schedule-Master")

def parse_to_iso(date_str: str, time_str: str):
    try:
        if time_str == "Chưa rõ" or not time_str.strip():
            time_str = "08:00"
            
        combined_str = f"{date_str} {time_str}"
        # Dùng dateutil parser với chế độ fuzzy để ráng hiểu được các chuỗi méo mó của LLM
        dt = date_parser.parse(combined_str, fuzzy=True, dayfirst=True)

        vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=vn_tz)
        else:
            dt = dt.astimezone(vn_tz)

        start_iso = dt.isoformat()
        end_iso = (dt + timedelta(hours=1)).isoformat()
        return start_iso, end_iso
    except Exception:
        # Thay vì crash, trả về ValueError với thông điệp hướng dẫn LLM
        raise ValueError(f"Không thể hiểu được ngày giờ '{date_str} {time_str}'.")

# =============================================
# TOOLS HIỆN TẠI (đã cập nhật hỗ trợ lặp tuần)
# =============================================

@mcp.tool()
def create_event_schedule(user_id: str, event: EventSchedule) -> str:
    """
    Tạo lịch trình sự kiện dựa trên schema chuẩn.
    Gọi tool này khi người dùng cung cấp thông tin về hoạt động, tiêu đề, ngày, giờ, địa điểm.
    """
    filename = f"lich_{event.activity_type}_{event.title.replace(' ', '_')}.txt"
    repeat_info = f"\n🔄 Lặp: {event.repeat_weeks} tuần" if event.repeat_weeks else ""
    content = (
        f"--- 📅 LỊCH SỰ KIỆN: {event.title.upper()} ---\n"
        f"🔹 Loại: {event.activity_type}\n"
        f"📆 Ngày: {event.date}\n"
        f"⏰ Giờ: {event.time}\n"
        f"📍 Địa điểm: {event.location}\n"
        f"✅ Trạng thái: Đã lên lịch{repeat_info}"
    )
    path = get_safe_path(user_id, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✅ Đã tạo lịch sự kiện: {filename}"

@mcp.tool()
def create_travel_schedule(user_id: str, travel: TravelSchedule) -> str:
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
    path = get_safe_path(user_id, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✅ Đã tạo lịch di chuyển: {filename}"

@mcp.tool()
def create_google_calendar_event(user_id: str, event: EventSchedule) -> str:
    """
    Tạo sự kiện ĐỒNG BỘ LÊN GOOGLE CALENDAR (Lịch sự kiện/học/họp).
    Bạn BẮT BUỘC phải đảm bảo event.date có định dạng YYYY-MM-DD và event.time có định dạng HH:MM.
    Nếu event.repeat_weeks có giá trị, sẽ tạo lịch LẶP HÀNG TUẦN cho số tuần đó.
    """
    try:
        start_iso, end_iso = parse_to_iso(event.date, event.time)
        summary = f"[{event.activity_type}] {event.title}"
        description = "Được tạo bởi HUST Schedule Agent"
        
        if event.repeat_weeks and event.repeat_weeks > 1:
            link = create_recurring_event(user_id, summary, event.location, description, start_iso, end_iso, event.repeat_weeks)
            return f"✅ Đã tạo lịch LẶP {event.repeat_weeks} tuần trên Google Calendar! Xem tại: {link}"
        else:
            link = create_calendar_event(user_id, summary, event.location, description, start_iso, end_iso)
            return f"✅ Đã tạo thành công sự kiện trên Google Calendar! Xem tại: {link}"
    except ValueError as ve:
        # Bắt lỗi parse ngày giờ và gửi thông điệp cho LLM
        return f"❌ Lỗi: {str(ve)} Hãy hỏi lại người dùng để xác nhận ngày giờ rõ ràng hơn (VD: 'Sáng mai mấy giờ?'). TUYỆT ĐỐI KHÔNG yêu cầu người dùng nhập theo định dạng YYYY-MM-DD!"
    except Exception as e:
        return f"❌ Lỗi Google Calendar: {str(e)}"

@mcp.tool()
def create_google_calendar_travel(user_id: str, travel: TravelSchedule) -> str:
    """
    Tạo sự kiện ĐỒNG BỘ LÊN GOOGLE CALENDAR (Lịch di chuyển).
    Bạn BẮT BUỘC phải đảm bảo travel.date có định dạng YYYY-MM-DD và travel.time có định dạng HH:MM.
    """
    try:
        start_iso, end_iso = parse_to_iso(travel.date, travel.time)
        summary = f"✈️ Di chuyển: {travel.departure} ➡️ {travel.destination}"
        description = f"Phương tiện: {travel.transport_type}\nĐược tạo bởi HUST Schedule Agent"
        
        link = create_calendar_event(user_id, summary, "Không xác định", description, start_iso, end_iso)
        return f"✅ Đã tạo thành công lịch di chuyển trên Google Calendar! Xem tại: {link}"
    except ValueError as ve:
        return f"❌ Lỗi: {str(ve)} Hãy hỏi lại người dùng để xác nhận ngày giờ rõ ràng hơn. TUYỆT ĐỐI KHÔNG yêu cầu người dùng nhập theo định dạng YYYY-MM-DD!"
    except Exception as e:
        return f"❌ Lỗi Google Calendar: {str(e)}"

@mcp.tool()
def list_google_calendar_events(user_id: str, limit: int = 10) -> str:
    """
    Lấy danh sách các sự kiện sắp tới trên Google Calendar.
    Dùng công cụ này để tra cứu thông tin lịch hoặc TÌM EVENT ID trước khi thực hiện xóa lịch hoặc đánh dấu đã dạy.
    """
    try:
        events = list_calendar_events(user_id, max_results=limit)
        if not events:
            return "Không tìm thấy sự kiện nào sắp tới."
        
        result = "Danh sách sự kiện sắp tới:\n"
        for idx, event in enumerate(events):
            result += f"{idx + 1}. [ID: {event['id']}] - Tên: {event['summary']} - Thời gian: {event['start']}\n"
        return result
    except Exception as e:
        return f"❌ Lỗi lấy danh sách sự kiện: {str(e)}"

@mcp.tool()
def delete_google_calendar_event(user_id: str, event_id: str) -> str:
    """
    Xóa một sự kiện trên Google Calendar bằng ID.
    BẠN BẮT BUỘC PHẢI gọi list_google_calendar_events trước để lấy chính xác event_id. Tuyệt đối không tự đoán ID.
    """
    try:
        delete_calendar_event(user_id, event_id)
        return f"✅ Đã xóa thành công sự kiện có ID: {event_id}"
    except Exception as e:
        return f"❌ Lỗi khi xóa sự kiện: {str(e)}"

# =============================================
# TOOLS MỚI: Lịch dạy + Đánh dấu + Tính lương
# =============================================

@mcp.tool()
def create_teaching_schedule(user_id: str, teaching: TeachingSchedule) -> str:
    """
    TẠO LỊCH DẠY GIA SƯ LÊN GOOGLE CALENDAR.
    Sử dụng khi người dùng muốn đặt lịch dạy, dạy kèm, gia sư.
    Nếu teaching.repeat_weeks có giá trị, sẽ tạo lịch DẠY LẶP HÀNG TUẦN.
    Bạn BẮT BUỘC phải đảm bảo teaching.date có định dạng YYYY-MM-DD và teaching.time có định dạng HH:MM.
    """
    try:
        start_iso, end_iso = parse_to_iso(teaching.date, teaching.time)
        summary = f"[Dạy] {teaching.title}"
        
        student_info = f" - Học sinh: {teaching.student_name}" if teaching.student_name != "Chưa rõ" else ""
        description = f"Lịch dạy gia sư{student_info}\nĐược tạo bởi HUST Schedule Agent"
        
        if teaching.repeat_weeks and teaching.repeat_weeks > 1:
            link = create_recurring_event(user_id, summary, teaching.location, description, start_iso, end_iso, teaching.repeat_weeks)
            return f"✅ Đã tạo lịch dạy LẶP {teaching.repeat_weeks} tuần trên Google Calendar!\n📚 Môn: {teaching.title}\n⏰ Bắt đầu: {teaching.date} lúc {teaching.time}\n📍 Tại: {teaching.location}\n🔗 Xem tại: {link}"
        else:
            link = create_calendar_event(user_id, summary, teaching.location, description, start_iso, end_iso)
            return f"✅ Đã tạo lịch dạy trên Google Calendar!\n📚 Môn: {teaching.title}\n⏰ Ngày: {teaching.date} lúc {teaching.time}\n📍 Tại: {teaching.location}\n🔗 Xem tại: {link}"
    except ValueError as ve:
        return f"❌ Lỗi: {str(ve)} Hãy hỏi lại người dùng để xác nhận ngày giờ rõ ràng hơn."
    except Exception as e:
        return f"❌ Lỗi Google Calendar: {str(e)}"

@mcp.tool()
def mark_teaching_completed(user_id: str, event_id: str) -> str:
    """
    ĐÁNH DẤU MỘT BUỔI DẠY LÀ "ĐÃ DẠY" TRÊN GOOGLE CALENDAR.
    Sự kiện sẽ đổi sang MÀU XANH LÁ và được gắn metadata "completed".
    BẮT BUỘC PHẢI gọi `list_google_calendar_events` trước để lấy chính xác event_id của buổi dạy cần đánh dấu.
    TUYỆT ĐỐI KHÔNG TỰ BỊA RA event_id.
    """
    try:
        event_name = mark_event_completed(user_id, event_id)
        return f"✅ Đã đánh dấu \"{event_name}\" là ĐÃ DẠY! 🟢 (Sự kiện đã đổi sang màu xanh lá trên Calendar)"
    except Exception as e:
        return f"❌ Lỗi khi đánh dấu: {str(e)}"

@mcp.tool()
def calculate_teaching_salary(user_id: str, month: int, year: int, rate_per_session: int = 250000) -> str:
    """
    TÍNH LƯƠNG DẠY GIA SƯ TRONG THÁNG.
    Công thức: Số buổi đã đánh dấu "đã dạy" × đơn giá mỗi buổi.
    - month: Tháng cần tính (1-12)
    - year: Năm cần tính (VD: 2026)
    - rate_per_session: Đơn giá mỗi buổi dạy (mặc định 250.000đ)
    Sử dụng khi người dùng hỏi "tính lương tháng này", "lương dạy tháng 4", v.v.
    """
    try:
        completed = count_completed_events(user_id, month, year, keyword="Dạy")
        count = len(completed)
        total_salary = count * rate_per_session
        
        # Format tiền VNĐ
        salary_str = f"{total_salary:,.0f}".replace(",", ".")
        rate_str = f"{rate_per_session:,.0f}".replace(",", ".")
        
        result = f"💰 BẢNG TÍNH LƯƠNG DẠY — Tháng {month}/{year}\n"
        result += f"{'='*40}\n"
        result += f"📊 Tổng buổi đã dạy: {count} buổi\n"
        result += f"💵 Đơn giá: {rate_str}đ/buổi\n"
        result += f"💰 TỔNG LƯƠNG: {salary_str}đ\n"
        result += f"{'='*40}\n"
        
        if completed:
            result += f"\n📋 Chi tiết các buổi đã dạy:\n"
            for i, evt in enumerate(completed, 1):
                result += f"  {i}. {evt['summary']} — {evt['start']}\n"
        else:
            result += f"\n⚠️ Chưa có buổi dạy nào được đánh dấu \"đã dạy\" trong tháng {month}/{year}."
        
        return result
    except Exception as e:
        return f"❌ Lỗi khi tính lương: {str(e)}"

if __name__ == "__main__":
    mcp.run()
