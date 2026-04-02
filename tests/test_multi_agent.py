"""
Test Script cho HUST Multi-Agent System.
Chạy khi server đang hoạt động: python main.py
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"
THREAD_ID = "test_multi_agent"

def chat(message: str, thread_id: str = THREAD_ID):
    """Gửi tin nhắn và in kết quả."""
    print(f"\n{'='*60}")
    print(f"👤 ducer: {message}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": message, "thread_id": thread_id},
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🤖 AI: {data['answer']}")
            print(f"📊 Status: {data['status']}")
            if data.get('files_affected'):
                print(f"📁 Files: {data['files_affected']}")
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Không kết nối được server! Chạy 'python main.py' trước.")
    except requests.exceptions.Timeout:
        print("⏰ Request timeout (>60s)")

def test_status():
    """Test 0: Kiểm tra server sống không."""
    print("\n🔍 TEST 0: Kiểm tra server status")
    try:
        r = requests.get(f"{BASE_URL}/status", timeout=5)
        print(f"  ✅ Server: {r.json()}")
        return True
    except:
        print("  ❌ Server chưa chạy!")
        return False

if __name__ == "__main__":
    print("🧪 HUST Multi-Agent Test Suite")
    print("=" * 60)
    
    if not test_status():
        exit(1)
    
    # Test 1: Chào hỏi → Supervisor → FINISH (trả lời trực tiếp)
    print("\n🧪 TEST 1: Chào hỏi (expect: Supervisor → FINISH)")
    chat("Xin chào!")
    
    # Test 2: RAG → Supervisor → rag_agent → search_internal_knowledge
    print("\n🧪 TEST 2: Hỏi quy chế (expect: Supervisor → RAG Agent → tool)")
    chat("Quy chế đào tạo HUST quy định gì về điểm rèn luyện?")
    
    # Test 3: Workspace → Supervisor → workspace_agent → list_local_files
    print("\n🧪 TEST 3: Liệt kê file (expect: Supervisor → Workspace Agent → tool)")
    chat("Liệt kê các file trong workspace của tôi")
    
    # Test 4: Workspace → Tạo lịch
    print("\n🧪 TEST 4: Đặt lịch (expect: Supervisor → Workspace Agent → tool)")
    chat("Hãy liệt kê toàn bộ tool của bạn")
    
    print("\n" + "=" * 60)
    print("🏁 Hoàn tất test suite!")
