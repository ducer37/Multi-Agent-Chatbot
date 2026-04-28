import os
import arxiv
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from utils.path_security import get_safe_path, WORKSPACE

load_dotenv()

mcp = FastMCP("HUST-Research-Master")

@mcp.tool()
def search_arxiv_papers(query: str, max_results: int = 5, sort_by: str = "relevance") -> str:
    """
    TÌM KIẾM BÀI BÁO KHOA HỌC TRÊN ARXIV.
    Sử dụng tool này khi người dùng muốn tìm paper, bài báo nghiên cứu, hoặc xu hướng nghiên cứu.
    - query: Từ khóa tìm kiếm (VD: "transformer attention mechanism", "LLM reasoning", "RAG retrieval augmented generation")
    - max_results: Số lượng kết quả tối đa (mặc định 5, tối đa 20)
    - sort_by: Sắp xếp theo "relevance" (liên quan nhất) hoặc "date" (mới nhất)
    """
    try:
        client = arxiv.Client(
            page_size=20,
            delay_seconds=3.0,
            num_retries=3
        )
        
        sort_criterion = (
            arxiv.SortCriterion.Relevance 
            if sort_by == "relevance" 
            else arxiv.SortCriterion.SubmittedDate
        )
        
        search = arxiv.Search(
            query=query,
            max_results=min(max_results, 20),
            sort_by=sort_criterion
        )
        
        results = []
        for paper in client.results(search):
            authors_list = [a.name for a in paper.authors[:5]]
            if len(paper.authors) > 5:
                authors_list.append(f"... và {len(paper.authors) - 5} tác giả khác")
            
            results.append({
                "id": paper.get_short_id(),
                "title": paper.title,
                "authors": authors_list,
                "abstract": paper.summary,
                "published": paper.published.strftime("%Y-%m-%d"),
                "updated": paper.updated.strftime("%Y-%m-%d") if paper.updated else None,
                "url": paper.entry_id,
                "pdf_url": paper.pdf_url,
                "categories": paper.categories
            })
        
        if not results:
            return "Không tìm thấy bài báo nào phù hợp với từ khóa tìm kiếm."
        
        # Format thành chuỗi dễ đọc cho LLM
        output = f"📚 Tìm thấy {len(results)} bài báo trên arXiv cho từ khóa \"{query}\":\n\n"
        
        for i, paper in enumerate(results, 1):
            output += f"--- 📄 Bài báo {i}/{len(results)} ---\n"
            output += f"🆔 ArXiv ID: {paper['id']}\n"
            output += f"📝 Tiêu đề: {paper['title']}\n"
            output += f"👥 Tác giả: {', '.join(paper['authors'])}\n"
            output += f"📅 Ngày xuất bản: {paper['published']}\n"
            output += f"🔗 Link: {paper['url']}\n"
            output += f"📂 Danh mục: {', '.join(paper['categories'])}\n"
            output += f"📖 Abstract:\n{paper['abstract']}\n\n"
        
        return output
        
    except Exception as e:
        return f"❌ Lỗi khi tìm kiếm arXiv: {str(e)}"

@mcp.tool()
def get_paper_details(paper_id: str) -> str:
    """
    LẤY CHI TIẾT MỘT BÀI BÁO CỤ THỂ TRÊN ARXIV BẰNG ID.
    - paper_id: Mã ID của bài báo trên arXiv (VD: "2301.00234", "2401.12345v1")
    Sử dụng tool này khi người dùng cung cấp một arXiv ID cụ thể hoặc muốn xem chi tiết 1 bài báo.
    """
    try:
        client = arxiv.Client()
        
        # Chuẩn hóa ID
        clean_id = paper_id.strip()
        if clean_id.startswith("arxiv:"):
            clean_id = clean_id[6:]
        
        search = arxiv.Search(id_list=[clean_id])
        paper = next(client.results(search), None)
        
        if not paper:
            return f"Không tìm thấy bài báo với ID: {paper_id}"
        
        authors_list = [a.name for a in paper.authors]
        
        output = f"📄 CHI TIẾT BÀI BÁO ARXIV\n"
        output += f"{'='*50}\n"
        output += f"🆔 ID: {paper.get_short_id()}\n"
        output += f"📝 Tiêu đề: {paper.title}\n"
        output += f"👥 Tác giả ({len(authors_list)}): {', '.join(authors_list)}\n"
        output += f"📅 Ngày xuất bản: {paper.published.strftime('%Y-%m-%d')}\n"
        if paper.updated:
            output += f"🔄 Cập nhật lần cuối: {paper.updated.strftime('%Y-%m-%d')}\n"
        output += f"🔗 Link: {paper.entry_id}\n"
        output += f"📥 PDF: {paper.pdf_url}\n"
        output += f"📂 Danh mục: {', '.join(paper.categories)}\n"
        if paper.comment:
            output += f"💬 Ghi chú: {paper.comment}\n"
        if paper.journal_ref:
            output += f"📰 Journal: {paper.journal_ref}\n"
        output += f"\n📖 ABSTRACT:\n{paper.summary}\n"
        
        return output
        
    except StopIteration:
        return f"Không tìm thấy bài báo với ID: {paper_id}"
    except Exception as e:
        return f"❌ Lỗi khi lấy chi tiết bài báo: {str(e)}"

@mcp.tool()
def download_paper_pdf(paper_id: str, user_id: str) -> str:
    """
    TẢI PDF BÀI BÁO TỪ ARXIV VỀ THƯ MỤC WORKSPACE CÁ NHÂN.
    - paper_id: Mã ID của bài báo trên arXiv (VD: "2301.00234")
    - user_id: ID người dùng để lưu vào workspace cá nhân
    Sử dụng tool này khi người dùng muốn tải/download PDF của bài báo.
    """
    try:
        client = arxiv.Client()
        
        clean_id = paper_id.strip()
        if clean_id.startswith("arxiv:"):
            clean_id = clean_id[6:]
        
        search = arxiv.Search(id_list=[clean_id])
        paper = next(client.results(search), None)
        
        if not paper:
            return f"Không tìm thấy bài báo với ID: {paper_id}"
        
        # Tạo tên file an toàn từ tiêu đề
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in paper.title)
        safe_title = safe_title.strip().replace(' ', '_')[:80]
        filename = f"arxiv_{clean_id.replace('/', '_')}_{safe_title}.pdf"
        
        user_workspace = os.path.join(WORKSPACE, user_id)
        os.makedirs(user_workspace, exist_ok=True)
        
        # Kiểm tra path traversal
        target_path = get_safe_path(user_id, filename)
        
        # Tải PDF
        paper.download_pdf(dirpath=user_workspace, filename=filename)
        
        return (
            f"✅ Đã tải PDF thành công!\n"
            f"📄 Tiêu đề: {paper.title}\n"
            f"📁 File: {filename}\n"
            f"📂 Thư mục: workspace/{user_id}/"
        )
        
    except StopIteration:
        return f"Không tìm thấy bài báo với ID: {paper_id}"
    except Exception as e:
        return f"❌ Lỗi khi tải PDF: {str(e)}"

if __name__ == "__main__":
    mcp.run()
