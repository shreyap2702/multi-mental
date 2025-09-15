import os
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model

class State(TypedDict):
    messages = Annotated[list, add_messages]
    plan: str   # storing the planned schedule/steps
    
graph_builder = StateGraph(State)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
llm = init_chat_model("google_genai:gemini-2.0-flash")

def planner_agent(state: dict):
    messages = state.get("messages", [])
    user_entry = messages[-1] if messages else state.get("tasks", "")
    
    prompt = f"""
    The user shared the following journal entry:
    {user_entry}
    
    Your task: act like a gentle planner.
    - Create a supportive and realistic day plan
    - Cover key tasks without making it overwhelming
    - Keep it short (2–3 sentences)
    - Ensure it promotes both productivity and mental well-being
    """
    
    response = llm.invoke(prompt)
    
    return {
        "plan": response.content,
        "messages": state["messages"] + [response]
    }

graph_builder.add_node("planner_agent", planner_agent)

graph_builder.add_edge(START, "planner_agent")
graph_builder.add_edge("planner_agent", END)

graph = graph_builder.compile()
