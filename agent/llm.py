import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def _make_llm(model: str, **kwargs) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        base_url=OPENROUTER_BASE_URL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        **kwargs
    )

DEFAULT_MODEL = os.getenv("MODEL", "nvidia/nemotron-3-super-120b-a12b:free")

supervisor_llm   = _make_llm(os.getenv("SUPERVISOR_MODEL", DEFAULT_MODEL))
rag_llm          = _make_llm(os.getenv("RAG_MODEL",        DEFAULT_MODEL), temperature=0)
workspace_llm    = _make_llm(os.getenv("WORKSPACE_MODEL",  DEFAULT_MODEL), temperature=0)
schedule_llm     = _make_llm(os.getenv("SCHEDULE_MODEL",   DEFAULT_MODEL), temperature=0)
responder_llm    = _make_llm(os.getenv("RESPONDER_MODEL",  DEFAULT_MODEL))
research_llm     = _make_llm(os.getenv("RESEARCH_MODEL",   DEFAULT_MODEL), temperature=0.1)