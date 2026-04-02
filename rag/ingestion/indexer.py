import uuid

from qdrant_client.http import models
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_text_splitters import MarkdownTextSplitter

from rag.core.storage import storage
from rag.ingestion.pdf_loader import load_pdf_text
from rag.ingestion.text_splitter import get_parent_documents

def run_ingestion(file_path: str, collection_name: str):
    client = storage.get_client()
    print(f"--- Đang khởi tạo/làm sạch collection: {collection_name} ---")

    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=384, # THAY ĐỔI: Phải khớp với dimension của embedding_model bạn dùng
            distance=models.Distance.COSINE
        )
    )

    print("--- Đang đọc file PDF và trích xuất Markdown ---")
    raw_md_text = load_pdf_text(file_path)
    
    print("--- Đang phân tách cấu trúc thành các Điều (Parent) ---")
    parent_docs = get_parent_documents(raw_md_text)

    vectorstore = storage.get_vectorstore()
    store = storage.get_docstore()

    child_splitter = MarkdownTextSplitter(chunk_size=400, chunk_overlap=50)

    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=store,
        child_splitter=child_splitter,
    )
    
    print(f"--- Đang nạp {len(parent_docs)} Điều vào hệ thống (Qdrant + Docstore) ---")
    
    # Tạo UUID duy nhất cho mỗi Parent Document để ánh xạ giữa Qdrant và Docstore
    doc_ids = [str(uuid.uuid4()) for _ in parent_docs]
    
    # Tiến hành nạp: Tự động băm nhỏ Child nạp vào Qdrant, và lưu nguyên Parent vào LocalFileStore
    retriever.add_documents(parent_docs, ids=doc_ids)
    
    print("--- Hoàn tất quá trình nạp dữ liệu! ---")
    
    return retriever

# Nếu muốn test chạy thử file này độc lập
if __name__ == "__main__":
    file_pdf = "data/QCDT_2025_5445_QD-DHBK.pdf" # Trỏ đúng đường dẫn file của bạn
    run_ingestion(file_pdf, "quy_che_dhbk")