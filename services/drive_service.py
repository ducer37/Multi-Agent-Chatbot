import os.path
from googleapiclient.http import MediaFileUpload
from services.google_auth import get_google_service

DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive'


def get_drive_service(user_id: str):
    return get_google_service(user_id, 'drive', 'v3', required_scope=DRIVE_SCOPE)


def list_drive_files(user_id: str, limit=10):
    service = get_drive_service(user_id)

    query = "'me' in owners and trashed = false"

    results = service.files().list(
        pageSize=limit, 
        fields="nextPageToken, files(id, name, mimeType)",
        q=query
    ).execute()
    return results.get('files', [])

def upload_file(user_id: str, local_path, drive_folder_id=None):
    """
    Tải file lên Drive. 
    Nếu muốn vào thư mục cụ thể, hãy cung cấp folder_id.
    """
    service = get_drive_service(user_id)
    file_metadata = {'name': os.path.basename(local_path)}
    if drive_folder_id:
        file_metadata['parents'] = [drive_folder_id]
    
    media = MediaFileUpload(local_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def delete_drive_file(user_id: str, file_id):
    """Xóa file trên Drive bằng ID."""
    service = get_drive_service(user_id)
    service.files().delete(fileId=file_id).execute()
    return True