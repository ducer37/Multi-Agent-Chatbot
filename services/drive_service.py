import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload  

SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def list_drive_files(limit=10):
    service = get_drive_service()

    query = "'me' in owners and trashed = false"

    results = service.files().list(
        pageSize=limit, 
        fields="nextPageToken, files(id, name, mimeType)",
        q=query
    ).execute()
    return results.get('files', [])

def upload_file(local_path, drive_folder_id=None):
    """
    Tải file lên Drive. 
    Nếu muốn vào thư mục cụ thể, hãy cung cấp folder_id.
    """
    service = get_drive_service()
    file_metadata = {'name': os.path.basename(local_path)}
    if drive_folder_id:
        file_metadata['parents'] = [drive_folder_id]
    
    media = MediaFileUpload(local_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def delete_drive_file(file_id):
    """Xóa file trên Drive bằng ID."""
    service = get_drive_service()
    service.files().delete(fileId=file_id).execute()
    return True

if __name__ == "__main__":
    print("🚀 Đang khởi tạo xác thực Google Drive...")
    try:
        service = get_drive_service()
        print("✅ Xác thực thành công!")
            
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")