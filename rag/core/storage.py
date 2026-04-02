import os
import pickle
import logging
from langchain_qdrant import QdrantVectorStore
from langchain_classic.storage import LocalFileStore, EncoderBackedStore
from rag.core.qdrant_client import get_qdrant_client
from rag.core.embeddings import get_embedding_model

logger = logging.getLogger(__name__)

class RAGStorage:
    def __init__(self, collection_name: str, store_dir: str = "rag_docstore"):
        client = get_qdrant_client()
        embedding_model = get_embedding_model()
        
        if client is None:
            raise ConnectionError("Không thể kết nối đến Qdrant.")

        self.collection_name = collection_name
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.store_path = os.path.join(base_dir, store_dir)
        os.makedirs(self.store_path, exist_ok=True)
        
        self.vectorstore = QdrantVectorStore(
            client=client,
            collection_name=self.collection_name,
            embedding=embedding_model,
        )
        
        underlying_store = LocalFileStore(self.store_path)
        self.docstore = EncoderBackedStore(
            store=underlying_store,
            key_encoder=lambda k: k,
            value_serializer=pickle.dumps,
            value_deserializer=pickle.loads
        )
        
        logger.info(f"Đã khởi tạo RAGStorage cho collection: {collection_name}")

    def get_client(self):
        return self.client 

    def get_vectorstore(self):
        return self.vectorstore

    def get_docstore(self):
        return self.docstore

storage = RAGStorage(collection_name="quy_che_dhbk")