import os
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model

class State(TypedDict):
    messages = Annotated[list, add_messages]
    safety_flag: bool   
    safety_notes: str   
graph_builder = StateGraph(State)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
llm = init_chat_model("google_genai:gemini-2.0-flash")

def safety_agent(state: State):
    user_entry = state["messages"][-1]  
    
    prompt = f"""
    You are a safety checker for a mental wellness journal.
    The user wrote:
    {user_entry}
    
    Your task:
    - Check if the entry shows signs of self-harm, suicidal ideation, violence, or extreme emotional distress.
    - Respond ONLY with one of the following formats:
    
    SAFE: [short explanation]
    UNSAFE: [short explanation]
    """
    
    response = llm.invoke(prompt)
    result_text = response.content.strip().upper()
    
    if result_text.startswith("UNSAFE"):
        return {
            "safety_flag": True,
            "safety_notes": response.content,
            "messages": state["messages"] + [response]
        }
    else:
        return {
            "safety_flag": False,
            "safety_notes": response.content,
            "messages": state["messages"] + [response]
        }

graph_builder.add_node("safety_agent", safety_agent)

graph_builder.add_edge(START, "safety_agent")
graph_builder.add_edge("safety_agent", END)

graph = graph_builder.compile()
