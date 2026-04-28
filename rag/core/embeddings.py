from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
import os

def get_embedding_model():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cache_path = os.path.join(base_dir, "fastembed_cache")
    
    embeddings = FastEmbedEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        cache_dir=cache_path
    )
    return embeddings