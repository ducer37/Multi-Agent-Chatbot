import logging

from typing import List, Dict, Any, Optional
from rag.core.storage import storage

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def retrieve_documents(
    query: str,
    collection_name: str = "quy_che_dhbk", 
    top_k: int = 3, 
    score_threshold: float = 0.4 
) -> List[Dict[str, Any]]:

    try:
        vectorstore = storage.get_vectorstore()
        store = storage.get_docstore()


        child_results = vectorstore.similarity_search_with_score(
            query, 
            k=top_k,
            score_threshold=score_threshold
        )

        formatted_results = []
        seen_parent_ids = set() 

        for child_doc, score in child_results:
            parent_id = child_doc.metadata.get("doc_id")
            
            if parent_id and parent_id not in seen_parent_ids:
                seen_parent_ids.add(parent_id)
                
                parent_docs = store.mget([parent_id])
                
                if parent_docs and parent_docs[0]:
                    parent_doc = parent_docs[0]
                    formatted_results.append({
                        "score": round(float(score), 4),
                        "text": parent_doc.page_content,
                        "metadata": parent_doc.metadata
                    })
            
        return formatted_results
        
    except Exception as e:
        logger.error(f"Lỗi trong retrieve_documents: {e}")
        return []