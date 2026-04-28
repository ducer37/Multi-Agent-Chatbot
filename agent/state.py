from typing import Annotated, Sequence, TypedDict
from typing_extensions import NotRequired
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    next_agent: str
    
    user_id: str
    
    status: NotRequired[str]
    
    tool_descriptions: NotRequired[str]