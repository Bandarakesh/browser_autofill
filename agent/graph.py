from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import (
    analyze_form,
    process_user_response,
    map_data,
    generate_question,
    generate_actions
)

def route_after_mapping(state: AgentState) -> str:
    if state.get("status") == "ask":
        return "generate_question"
    return "generate_actions"

# Define the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("process_user_response", process_user_response)
workflow.add_node("analyze_form", analyze_form)
workflow.add_node("map_data", map_data)
workflow.add_node("generate_question", generate_question)
workflow.add_node("generate_actions", generate_actions)

# Set entry point
workflow.set_entry_point("process_user_response")

# Add edges
workflow.add_edge("process_user_response", "analyze_form")
workflow.add_edge("analyze_form", "map_data")

# Conditional routing
workflow.add_conditional_edges(
    "map_data",
    route_after_mapping,
    {
        "generate_question": "generate_question",
        "generate_actions": "generate_actions"
    }
)

workflow.add_edge("generate_question", END)
workflow.add_edge("generate_actions", END)

# Compile graph
app = workflow.compile()
