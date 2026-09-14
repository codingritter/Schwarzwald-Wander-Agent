from __future__ import annotations

from langgraph.graph import END, StateGraph

from .nodes import (
    analyze_requirements_node,
    collect_feedback_node,
    compare_routes_node,
    extract_itinerary_node,
    gather_requirements_node,
    research_critique_node,
    research_regions_node,
    should_continue,
    write_itinerary_node,
)
from .state import AgentState


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("gather_requirements", gather_requirements_node)
    builder.add_node("analyze_requirements", analyze_requirements_node)
    builder.add_node("research_regions", research_regions_node)
    builder.add_node("compare_routes", compare_routes_node)
    builder.add_node("collect_feedback", collect_feedback_node)
    builder.add_node("research_critique", research_critique_node)
    builder.add_node("extract_itinerary", extract_itinerary_node)
    builder.add_node("write_itinerary", write_itinerary_node)

    builder.set_entry_point("gather_requirements")

    builder.add_edge("gather_requirements", "analyze_requirements")
    builder.add_edge("analyze_requirements", "research_regions")
    builder.add_edge("research_regions", "compare_routes")

    builder.add_conditional_edges(
        "compare_routes",
        should_continue,
        {"collect_feedback": "collect_feedback", "extract_itinerary": "extract_itinerary"},
    )
    builder.add_edge("collect_feedback", "research_critique")
    builder.add_edge("research_critique", "compare_routes")
    builder.add_edge("extract_itinerary", "write_itinerary")
    builder.add_edge("write_itinerary", END)

    return builder.compile()
