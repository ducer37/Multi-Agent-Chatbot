import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager, AsyncExitStack
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from dotenv import load_dotenv

load_dotenv()

from services.mcp_client import MCPClient
from agent.graph import create_multi_agent_graph
from api.routes import router

MCP_SERVERS = {
    "workspace": {"name": "File-Master",      "path": "server/mcp_server.py"},
    "schedule":  {"name": "Schedule-Master",   "path": "server/schedule_server.py"},
    "rag":       {"name": "Knowledge-Master",  "path": "rag/mcp_server.py"},
}

DB_URI = os.getenv("POSTGRES_URI")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 --- Đang khởi động HUST Multi-Agent API ---")
    
    exit_stack = AsyncExitStack()
    all_sessions = {}
    
    try:
        print("  🗄️ Đang kết nối PostgreSQL để lưu trữ trí nhớ...")
        connection_pool = AsyncConnectionPool(
            conninfo=DB_URI,
            max_size=20,
            kwargs={"autocommit": True}
        )

        pool = await exit_stack.enter_async_context(connection_pool)
        
        checkpointer = AsyncPostgresSaver(pool)
        
        await checkpointer.setup() 
        print("  ✅ Cơ sở dữ liệu trí nhớ đã sẵn sàng!")

        for role, server_info in MCP_SERVERS.items():
            print(f"  🔌 Đang kết nối MCP Server: {server_info['name']}...")
            
            client = MCPClient(server_info["path"])
            read, write = await exit_stack.enter_async_context(client.stdio_client())
            session = await exit_stack.enter_async_context(client.create_session(read, write))
            await session.initialize()
            
            all_sessions[role] = {"client": client, "session": session}
            print(f"  ✅ {server_info['name']} đã kết nối!")
        
        workspace_tools = await all_sessions["workspace"]["client"].get_langchain_tools(all_sessions["workspace"]["session"])
        schedule_tools = await all_sessions["schedule"]["client"].get_langchain_tools(all_sessions["schedule"]["session"])
        rag_tools = await all_sessions["rag"]["client"].get_langchain_tools(all_sessions["rag"]["session"])
        
        print(f"  📦 Workspace: {len(workspace_tools)} | Schedule: {len(schedule_tools)} | RAG: {len(rag_tools)} tools")
        
        langgraph_app = create_multi_agent_graph(workspace_tools, schedule_tools, rag_tools, checkpointer)
        app.state.agent = langgraph_app
        
        total = len(workspace_tools) + len(schedule_tools) + len(rag_tools)
        print(f"✅ Hệ thống Multi-Agent sẵn sàng! ({total} tools từ {len(MCP_SERVERS)} servers)")
        yield
        
    except Exception as e:
        print(f"❌ Lỗi khởi động hệ thống: {e}")
        raise
    finally:
        await exit_stack.aclose()
        print("🛑 Đã đóng tất cả kết nối MCP an toàn. Tạm biệt ducer!")

app = FastAPI(
    title="HUST Multi-Agent API",
    description="API đa tác nhân: Supervisor điều phối Workspace, Schedule và RAG Agent.",
    version="3.1.0",
    lifespan=lifespan
)

app.include_router(router)

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True, reload_excludes=["workspace/*", "token.json"])