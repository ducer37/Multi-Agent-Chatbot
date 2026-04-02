import pymupdf4llm
from pathlib import Path

def load_pdf_text(file_path: str) -> str:
    """
    Đọc file PDF và chuyển đổi toàn bộ nội dung (bao gồm cả bảng biểu)
    sang định dạng Markdown chuẩn để bảo toàn cấu trúc cho LLM.
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Không tìm thấy file tại: {file_path}")
    
    print(f"--- Đang phân tích layout và bảng biểu file: {file_path} ---")
    md_text = pymupdf4llm.to_markdown(file_path, pages=range(4, 34))    
    return md_text