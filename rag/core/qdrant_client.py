from qdrant_client import QdrantClient
from rag.core.config import settings

def get_qdrant_client():
    """
    Khởi tạo kết nối tới Qdrant Server
    """
    try:
        client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=120,
        )
        print(f"--- Connected to Qdrant Cloud---")
        return client
    except Exception as e:
        print(f"--- Failed to connect to Qdrant: {e} ---")
        return None