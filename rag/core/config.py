import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "quy_che_dhbk")
    
    EMBEDDING_MODEL_DIR: str = os.getenv("EMBEDDING_MODEL_DIR","rag/core/onnx_model/bge-m3")
    
    DEVICE: str = os.getenv("DEVICE", "cpu") 

settings = Settings()