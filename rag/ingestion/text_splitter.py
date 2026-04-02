import re
from langchain_core.documents import Document

def get_parent_documents(markdown_text: str) -> list[Document]:
    """
    Tách Markdown text thành các Document theo cấp độ "Điều". 
    Mỗi Điều sẽ đóng vai trò là một Parent Document.
    """
    documents = []
    
    chapter_pattern = re.compile(r'(CHƯƠNG\s+[IVXLCDM]+.*?)(?=CHƯƠNG\s+[IVXLCDM]+|$)', re.DOTALL)
    article_pattern = re.compile(r'(Điều\s+\d+\..*?)(?=Điều\s+\d+\.|$)', re.DOTALL)
    
    chapters = chapter_pattern.findall(markdown_text)
    
    for chapter_text in chapters:
        chapter_lines = chapter_text.strip().split('\n')
        chapter_name = chapter_lines[0].strip()
        if len(chapter_lines) > 1 and not chapter_lines[1].startswith("Điều"):
            chapter_name += " - " + chapter_lines[1].strip()
            
        level = "Chung"
        if "ĐÀO TẠO ĐẠI HỌC" in chapter_text: level = "Đại học"
        elif "ĐÀO TẠO KỸ SƯ" in chapter_text: level = "Kỹ sư"
        elif "ĐÀO TẠO THẠC SĨ" in chapter_text: level = "Thạc sĩ"
        elif "ĐÀO TẠO TIẾN SĨ" in chapter_text: level = "Tiến sĩ"
        
        articles = article_pattern.findall(chapter_text)
        
        for article_text in articles:
            article_text = article_text.strip()
            article_name_match = re.match(r'(Điều\s+\d+\.[^\n]*)', article_text)
            article_name = article_name_match.group(1).strip() if article_name_match else "Điều Không xác định"
            
            # Gắn thêm tên Chương và Điều vào nội dung để tạo bối cảnh (Context)
            enriched_text = f"[{chapter_name}]\n[{article_name}]\n\n{article_text}"
            
            metadata = {
                "source": "Quy chế 5445/ĐHBK",
                "chapter": chapter_name,
                "article": article_name,
                "level": level
            }
            
            # Đóng gói nguyên một "Điều" thành Parent Document
            documents.append(Document(page_content=enriched_text, metadata=metadata))
            
    return documents