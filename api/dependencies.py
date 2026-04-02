from fastapi import Request
from services.mcp_client import MCPClient

def get_agent(request: Request):
    """Lấy thực thể LangGraph Agent duy nhất từ app.state."""
    return request.app.state.agent

def get_mcp(request: Request):
    """Lấy thực thể MCP Client duy nhất từ app.state."""
    return request.app.state.mcp