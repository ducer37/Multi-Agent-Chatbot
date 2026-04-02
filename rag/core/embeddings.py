from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
import os

def get_embedding_model():
    cache_path = os.path.join(os.getcwd(), "fastembed_cache")
    
    embeddings = FastEmbedEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        cache_dir=cache_path
    )
    return embeddings