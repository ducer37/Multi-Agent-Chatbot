from rag.retrieval.retriever import retrieve_documents

def main():
    query = "Sinh viên bị nâng 2 mức cảnh báo học tập trong trường hợp nào?"
    print(retrieve_documents(query))

# BẠN HÃY THÊM ĐÚNG 2 DÒNG NÀY VÀO CUỐI FILE:
if __name__ == "__main__":
    main()