"""
Planner Agent Node for Governed AI Database Copilot.
Classifies query intent into 'read', 'write', or 'ambiguous' and decomposes multi-step questions.
"""

import json
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from config import settings
from graph.state import AgentState, PlannerOutput, PlanStep

logger = logging.getLogger("planner-node")


class PlannerAgent:
    def classify_and_plan(self, user_query: str, glossary_terms: List[Dict[str, Any]] = None) -> PlannerOutput:
        """
        Classify query intent and break down steps using Groq API (or heuristic fallback).
        """
        query_lower = user_query.lower()
        glossary_terms = glossary_terms or []

        # Check for explicit ambiguous terms flagged in glossary (e.g. 'best employee')
        ambiguous_terms = [
            t.get("term", "").lower()
            for t in glossary_terms
            if t.get("is_ambiguous", False) or "ambiguous" in t.get("definition", "").lower()
        ]
        
        # Hardcoded core ambiguity benchmarks
        if "best employee" in query_lower or "top employee" in query_lower:
            return PlannerOutput(
                intent="ambiguous",
                steps=[PlanStep(step_number=1, description="Clarify evaluation criteria for 'best employee'")],
                ambiguity_reason="The term 'best employee' is ambiguous and could refer to highest sales revenue, most orders processed, or fastest customer support resolution.",
            )
        
        for ambig in ambiguous_terms:
            if ambig and ambig in query_lower:
                return PlannerOutput(
                    intent="ambiguous",
                    steps=[PlanStep(step_number=1, description=f"Clarify definition of '{ambig}' with user")],
                    ambiguity_reason=f"The concept '{ambig}' requires business clarification before query synthesis.",
                )

        # Call Groq if configured
        if settings.groq_api_key:
            try:
                from groq import Groq
                client = Groq(api_key=settings.groq_api_key)
                
                system_prompt = (
                    "You are the Planner Agent in an enterprise database copilot. "
                    "Analyze the user's question and classify its intent into exactly one of:\n"
                    "- 'read': analytical queries, aggregations, SELECT statements, reporting.\n"
                    "- 'write': data modifications, INSERT, UPDATE, DELETE, DROP, TRUNCATE.\n"
                    "- 'ambiguous': queries with ill-defined business metrics, subjective terms (e.g. 'best employee', 'churn rate' without formula), or unclear scope.\n\n"
                    "Respond with a strict JSON object matching schema:\n"
                    "{\"intent\": \"read\"|\"write\"|\"ambiguous\", \"steps\": [{\"step_number\": 1, \"description\": \"...\", \"target_table\": \"...\"}], \"ambiguity_reason\": \"...\"}"
                )

                chat = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"User Query: {user_query}"},
                    ],
                    model=settings.groq_model,
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )

                raw = chat.choices[0].message.content
                parsed = json.loads(raw or "{}")
                return PlannerOutput(**parsed)
            except Exception as e:
                logger.warning(f"Groq Planner call failed: {e}. Using deterministic classifier.")

        # Deterministic Heuristic Classifier
        write_keywords = ["delete", "remove", "drop", "update", "insert", "modify", "set ", "truncate", "alter"]
        if any(w in query_lower for w in write_keywords):
            return PlannerOutput(
                intent="write",
                steps=[
                    PlanStep(step_number=1, description="Perform dry-run inspection to estimate affected rows", target_table="customers"),
                    PlanStep(step_number=2, description="Generate plain language preview for user confirmation"),
                ],
                ambiguity_reason=None,
            )

        return PlannerOutput(
            intent="read",
            steps=[
                PlanStep(step_number=1, description="Retrieve relevant schema tables and business rules"),
                PlanStep(step_number=2, description="Generate AST-validated read-only SELECT query"),
            ],
            ambiguity_reason=None,
        )


planner_agent = PlannerAgent()


def planner_node(state: AgentState) -> Dict[str, Any]:
    """LangGraph node wrapper for Planner Agent."""
    user_query = state.get("user_query", "")
    output = planner_agent.classify_and_plan(user_query)
    
    return {
        "intent": output.intent,
        "plan_steps": [s.model_dump() for s in output.steps],
        "clarification_question": output.ambiguity_reason if output.intent == "ambiguous" else None,
    }
