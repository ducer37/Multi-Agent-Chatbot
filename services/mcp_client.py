# services/mcp_client.py
import os
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools 

class MCPClient:
    def __init__(self, server_path: str):
        self.server_params = StdioServerParameters(
            command="python", # Hoặc python3
            args=[server_path],
            env={**os.environ, "PYTHONPATH": "."}
        )

    @asynccontextmanager
    async def stdio_client(self):
        async with stdio_client(self.server_params) as (read, write):
            yield read, write

    @asynccontextmanager
    async def create_session(self, read, write):
        async with ClientSession(read, write) as session:
            yield session
            
    async def get_langchain_tools(self, session):
        """Trả về danh sách các LangChain Tools đã sẵn sàng để thực thi."""
        return await load_mcp_tools(session)