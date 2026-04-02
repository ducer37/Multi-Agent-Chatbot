import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def _make_llm(model: str, **kwargs) -> ChatGroq:
    return ChatGroq(
        model=model,
        api_key=os.getenv("GROQ_API_KEY"),
        **kwargs
    )

supervisor_llm   = _make_llm(os.getenv("SUPERVISOR_MODEL", "llama-3.3-70b-versatile"))
rag_llm          = _make_llm(os.getenv("RAG_MODEL",        "llama-3.3-70b-versatile"), temperature=0)
workspace_llm    = _make_llm(os.getenv("WORKSPACE_MODEL",  "qwen/qwen3-32b"),          temperature=0)
schedule_llm     = _make_llm(os.getenv("SCHEDULE_MODEL",   "qwen/qwen3-32b"),          temperature=0)
responder_llm    = _make_llm(os.getenv("RESPONDER_MODEL",  "llama-3.3-70b-versatile"))