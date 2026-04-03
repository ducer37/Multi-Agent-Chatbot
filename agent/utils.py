from langchain_core.messages import trim_messages

def get_trimmed_messages(messages):
    return trim_messages(
        messages,
        max_tokens=20,          
        token_counter=len,      
        include_system=True,
        strategy="last", 
        start_on="human",
        allow_partial=False 
    )
