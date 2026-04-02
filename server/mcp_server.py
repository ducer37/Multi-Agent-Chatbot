import os
import subprocess
import sys
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from services.drive_service import list_drive_files, delete_drive_file, upload_file

load_dotenv()

mcp = FastMCP("HUST-File-Master")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.path.join(BASE_DIR, os.getenv("WORKSPACE_DIR", "workspace"))
os.makedirs(WORKSPACE, exist_ok=True)

def get_safe_path(filename: str) -> str:
    safe_path = os.path.abspath(os.path.join(WORKSPACE, filename))
    if not safe_path.startswith(os.path.abspath(WORKSPACE)):
        raise ValueError("Truy cập ngoài workspace bị từ chối!")
    return safe_path

@mcp.tool()
def write_text_file(filename: str, content: str) -> str:
    """Tạo hoặc ghi đè file văn bản (.py, .txt, .md, .html)."""
    try:
        path = get_safe_path(filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ Đã tạo file: {filename}"
    except Exception as e:
        return f"❌ Lỗi: {str(e)}"

@mcp.tool()
def execute_python_agent(script: str) -> str:
    """
    THỰC THI MÃ PYTHON ĐỂ TẠO FILE (.docx, .xlsx, .pdf).
    QUY TẮC BẮT BUỘC:
    1. CHỈ sử dụng các thư viện Python (python-docx, pandas, openpyxl).
    2. TUYỆT ĐỐI KHÔNG sử dụng Node.js, JavaScript hoặc gọi subprocess để chạy ngôn ngữ khác.
    3. Luôn sử dụng biến WORKSPACE có sẵn để lưu file qua os.path.join(WORKSPACE, filename).
    """
    temp_script_path = get_safe_path("_temp_script.py")
    # Tiêm sẵn WORKSPACE vào script để Claude sử dụng
    enriched_script = f"import os\nWORKSPACE='{WORKSPACE}'\n{script}"
    
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
def list_local_files() -> str:
    """Liệt kê file trong thư mục LOCAL workspace trên máy tính."""
    try:
        files = os.listdir(WORKSPACE)
        if not files:
            return "📁 Thư mục workspace hiện đang rỗng."
        
        # Lọc bỏ các file ẩn nếu cần (.DS_Store...)
        visible_files = [f for f in files if not f.startswith('.')]
        return "📁 Các file hiện có: " + ", ".join(visible_files)
    except Exception as e:
        return f"❌ Lỗi khi liệt kê file: {str(e)}"

@mcp.tool()
def delete_file(filename: str) -> str:
    """
    Xóa một file cụ thể trong thư mục workspace. 
    Yêu cầu cung cấp chính xác tên file (bao gồm cả phần mở rộng).
    """
    try:
        if not filename:
            return "⚠️ Vui lòng cung cấp tên file cần xóa."
            
        path = get_safe_path(filename)
        
        if os.path.exists(path):
            os.remove(path)
            return f"🗑️ Đã xóa thành công: {filename}"
        else:
            return f"❓ Không tìm thấy file '{filename}' để xóa."
            
    except Exception as e:
        return f"❌ Lỗi khi xóa file: {str(e)}"

@mcp.tool()
def list_google_drive(limit: int = 5) -> str:
    """Liệt kê file trên Cloud GOOGLE DRIVE cá nhân."""
    try:
        files = list_drive_files(limit)
        if not files:
            return "📭 Drive của bạn trống không."

        file_list = [f"- {f['name']} (ID: {f['id']})" for f in files if f['mimeType'] != "application/vnd.google-apps.folder"]
        return "📁 Các file trên Drive: \n" + "\n".join(file_list)
    except Exception as e:
        return f"❌ Lỗi Drive: {str(e)}"

@mcp.tool()
def upload_to_drive(filename: str) -> str:
    """Tải một file từ thư mục LOCAL workspace lên Google Drive."""
    try:
        path = get_safe_path(filename)
        if not os.path.exists(path):
            return f"❌ Không tìm thấy file {filename} trong workspace."
        
        file_id = upload_file(path)
        return f"🚀 Đã tải lên Drive thành công! ID file mới: {file_id}"
    except Exception as e:
        return f"❌ Lỗi khi tải lên: {str(e)}"

@mcp.tool()
def delete_from_drive(file_id: str) -> str:
    """
    Xóa file trên Google Drive. 
    LƯU Ý: Cần cung cấp ID của file (lấy từ tool list_google_drive).
    """
    try:
        delete_drive_file(file_id)
        return f"🗑️ Đã xóa file trên Drive (ID: {file_id})"
    except Exception as e:
        return f"❌ Lỗi khi xóa trên Drive: {str(e)}"

if __name__ == "__main__":
    mcp.run()
