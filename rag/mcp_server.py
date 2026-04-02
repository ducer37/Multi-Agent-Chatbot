import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from rag.retrieval.retriever import retrieve_documents 

load_dotenv()

mcp = FastMCP("HUST-Knowledge-Master")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "quy_che_dhbk")

@mcp.tool()
def search_internal_knowledge(query: str) -> str:
    """
    TÌM KIẾM QUY CHẾ VÀ KIẾN THỨC NỘI BỘ ĐHBK (RAG).
    Bạn BẮT BUỘC PHẢI GỌI tool này khi người dùng hỏi về bất kỳ chủ đề nào sau đây:
    - Điểm số, quy đổi điểm (hệ 10, hệ 4, điểm chữ), đánh giá kết quả học tập.
    - Tín chỉ, xếp hạng năm học, khối lượng học tập.
    - Trọng số điểm thi, điểm quá trình, điểm cuối kỳ.
    - Các quy định, quy chế, thời gian, điều kiện học vụ, cảnh báo học tập.
    RÀNG BUỘC NGHIÊM NGẶT:
    1. TUYỆT ĐỐI KHÔNG sử dụng kiến thức nền để tự trả lời các vấn đề về điểm và tín chỉ.
    2. Khi trả lời về điểm, luôn kèm theo bảng quy đổi hoặc công thức nếu quy chế có cung cấp.
    3. Nếu không tìm thấy thông tin trong tool, hãy báo rõ là "Quy chế không đề cập" thay vì đoán.
    """
    try:
        results = retrieve_documents(
            query=query, 
            collection_name=COLLECTION_NAME, 
            top_k=3, 
            score_threshold=0.4
        )
        
        if not results:
            return "Không tìm thấy thông tin nào liên quan trong cơ sở dữ liệu."
            
        context_str = "Dưới đây là các thông tin trích xuất từ cơ sở dữ liệu nội bộ:\n\n"
        for i, doc in enumerate(results, 1):
            metadata = doc.get('metadata', {})
            source = metadata.get('source', 'Unknown')
            chapter = metadata.get('chapter', 'Chương N/A')
            article = metadata.get('article', 'Điều N/A')
            score = doc.get('score', 'N/A')
            text = doc.get('text', '')
            
            context_str += f"--- Kết quả {i} (Độ tương đồng: {score}) ---\n"
            context_str += f"Nguồn: {source} | {chapter} | {article}\n"
            context_str += f"Nội dung:\n{text}\n\n"
            
        return context_str
        
    except Exception as e:
        return f"❌ Lỗi khi truy vấn Qdrant: {str(e)}"

if __name__ == "__main__":
    mcp.run()