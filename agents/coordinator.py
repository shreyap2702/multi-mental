import os
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from gratitude import gratitude_agent
from listener import listener_agent
from planner import planner_agent
from safety import safety_agent

class State(TypedDict):
    messages = Annotated[list, add_messages]
    gratitude: str
    raw_thoughts: str
    tasks: str
    pain_points: str
    
graph_builder = StateGraph(State)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
llm = init_chat_model("google_genai:gemini-2.0-flash")

def coordinator_agent(state: State):
    responses = {}

    
    if state.get("gratitude"):
        gratitude_result = gratitude_agent(state)
        responses["gratitude"] = gratitude_result["gratitude"]

   
    if state.get("raw_thoughts"):
        listener_result = listener_agent(state)
        responses["reflection"] = listener_result["reflection"]

    if state.get("tasks"):
        planner_result = planner_agent(state)
        responses["plan"] = planner_result["plan"]

    if state.get("pain_points"):
        safety_result = safety_agent(state)
        responses["safety"] = safety_result["safety_check"]

    summary_prompt = f"""
    The following agents provided responses:
    {responses}

    Write a short, empathetic summary of the user's diary entry.
    """
    final_summary = llm.invoke(summary_prompt).content

    return {
        **state,  
        "messages": state["messages"] + [final_summary],
        "coordinator_summary": final_summary,
        "agent_responses": responses,
    }


graph_builder.add_node("coordinator_agent", coordinator_agent)

graph_builder.add_edge(START, "coordinator_agent")
graph_builder.add_edge("coordinator_agent", END)

graph = graph_builder.compile()