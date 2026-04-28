import os
import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from services.db_service import save_user_token

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/calendar.events'
]

# Bộ nhớ đệm tạm thời để lưu mã PKCE (code_verifier) giữa lúc login và lúc callback
oauth_state_store = {}

def get_flow():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")
    
    if not client_id or not client_secret:
        raise ValueError("Thiếu cấu hình GOOGLE_CLIENT_ID hoặc GOOGLE_CLIENT_SECRET trong file .env")

    # Giả lập lại cấu trúc của file credentials.json từ các biến môi trường
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [redirect_uri]
        }
    }
        
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

@router.get("/google/login")
async def google_login(user_id: str):
    """
    Khởi tạo quá trình đăng nhập Google OAuth.
    Sinh ra một URL xác thực và redirect trình duyệt tới đó.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="Cần cung cấp user_id")
        
    try:
        flow = get_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent', # Buộc hiện consent screen để lấy được refresh_token
            state=user_id # Truyền user_id vào state để nhận lại ở callback
        )
        
        # Lưu lại code_verifier sinh ra ở bước này để dùng ở bước callback
        if hasattr(flow, 'code_verifier'):
            oauth_state_store[user_id] = flow.code_verifier
            
        return RedirectResponse(url=authorization_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/google/callback")
async def google_callback(request: Request):
    """
    Endpoint xử lý callback từ Google.
    """
    code = request.query_params.get("code")
    state = request.query_params.get("state") # state chính là user_id
    error = request.query_params.get("error")

    if error:
        raise HTTPException(status_code=400, detail=f"OAuth Error: {error}")
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="Thiếu code hoặc state (user_id)")

    user_id = state
    flow = get_flow()
    
    # Fix cho test localhost không cần HTTPS
    authorization_response = str(request.url)
    if authorization_response.startswith("http://") and ("localhost" in authorization_response or "127.0.0.1" in authorization_response):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Khôi phục lại code_verifier từ bước login
    if user_id in oauth_state_store:
        flow.code_verifier = oauth_state_store.pop(user_id)

    try:
        flow.fetch_token(authorization_response=authorization_response)
        creds = flow.credentials
        
        creds_dict = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        
        # Lưu vào PostgreSQL thông qua NeonDB
        save_user_token(user_id, creds_dict)
        
        return {"status": "success", "message": f"✅ Cấp quyền Google Drive thành công cho user: {user_id}. Bạn có thể đóng tab này và bắt đầu chat."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi trao đổi token: {str(e)}")
