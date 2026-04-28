import os
import subprocess
import sys
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from services.drive_service import list_drive_files, delete_drive_file, upload_file
from utils.path_security import get_safe_path, WORKSPACE

load_dotenv()

mcp = FastMCP("HUST-File-Master")


@mcp.tool()
def write_text_file(user_id: str, filename: str, content: str) -> str:
    """Tạo hoặc ghi đè file văn bản (.py, .txt, .md, .html)."""
    try:
        path = get_safe_path(user_id, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ Đã tạo file: {filename}"
    except Exception as e:
        return f"❌ Lỗi: {str(e)}"

@mcp.tool()
def execute_python_agent(user_id: str, script: str) -> str:
    """
    THỰC THI MÃ PYTHON ĐỂ TẠO FILE (.docx, .xlsx, .pdf).
    QUY TẮC BẮT BUỘC:
    1. CHỈ sử dụng các thư viện Python (python-docx, pandas, openpyxl).
    2. TUYỆT ĐỐI KHÔNG sử dụng Node.js, JavaScript hoặc gọi subprocess để chạy ngôn ngữ khác.
    3. Luôn sử dụng biến WORKSPACE có sẵn để lưu file qua os.path.join(WORKSPACE, filename).
    """
    temp_script_path = get_safe_path(user_id, "_temp_script.py")
    user_workspace = os.path.join(WORKSPACE, user_id)
    enriched_script = f"import os\nWORKSPACE='{user_workspace}'\n{script}"
    
    try:
        with open(temp_script_path, "w", encoding="utf-8") as f:
            f.write(enriched_script)
        
        # Chạy bằng chính Python của .venv
        result = subprocess.run(
            [sys.executable, temp_script_path],
            capture_output=True, text=True, timeout=20
        )
        
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)
            
        if result.returncode == 0:
            return f"🚀 Thành công!\n{result.stdout}"
        else:
            return f"⚠️ Lỗi code:\n{result.stderr}"
    except Exception as e:
        return f"❌ Lỗi hệ thống: {str(e)}"

@mcp.tool()
def list_local_files(user_id: str) -> str:
    """Liệt kê file trong thư mục LOCAL workspace cá nhân trên máy tính."""
    try:
        user_workspace = os.path.join(WORKSPACE, user_id)
        if not os.path.exists(user_workspace):
            return "📁 Thư mục workspace cá nhân của bạn hiện đang rỗng."
            
        files = os.listdir(user_workspace)
        if not files:
            return "📁 Thư mục workspace cá nhân của bạn hiện đang rỗng."
        
        # Lọc bỏ các file ẩn nếu cần (.DS_Store...)
        visible_files = [f for f in files if not f.startswith('.')]
        return "📁 Các file hiện có: " + ", ".join(visible_files)
    except Exception as e:
        return f"❌ Lỗi khi liệt kê file: {str(e)}"

@mcp.tool()
def delete_file(user_id: str, filename: str) -> str:
    """
    Xóa một file cụ thể trong thư mục workspace cá nhân. 
    Yêu cầu cung cấp chính xác tên file (bao gồm cả phần mở rộng).
    """
    try:
        if not filename:
            return "⚠️ Vui lòng cung cấp tên file cần xóa."
            
        path = get_safe_path(user_id, filename)
        
        if os.path.exists(path):
            os.remove(path)
            return f"🗑️ Đã xóa thành công: {filename}"
        else:
            return f"❓ Không tìm thấy file '{filename}' để xóa."
            
    except Exception as e:
        return f"❌ Lỗi khi xóa file: {str(e)}"

@mcp.tool()
def list_google_drive(user_id: str, limit: int = 5) -> str:
    """Liệt kê file trên Cloud GOOGLE DRIVE cá nhân của user_id."""
    try:
        files = list_drive_files(user_id, limit)
        if not files:
            return "📭 Drive của bạn trống không."

        file_list = [f"- {f['name']} (ID: {f['id']})" for f in files if f['mimeType'] != "application/vnd.google-apps.folder"]
        return "📁 Các file trên Drive: \n" + "\n".join(file_list)
    except Exception as e:
        return f"❌ Lỗi Drive: {str(e)}"

@mcp.tool()
def upload_to_drive(user_id: str, filename: str) -> str:
    """Tải một file từ thư mục LOCAL workspace lên Google Drive của user_id."""
    try:
        path = get_safe_path(user_id, filename)
        if not os.path.exists(path):
            return f"❌ Không tìm thấy file {filename} trong workspace cá nhân."
        
        file_id = upload_file(user_id, path)
        return f"🚀 Đã tải lên Drive thành công! ID file mới: {file_id}"
    except Exception as e:
        return f"❌ Lỗi khi tải lên: {str(e)}"

@mcp.tool()
def delete_from_drive(user_id: str, file_id: str) -> str:
    """
    Xóa file trên Google Drive của user_id. 
    LƯU Ý: Cần cung cấp ID của file (lấy từ tool list_google_drive).
    """
    try:
        delete_drive_file(user_id, file_id)
        return f"🗑️ Đã xóa file trên Drive (ID: {file_id})"
    except Exception as e:
        return f"❌ Lỗi khi xóa trên Drive: {str(e)}"

if __name__ == "__main__":
    mcp.run()
