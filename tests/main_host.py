# main_host.py
import os
import json
import asyncio
from groq import Groq
from dotenv import load_dotenv
from services.mcp_client import MCPClient
from mcp.client.stdio import stdio_client
from mcp import ClientSession
from agent.prompts import SYSTEM_PROMPT
from agent.graph import create_graph

async def main():
    mcp_helper = MCPClient(os.path.abspath("server/mcp_server.py"))
    
    async with stdio_client(mcp_helper.server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_helper.session = session
            tools = await mcp_helper.get_tools()

            app = create_graph(mcp_helper, tools)
            
            print("⚡ HUST Hybrid Agent (LangGraph) Ready!")
            messages = []
            
            while True:
                user_input = input("\n👤 ducer: ")
                if user_input.lower() in ["exit", "quit"]: break
                
                messages.append(("user", user_input))
                # Chạy đồ thị
                result = await app.ainvoke({"messages": messages})
                
                # Cập nhật history và in kết quả
                messages = result["messages"]
                print(f"\n🤖 AI: {messages[-1].content}")

if __name__ == "__main__":
    asyncio.run(main())