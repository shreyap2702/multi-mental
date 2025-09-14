import os
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model

class State(TypedDict):
    messages = Annotated[list, add_messages]
    reflection: str

graph_builder = StateGraph(State)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
llm = init_chat_model("google_genai:gemini-2.0-flash")

def listener_agent(state: State):
    user_entry = state["messages"][-1]  # Last user message
    
    prompt = f"""
    The user shared the following journal entry:
    {user_entry}
    
    Your task: respond like an empathetic listener.
    - Acknowledge the emotions expressed
    - Avoid advice or solutions
    - Validate their feelings in a compassionate tone
    - Keep it short (2–3 sentences)
    """
    
    response = llm.invoke(prompt)
    
    return {
        "reflection": response.content,
        "messages": state["messages"] + [response]
    }

graph_builder.add_node("listener_agent", listener_agent)

graph_builder.add_edge(START, "listener_agent")
graph_builder.add_edge("listener_agent", END)

graph = graph_builder.compile()
