from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

def update_rag_data(old_data: dict, new_data: dict):
    if not old_data:
        old_data = {}
    if not new_data:
        return old_data
    return {**old_data, **new_data}

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    next_agent: str

    rag_data: Annotated[dict, update_rag_data]