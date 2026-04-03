<p align="center">
  <h1 align="center">🤖 HUST Multi-Agent Chatbot</h1>
  <p align="center">
    Hệ thống chatbot đa tác nhân thông minh dành cho sinh viên ĐHBK Hà Nội
    <br/>
    <em>Kiến trúc Supervisor — Worker — Responder | Model Context Protocol | RAG</em>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/LangGraph-Orchestration-blue" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/Groq-LLM-orange" alt="Groq"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Qdrant-Vector_DB-red" alt="Qdrant"/>
  <img src="https://img.shields.io/badge/MCP-Protocol-purple" alt="MCP"/>
</p>

---

## 📖 Giới Thiệu

**HUST Multi-Agent Chatbot** là hệ thống AI đa tác nhân (Multi-Agent System) được thiết kế theo kiến trúc **Supervisor-Worker** sử dụng **LangGraph** để điều phối. Hệ thống tích hợp **Model Context Protocol (MCP)** để kết nối các tool server chuyên biệt, cung cấp 3 khả năng chính:

| Khả năng | Agent phụ trách | Mô tả |
|---|---|---|
| 📁 **Quản lý File** | Workspace Agent | Tạo, xóa, liệt kê file local & Google Drive |
| 📅 **Đặt lịch trình** | Schedule Agent | Tạo lịch sự kiện, lịch di chuyển với Slot Filling |
| 📚 **Tra cứu quy chế** | RAG Agent | Tìm kiếm quy chế đào tạo ĐHBK qua vector search |

---

## 🏗️ Kiến Trúc Hệ Thống

### Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                         │
│  ┌───────────┐    ┌──────────────────────────────────────────┐  │
│  │  API      │    │         LangGraph State Machine          │  │
│  │  /chat    │───▶│                                          │  │
│  │  /status  │    │   START ──▶ Supervisor ──┬──▶ Worker ──┐ │  │
│  └───────────┘    │                          │             │ │  │
│                   │            FINISH ◀──────┤   Tools ◀───┘ │  │
│                   │              │           │               │  │
│                   │              ▼           └──▶ Cleanup ───│  │
│                   │          Responder ──▶ Cleanup ──▶ END   │  │
│                   └──────────────────────────────────────────┘  │
│                              │                                  │
│  ┌───────────────────────────┼───────────────────────────────┐  │
│  │         MCP Clients (stdio transport)                     │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │ File-Master│  │Schedule-   │  │Knowledge-Master    │  │  │
│  │  │ (7 tools)  │  │Master      │  │(RAG + Qdrant)      │  │  │
│  │  │            │  │(2 tools)   │  │(1 tool)            │  │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────┐  ┌─────────────────────────────────┐  │
│  │ PostgreSQL (Neon)    │  │ Qdrant Cloud                    │  │
│  │ Conversation Memory  │  │ Vector Store (quy_che_dhbk)     │  │
│  └──────────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Mô hình Orchestrator-Worker

Hệ thống áp dụng mô hình phân tách trách nhiệm rõ ràng:

| Vai trò | Node | Nhiệm vụ |
|---|---|---|
| 🧠 **Điều phối** | `supervisor` | Phân tích ý định user, routing đến agent phù hợp |
| 👷 **Thực thi** | `workspace_agent`, `schedule_agent`, `rag_agent` | Chỉ gọi tool, không trả lời trực tiếp cho user |
| 💬 **Phản hồi** | `responder` | Tổng hợp kết quả từ worker, tạo câu trả lời tự nhiên |
| 🧹 **Dọn dẹp** | `cleanup` | Xóa ToolMessage khỏi memory, lưu RAG data vào state |

---

## 🔄 Luồng Hoạt Động Chi Tiết

### Luồng chính (Main Flow)

```mermaid
graph TD
    A[👤 User gửi message] --> B[FastAPI /api/v1/chat]
    B --> C[LangGraph ainvoke]
    C --> D[🧠 Supervisor Node]
    
    D -->|workspace_agent| E[📁 Workspace Agent]
    D -->|schedule_agent| F[📅 Schedule Agent]
    D -->|rag_agent| G[📚 RAG Agent]
    D -->|FINISH| H[💬 Responder]
    
    E -->|has tool_calls| I[⚙️ Workspace Tools]
    I --> E
    E -->|no tool_calls| J[🧹 Cleanup]
    
    F -->|has tool_calls| K[⚙️ Schedule Tools]
    K --> F
    F -->|no tool_calls| J
    
    G -->|has tool_calls| L[⚙️ RAG Tools]
    L --> G
    G -->|no tool_calls| J
    
    H --> J
    J --> M[END ✅]
    M --> N[Trả kết quả về Client]
```

### Chi tiết từng bước

#### 1️⃣ Khởi động hệ thống (`main.py` — Lifespan)

```
1. Kết nối PostgreSQL (Neon Cloud) → tạo AsyncPostgresSaver cho conversation memory
2. Khởi tạo 3 MCP Server qua stdio transport:
   ├── File-Master      (server/mcp_server.py)      → 7 workspace tools
   ├── Schedule-Master   (server/schedule_server.py) → 2 schedule tools
   └── Knowledge-Master  (rag/mcp_server.py)        → 1 RAG search tool
3. Load LangChain tools từ mỗi MCP session (langchain-mcp-adapters)
4. Bind tools vào LLM tương ứng (llm.bind_tools)
5. Compile LangGraph StateGraph với checkpointer
6. Gắn compiled graph vào app.state.agent
```

#### 2️⃣ User gửi request

```
POST /api/v1/chat
Body: { "message": "Liệt kê file workspace", "thread_id": "session_01" }

→ Tạo HumanMessage, gọi agent.ainvoke() với thread_id config
→ PostgreSQL checkpointer tự động load/save conversation state
```

#### 3️⃣ Supervisor phân tích & routing

```python
# Supervisor sử dụng structured output (Pydantic) để đảm bảo routing chính xác
class RouteResponse(BaseModel):
    next_agent: Literal["workspace_agent", "schedule_agent", "rag_agent", "FINISH"]

# Quy tắc đặc biệt: Nếu message cuối là AI (không có tool_calls)
# → Worker đang hỏi user → auto FINISH để chuyển cho Responder
```

#### 4️⃣ Worker Agent thực thi

```
Worker nhận state → Gọi LLM (đã bind tools) → Có 2 kết quả:
├── Có tool_calls → Edge "continue" → ToolNode thực thi → Quay lại Worker
└── Không tool_calls → Edge "cleanup" → Cleanup Node
```

#### 5️⃣ Cleanup & Responder

```
Cleanup Node:
├── Trích xuất text từ ToolMessage → lưu vào state["rag_data"]
├── Xóa tất cả ToolMessage khỏi conversation (RemoveMessage)
└── Xóa AI message rỗng (chỉ chứa tool_calls, không có content)

Responder Node:
├── Đọc toàn bộ conversation history (đã được cleanup)
├── Tổng hợp kết quả tool thành câu trả lời tự nhiên bằng tiếng Việt
└── Trả về AIMessage cuối cùng cho user
```

### Luồng đặt lịch (Slot Filling)

Đây là luồng đặc biệt khi user cung cấp thông tin không đầy đủ:

```
User: "Đặt lịch học Giải tích"
  → Supervisor → schedule_agent
  → Agent thấy thiếu [date, time, location] → Trả lời text (hỏi user)
  → Edge: no tool_calls → cleanup → END

User: "Thứ 4, 7h sáng, phòng D3-201"
  → Supervisor nhận thấy AI vừa hỏi → tiếp tục routing schedule_agent
  → Agent đủ thông tin → Gọi create_event_schedule tool
  → Tool tạo file lịch → cleanup → Responder tổng hợp → END
```

---

## 📂 Cấu Trúc Thư Mục

```
MCP/
│
├── main.py                          # 🚀 Entrypoint: FastAPI app + Lifespan (khởi tạo MCP, DB, Graph)
├── requirements.txt                 # 📦 Danh sách dependencies
├── dockerfile                       # 🐳 Docker image config
├── docker-compose.yml               # 🐳 Docker Compose (RAG testing service)
├── .env                             # 🔐 Biến môi trường (API keys, DB URI, ...)
├── .gitignore                       # Git ignore rules
├── credentials.json                 # 🔑 Google OAuth2 credentials
├── token.json                       # 🔑 Google OAuth2 token (auto-generated)
│
├── agent/                           # 🤖 LangGraph Multi-Agent Core
│   ├── __init__.py
│   ├── graph.py                     #   Xây dựng & compile StateGraph (nodes + edges)
│   ├── state.py                     #   AgentState TypedDict (messages, next_agent, rag_data)
│   ├── llm.py                       #   Factory khởi tạo các ChatGroq LLM instances
│   ├── prompts.py                   #   System prompts cho từng agent (tiếng Việt)
│   ├── schema.py                    #   Pydantic models: EventSchedule, TravelSchedule
│   ├── edges.py                     #   Conditional edge: agent_should_continue()
│   ├── utils.py                     #   Utility: trim_messages (giới hạn context window)
│   └── nodes/                       #   Các node trong graph
│       ├── __init__.py              #     Export tất cả node functions
│       ├── supervisor.py            #     🧠 Phân loại ý định → routing (structured output)
│       ├── workspace.py             #     📁 Worker: quản lý file local + Google Drive
│       ├── schedule.py              #     📅 Worker: đặt lịch sự kiện/di chuyển
│       ├── rag.py                   #     📚 Worker: tra cứu quy chế ĐHBK
│       ├── responder.py             #     💬 Tổng hợp kết quả → trả lời user
│       └── cleanup.py               #     🧹 Xóa ToolMessage, lưu rag_data
│
├── api/                             # 🌐 FastAPI REST Layer
│   ├── routes.py                    #   POST /api/v1/chat, GET /api/v1/status
│   ├── schema.py                    #   Pydantic: ChatRequest, ChatResponse
│   └── dependencies.py              #   Dependency Injection: get_agent(), get_mcp()
│
├── server/                          # 🔌 MCP Tool Servers (chạy qua stdio)
│   ├── __init__.py
│   ├── mcp_server.py                #   File-Master: 7 tools (CRUD file local + Google Drive)
│   └── schedule_server.py           #   Schedule-Master: 2 tools (event + travel schedule)
│
├── services/                        # ⚙️ Shared Services
│   ├── __init__.py
│   ├── mcp_client.py                #   MCPClient: kết nối MCP server, load LangChain tools
│   └── drive_service.py             #   Google Drive API wrapper (OAuth2, CRUD)
│
├── rag/                             # 📚 RAG Pipeline (Retrieval-Augmented Generation)
│   ├── __init__.py
│   ├── mcp_server.py                #   Knowledge-Master: 1 tool (search_internal_knowledge)
│   ├── core/                        #   Lõi RAG
│   │   ├── config.py                #     Settings: Qdrant URL, API key, embedding model
│   │   ├── embeddings.py            #     FastEmbed: paraphrase-multilingual-MiniLM-L12-v2
│   │   ├── qdrant_client.py         #     QdrantClient factory (kết nối Qdrant Cloud)
│   │   └── storage.py               #     RAGStorage: QdrantVectorStore + LocalFileStore (docstore)
│   ├── ingestion/                   #   Nạp dữ liệu
│   │   ├── pdf_loader.py            #     Đọc PDF → Markdown (pymupdf4llm)
│   │   ├── text_splitter.py         #     Tách theo Chương/Điều → Parent Documents
│   │   └── indexer.py               #     ParentDocumentRetriever: index vào Qdrant + docstore
│   └── retrieval/                   #   Truy vấn
│       └── retriever.py             #     Similarity search → trả Parent Document gốc
│
├── data/                            # 📄 Dữ liệu nguồn
│   └── QCDT_2025_5445_QD-DHBK.pdf  #   Quy chế đào tạo ĐHBK Hà Nội 2025
│
├── workspace/                       # 📁 Thư mục lưu file do Agent tạo ra
│
├── tests/                           # 🧪 Test Scripts
│   ├── test_multi_agent.py          #   Integration test: gửi request qua API
│   └── main_host.py                 #   CLI test trực tiếp (legacy)
│
├── evaluation/                      # 📊 Đánh giá chất lượng RAG
│   └── notebook/                    #   Jupyter notebooks (RAGAS evaluation)
│
├── fastembed_cache/                  # 💾 Cache model embedding đã tải
└── rag_docstore/                    # 💾 LocalFileStore lưu Parent Documents
```

---

## ⚙️ Tech Stack

### Core Framework

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| **Orchestration** | [LangGraph](https://github.com/langchain-ai/langgraph) | State machine điều phối multi-agent graph |
| **LLM Provider** | [Groq](https://groq.com/) (LPU Inference) | Chạy các model LLM với tốc độ cao |
| **LLM Models** | `llama-3.3-70b-versatile`, `qwen/qwen3-32b` | Supervisor/Responder dùng Llama, Worker dùng Qwen |
| **Tool Protocol** | [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) | Giao thức chuẩn kết nối LLM ↔ Tool Servers |
| **MCP Adapter** | `langchain-mcp-adapters` | Chuyển MCP tools → LangChain Tools |

### Backend & API

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| **Web Framework** | [FastAPI](https://fastapi.tiangolo.com/) | REST API server async |
| **ASGI Server** | [Uvicorn](https://www.uvicorn.org/) | Production ASGI server |
| **Validation** | [Pydantic](https://docs.pydantic.dev/) | Request/Response schema validation |

### Data & Storage

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| **Vector DB** | [Qdrant Cloud](https://qdrant.tech/) | Lưu trữ & tìm kiếm vector embeddings |
| **Embedding** | `paraphrase-multilingual-MiniLM-L12-v2` (FastEmbed/ONNX) | Chuyển text → vector 384 chiều, hỗ trợ đa ngôn ngữ |
| **Conversation Memory** | [PostgreSQL (Neon)](https://neon.tech/) | Lưu trữ bền vững lịch sử hội thoại (checkpointer) |
| **Document Store** | `LocalFileStore` | Lưu Parent Documents cho Parent-Child retrieval |

### RAG Pipeline

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| **PDF Parser** | `pymupdf4llm` | Đọc PDF → Markdown (bảo toàn layout + bảng biểu) |
| **Text Splitter** | Custom regex + `MarkdownTextSplitter` | Tách theo cấu trúc Chương/Điều (Parent-Child) |
| **Retrieval** | `ParentDocumentRetriever` | Tìm child chunk → trả về nguyên Điều (parent) |
| **Search** | Cosine Similarity (threshold ≥ 0.4) | Semantic search trên Qdrant |

### External APIs

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| **Cloud Storage** | Google Drive API v3 | Upload, list, delete file trên Drive |
| **Auth** | Google OAuth2 | Xác thực quyền truy cập Drive |
| **Observability** | [LangSmith](https://smith.langchain.com/) | Tracing & debugging LangGraph execution |

---

## 🔌 MCP Tool Servers

### File-Master (`server/mcp_server.py`) — 7 Tools

| Tool | Input | Chức năng |
|---|---|---|
| `write_text_file` | `filename`, `content` | Tạo/ghi đè file text (.py, .txt, .md, .html) |
| `execute_python_agent` | `script` | Thực thi Python script để tạo file phức tạp (.docx, .xlsx, .pdf) |
| `list_local_files` | — | Liệt kê file trong workspace local |
| `delete_file` | `filename` | Xóa file trong workspace local |
| `list_google_drive` | `limit` | Liệt kê file trên Google Drive |
| `upload_to_drive` | `filename` | Tải file từ workspace lên Google Drive |
| `delete_from_drive` | `file_id` | Xóa file trên Google Drive (cần File ID) |

### Schedule-Master (`server/schedule_server.py`) — 2 Tools

| Tool | Input Schema | Chức năng |
|---|---|---|
| `create_event_schedule` | `EventSchedule` (type, title, date, time, location) | Tạo lịch sự kiện (học, họp, hẹn) |
| `create_travel_schedule` | `TravelSchedule` (transport, departure, destination, date, time) | Tạo lịch di chuyển (máy bay, tàu, xe) |

### Knowledge-Master (`rag/mcp_server.py`) — 1 Tool

| Tool | Input | Chức năng |
|---|---|---|
| `search_internal_knowledge` | `query` | Tìm kiếm quy chế đào tạo ĐHBK trong Qdrant (top-3, cosine ≥ 0.4) |

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy

### Yêu cầu hệ thống

- **Python** ≥ 3.10
- **Git**
- Tài khoản **Groq**, **Qdrant Cloud**, **Neon PostgreSQL** (hoặc PostgreSQL local)
- (Tuỳ chọn) Google Cloud Console project với Drive API enabled

### 1. Clone & Cài đặt

```bash
# Clone repository
git clone <repository-url>
cd MCP

# Tạo virtual environment
python -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows

# Cài đặt dependencies
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường

Tạo file `.env` tại thư mục gốc:

```env
# === LLM Provider ===
GROQ_API_KEY=gsk_your_groq_api_key

# === Model Configuration (tuỳ chỉnh tên model) ===
SUPERVISOR_MODEL=llama-3.3-70b-versatile
RAG_MODEL=llama-3.3-70b-versatile
WORKSPACE_MODEL=qwen/qwen3-32b
SCHEDULE_MODEL=qwen/qwen3-32b
RESPONDER_MODEL=llama-3.3-70b-versatile

# === PostgreSQL (Conversation Memory) ===
POSTGRES_URI="postgresql://user:password@host/dbname?sslmode=require"

# === Qdrant Cloud (Vector DB) ===
QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=quy_che_dhbk

# === Embedding ===
EMBEDDING_MODEL_NAME=paraphrase-multilingual-MiniLM-L12-v2

# === LangSmith (Observability - tuỳ chọn) ===
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=Agent1
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# === App Settings ===
WORKSPACE_DIR=workspace
HOST=127.0.0.1
PORT=8000
DEVICE=cpu
```

### 3. Cấu hình Google Drive (tuỳ chọn)

```bash
# Đặt file credentials.json từ Google Cloud Console vào thư mục gốc
# Chạy xác thực lần đầu:
python services/drive_service.py
# → Mở trình duyệt → Đăng nhập Google → Tự động tạo token.json
```

### 4. Nạp dữ liệu RAG (chỉ cần chạy 1 lần)

```bash
# Nạp file PDF quy chế vào Qdrant
python -m rag.ingestion.indexer
# → Đọc PDF → Tách Chương/Điều → Embedding → Index vào Qdrant + Docstore
```

### 5. Khởi chạy Server

```bash
# Chạy FastAPI server (auto-reload khi dev)
python main.py

# Hệ thống sẽ:
# 1. Kết nối PostgreSQL ✅
# 2. Khởi động 3 MCP Server ✅
# 3. Load tools & compile graph ✅
# → Sẵn sàng tại http://127.0.0.1:8000
```

### 6. Kiểm tra & Sử dụng

```bash
# Kiểm tra server status
curl http://127.0.0.1:8000/api/v1/status

# Gửi tin nhắn
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Xin chào!", "thread_id": "my_session"}'

# Chạy test suite
python tests/test_multi_agent.py
```

### 7. Xem API Documentation

Truy cập **Swagger UI** tại: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---


## 📊 API Endpoints

| Method | Endpoint | Mô tả |
|---|---|---|
| `POST` | `/api/v1/chat` | Gửi tin nhắn cho Multi-Agent System |
| `GET` | `/api/v1/status` | Kiểm tra trạng thái server |

### Request Body (`POST /api/v1/chat`)

```json
{
  "message": "Đặt lịch học Giải tích sáng thứ 4",
  "thread_id": "ducer_session_101"
}
```

### Response Body

```json
{
  "answer": "Đã tạo lịch học Giải tích vào sáng thứ 4 cho bạn! 📅",
  "files_affected": ["lich_hoc_Giai_tich.txt"],
  "status": "success"
}
```

---

## 🧪 Testing

```bash
# Integration test (yêu cầu server đang chạy)
python tests/test_multi_agent.py

# Test RAG retrieval độc lập
python rag_test.py

# Test nạp dữ liệu RAG
python -m rag.ingestion.indexer
```

---

## 📝 Ghi Chú Kỹ Thuật

### Quản lý Memory

- **Conversation Memory**: PostgreSQL (Neon) qua `AsyncPostgresSaver` — lưu trữ bền vững toàn bộ lịch sử hội thoại theo `thread_id`.
- **Cleanup Strategy**: Sau mỗi lượt, `cleanup_node` xóa `ToolMessage` và AI message rỗng khỏi DB để giảm noise cho các lượt tiếp theo.
- **RAG Data**: Nội dung tool RAG được trích xuất và lưu vào `state["rag_data"]` (merge dạng dict) để RAG Agent có thể tham chiếu lại trong các lượt sau mà không cần gọi tool lại.
- **Message Trimming**: `get_trimmed_messages()` giới hạn context window gửi cho LLM (20 messages gần nhất) để tránh vượt token limit.

### Bảo mật

- **Workspace Sandbox**: Hàm `get_safe_path()` đảm bảo mọi thao tác file chỉ nằm trong thư mục `workspace/`, chặn path traversal.
- **Python Sandbox**: `execute_python_agent` chạy script trong subprocess riêng biệt với timeout 20s.
- **Sensitive Files**: `credentials.json`, `token.json`, `.env` đều nằm trong `.gitignore`.

---

## 📄 License

Dự án này được phát triển cho mục đích học tập và nghiên cứu tại Đại học Bách khoa Hà Nội (HUST).
