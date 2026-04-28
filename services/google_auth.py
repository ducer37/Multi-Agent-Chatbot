import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from services.db_service import get_user_token, save_user_token


def get_google_credentials(user_id: str, required_scope: str = None) -> Credentials:
    """
    Logic xác thực Google OAuth dùng chung cho mọi Google API service.
    - Lấy token từ DB
    - Validate scope (nếu yêu cầu)
    - Tự động refresh token nếu hết hạn
    - Lưu lại token mới sau khi refresh
    """
    if not user_id:
        raise ValueError("Yêu cầu user_id để xác thực Google API.")

    creds_dict = get_user_token(user_id)
    if not creds_dict:
        raise ValueError(
            f"Người dùng {user_id} chưa đăng nhập. "
            f"Vui lòng truy cập /api/v1/auth/google/login?user_id={user_id}"
        )

    # Validate scope nếu được yêu cầu
    if required_scope:
        scopes = creds_dict.get('scopes', [])
        if required_scope not in scopes:
            raise ValueError(
                f"Tài khoản của {user_id} thiếu quyền '{required_scope}'. "
                f"Vui lòng đăng nhập lại để cấp quyền mới."
            )

    creds = Credentials(
        token=creds_dict['token'],
        refresh_token=creds_dict['refresh_token'],
        token_uri=creds_dict['token_uri'],
        client_id=creds_dict['client_id'],
        client_secret=creds_dict['client_secret'],
        scopes=creds_dict['scopes']
    )

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                updated_creds = {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }
                save_user_token(user_id, updated_creds)
            except Exception as e:
                raise ValueError(f"Không thể làm mới token cho {user_id}: {str(e)}")
        else:
            raise ValueError(
                f"Token của {user_id} đã hết hạn và không thể refresh. Vui lòng xác thực lại."
            )

    return creds


def get_google_service(user_id: str, service_name: str, version: str, required_scope: str = None):
    """
    Tạo Google API service client (Drive, Calendar, ...) với xác thực tự động.
    """
    creds = get_google_credentials(user_id, required_scope)
    return build(service_name, version, credentials=creds)
