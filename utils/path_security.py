import os
import re


WORKSPACE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    os.getenv("WORKSPACE_DIR", "workspace")
)
os.makedirs(WORKSPACE, exist_ok=True)


def get_safe_path(user_id: str, filename: str) -> str:
    """
    Tạo đường dẫn file an toàn trong workspace cá nhân của user.
    Bảo vệ chống Path Traversal (../ attack).
    """
    if re.search(r'\.\.', user_id) or re.search(r'\.\.', filename):
        raise ValueError("Phát hiện truy cập trái phép (Path Traversal)!")
        
    user_workspace = os.path.abspath(os.path.join(WORKSPACE, user_id))
    if not user_workspace.startswith(os.path.abspath(WORKSPACE)):
        raise ValueError("Invalid user_id")
    os.makedirs(user_workspace, exist_ok=True)
    
    safe_path = os.path.abspath(os.path.join(user_workspace, filename))
    if not safe_path.startswith(user_workspace):
        raise ValueError("Truy cập ngoài workspace bị từ chối!")
    return safe_path


def get_user_workspace(user_id: str) -> str:
    """Trả về đường dẫn workspace cá nhân của user (tạo nếu chưa có)."""
    user_workspace = os.path.abspath(os.path.join(WORKSPACE, user_id))
    if not user_workspace.startswith(os.path.abspath(WORKSPACE)):
        raise ValueError("Invalid user_id")
    os.makedirs(user_workspace, exist_ok=True)
    return user_workspace
