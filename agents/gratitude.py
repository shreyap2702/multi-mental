import os
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model

class State(TypedDict):
    messages = Annotated[list, add_messages]
    gratitude = str
    
graph_builder = StateGraph(State)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
llm = init_chat_model("google_genai:gemini-2.0-flash")

def gratitude_agent(state: State):
    user_entry =  state["messages"][-1]
    
    prompt = f"""
    The user wrote the following journal entry:
    {user_entry}
    
    Your task: extract and highlight the POSITIVE aspects of this entry.
    Focus on gratitude, small wins, or moments of hope.
    Return a short and empathetic reflection.
    """
    response = llm.invoke(prompt)
    
    return {
        "gratitude": response.content, 
        "messages": state["messages"] + [response]  
    }

graph_builder.add_node("gratitude_agent", gratitude_agent)

graph_builder.add_edge(START, "gratitude_agent")

graph_builder.add_edge("gratitude_agent", END)

graph = graph_builder.compile()