from services.google_auth import get_google_service
from datetime import datetime
import calendar as cal_module

CALENDAR_SCOPE = 'https://www.googleapis.com/auth/calendar.events'


def get_calendar_service(user_id: str):
    return get_google_service(user_id, 'calendar', 'v3', required_scope=CALENDAR_SCOPE)


def create_calendar_event(user_id: str, summary: str, location: str, description: str, start_iso: str, end_iso: str):
    """
    Tạo sự kiện trên Google Calendar.
    start_iso và end_iso phải là định dạng chuẩn: "2023-12-01T08:00:00+07:00"
    """
    service = get_calendar_service(user_id)
    
    event_body = {
        'summary': summary,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start_iso,
            'timeZone': 'Asia/Ho_Chi_Minh',
        },
        'end': {
            'dateTime': end_iso,
            'timeZone': 'Asia/Ho_Chi_Minh',
        },
    }

    event = service.events().insert(calendarId='primary', body=event_body).execute()
    return event.get('htmlLink')


def create_recurring_event(user_id: str, summary: str, location: str, description: str, 
                           start_iso: str, end_iso: str, repeat_weeks: int):
    """
    Tạo sự kiện lặp hàng tuần trên Google Calendar.
    repeat_weeks: số tuần lặp lại (VD: 15 = lặp 15 tuần liên tiếp).
    """
    service = get_calendar_service(user_id)
    
    event_body = {
        'summary': summary,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start_iso,
            'timeZone': 'Asia/Ho_Chi_Minh',
        },
        'end': {
            'dateTime': end_iso,
            'timeZone': 'Asia/Ho_Chi_Minh',
        },
        'recurrence': [f'RRULE:FREQ=WEEKLY;COUNT={repeat_weeks}'],
    }

    event = service.events().insert(calendarId='primary', body=event_body).execute()
    return event.get('htmlLink')


def mark_event_completed(user_id: str, event_id: str):
    """
    Đánh dấu một sự kiện là "đã hoàn thành" (đã dạy).
    - Đổi màu sang xanh lá (colorId=2) để user nhìn thấy trên Calendar.
    - Gắn metadata extendedProperties.private.status = "completed" để tool tính lương query chính xác.
    """
    service = get_calendar_service(user_id)
    
    updated_event = service.events().patch(
        calendarId='primary',
        eventId=event_id,
        body={
            'colorId': '2',
            'extendedProperties': {
                'private': {
                    'status': 'completed'
                }
            }
        }
    ).execute()
    
    return updated_event.get('summary', 'Không rõ tên')


def count_completed_events(user_id: str, month: int, year: int, keyword: str = "Dạy"):
    """
    Đếm số buổi đã hoàn thành trong tháng có chứa keyword trong summary.
    Thuật toán: query events theo khoảng thời gian tháng → lọc theo keyword + status completed.
    """
    service = get_calendar_service(user_id)
    
    # Tính đầu-cuối tháng theo timezone VN
    last_day = cal_module.monthrange(year, month)[1]
    time_min = f"{year}-{month:02d}-01T00:00:00+07:00"
    time_max = f"{year}-{month:02d}-{last_day}T23:59:59+07:00"
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,       # Mở rộng recurring events thành từng instance
        orderBy='startTime',
        maxResults=200
    ).execute()
    
    events = events_result.get('items', [])
    
    completed_events = []
    for event in events:
        summary = event.get('summary', '')
        ext_props = event.get('extendedProperties', {}).get('private', {})
        status = ext_props.get('status', '')
        
        if keyword in summary and status == 'completed':
            start = event['start'].get('dateTime', event['start'].get('date'))
            completed_events.append({
                'summary': summary,
                'start': start
            })
    
    return completed_events


def list_calendar_events(user_id: str, max_results: int = 10):
    """
    Lấy danh sách các sự kiện sắp tới trên Google Calendar.
    """
    service = get_calendar_service(user_id)
    now = datetime.utcnow().isoformat() + 'Z'  # Định dạng 'Z' cho UTC timezone
    
    events_result = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=max_results, singleEvents=True,
        orderBy='startTime').execute()
    
    events = events_result.get('items', [])
    
    result = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        result.append({
            'id': event['id'],
            'summary': event.get('summary', 'Không có tiêu đề'),
            'start': start
        })
    return result

def delete_calendar_event(user_id: str, event_id: str):
    """
    Xóa một sự kiện trên Google Calendar bằng ID.
    """
    service = get_calendar_service(user_id)
    service.events().delete(calendarId='primary', eventId=event_id).execute()
    return True
