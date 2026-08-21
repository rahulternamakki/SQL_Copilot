"""
LangGraph Multi-Agent Workflow for Governed AI Database Copilot.
Orchestrates Planner, Clarifier, Retriever, SQL Generator, Safety Critic, Executor, and Explainer nodes.
Halts on Ambiguity and Unconfirmed Destructive Writes.
"""

import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

from graph.state import AgentState
from graph.nodes.planner import planner_node
from graph.nodes.clarifier import clarifier_node
from graph.nodes.retriever import retriever_node
from graph.nodes.sql_generator import sql_generator_node
from graph.nodes.safety_critic import safety_critic_node
from graph.nodes.executor import executor_node
from graph.nodes.explainer import explainer_node

logger = logging.getLogger("graph-workflow")


def route_planner(state: AgentState) -> Literal["clarifier", "retriever"]:
    """Conditional routing based on query intent classification."""
    intent = state.get("intent", "read")
    if intent == "ambiguous":
        logger.info("Routing to Clarifier Agent (Ambiguity Detected)")
        return "clarifier"
    logger.info(f"Routing to Retriever Agent (Intent: {intent})")
    return "retriever"


def route_safety_critic(state: AgentState) -> Literal["executor", "end_for_confirmation"]:
    """Halt graph if write operation requires user confirmation."""
    requires_conf = state.get("requires_confirmation", False)
    if requires_conf:
        logger.info("Halting graph execution: Destructive write requires human authorization.")
        return "end_for_confirmation"
    return "executor"


def route_executor(state: AgentState) -> Literal["sql_generator", "explainer"]:
    """Conditional routing after execution: retry once on error, else proceed to explainer."""
    error = state.get("error_message")
    retry_count = state.get("retry_count", 0)

    if error and retry_count <= 1:
        logger.warning(f"Self-correction loop triggered (retry {retry_count}). Returning to SQL Generator.")
        return "sql_generator"
    return "explainer"


def build_agent_graph():
    """Construct the compiled LangGraph StateGraph."""
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("clarifier", clarifier_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("sql_generator", sql_generator_node)
    workflow.add_node("safety_critic", safety_critic_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("explainer", explainer_node)

    # Set Entry Point
    workflow.set_entry_point("planner")

    # Conditional branching from Planner
    workflow.add_conditional_edges(
        "planner",
        route_planner,
        {
            "clarifier": "clarifier",
            "retriever": "retriever",
        },
    )

    # Pipeline
    workflow.add_edge("clarifier", END)
    workflow.add_edge("retriever", "sql_generator")
    workflow.add_edge("sql_generator", "safety_critic")

    # Conditional Branching from Safety Critic (Halt on Write Confirmation)
    workflow.add_conditional_edges(
        "safety_critic",
        route_safety_critic,
        {
            "end_for_confirmation": END,
            "executor": "executor",
        },
    )

    # Conditional Branching from Executor (Self-Correction Loop)
    workflow.add_conditional_edges(
        "executor",
        route_executor,
        {
            "sql_generator": "sql_generator",
            "explainer": "explainer",
        },
    )

    workflow.add_edge("explainer", END)

    return workflow.compile()


# Global compiled app instance
agent_app = build_agent_graph()
