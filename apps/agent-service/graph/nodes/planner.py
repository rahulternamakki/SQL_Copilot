"""
Planner Agent Node for Governed AI Database Copilot.
Classifies query intent (read vs. write vs. ambiguous) and creates multi-step query execution plans.
"""

import re
import json
import logging
from typing import Dict, Any, List, Literal, Optional
from pydantic import BaseModel, Field
from config import settings
from graph.state import AgentState, PlannerOutput, PlanStep

logger = logging.getLogger("planner-node")


class PlannerAgent:
    def classify_and_plan(self, user_query: str) -> PlannerOutput:
        """
        Classify intent and generate structured execution plan using Groq LLaMA 3.3 70B (or heuristic fallback).
        """
        # Call Groq API if configured
        if settings.groq_api_key:
            try:
                from groq import Groq
                client = Groq(api_key=settings.groq_api_key)

                system_prompt = (
                    "You are the Planner Agent in an enterprise SQL database copilot. "
                    "Analyze the user's question and classify its intent into one of:\n"
                    "- 'read': Analytical or data retrieval queries (e.g., SELECT, aggregations, joins, counts).\n"
                    "- 'write': Mutating, updating, deleting, or altering operations (e.g., UPDATE, DELETE, INSERT, DROP, TRUNCATE).\n"
                    "- 'ambiguous': Queries with subjective or undefined business metrics (e.g., 'best employee', 'churn rate', 'popular products', 'high-value accounts').\n\n"
                    "Output a strict JSON object with this schema:\n"
                    "{\n"
                    "  \"intent\": \"read\" | \"write\" | \"ambiguous\",\n"
                    "  \"plan_steps\": [{\"step_number\": 1, \"description\": \"...\", \"target_table\": \"...\"}],\n"
                    "  \"clarification_question\": \"Optional clarification question if ambiguous\",\n"
                    "  \"reasoning\": \"Brief explanation\"\n"
                    "}"
                )

                chat = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"User Database Query: {user_query}"},
                    ],
                    model=settings.groq_model,
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )

                raw = chat.choices[0].message.content
                parsed = json.loads(raw or "{}")
                return PlannerOutput(**parsed)
            except Exception as e:
                logger.warning(f"Groq Planner API call failed: {e}. Using rule-based classification.")

        # Deterministic / Benchmark Fallback Heuristics
        q_lower = user_query.lower()
        words = set(re.findall(r"\b[a-zA-Z_]+\b", q_lower))

        # Check for Destructive / Write operations
        write_keywords = {"delete", "remove", "drop", "truncate", "update", "modify", "insert", "alter"}
        if any(kw in words for kw in write_keywords):
            return PlannerOutput(
                intent="write",
                plan_steps=[
                    PlanStep(step_number=1, description="Synthesize data modification SQL statement", target_table=None),
                    PlanStep(step_number=2, description="Trigger Safety Critic for dry run and HMAC confirmation token", target_table=None),
                ],
                reasoning="Detected destructive or mutating database operation.",
            )

        # Check for Ambiguous / Subjective Business Criteria (Step 2.4)
        ambiguous_keywords = [
            "best employee",
            "top employee",
            "mvp",
            "best performing",
            "churn rate",
            "churn",
            "popular product",
            "popular",
            "high-value",
            "high value",
        ]
        if any(ak in q_lower for ak in ambiguous_keywords):
            return PlannerOutput(
                intent="ambiguous",
                plan_steps=[
                    PlanStep(step_number=1, description="Intercept ambiguous business definition", target_table=None),
                    PlanStep(step_number=2, description="Request user clarification before executing query", target_table=None),
                ],
                clarification_question="The metric involves ambiguous business criteria. Please clarify your definition.",
                reasoning="Query contains subjective terms with multiple plausible metric formulations.",
            )

        # Default Read Plan
        return PlannerOutput(
            intent="read",
            plan_steps=[
                PlanStep(step_number=1, description="Retrieve schema context and business glossary from Qdrant", target_table=None),
                PlanStep(step_number=2, description="Synthesize PostgreSQL query using LLaMA 3.3 70B", target_table=None),
                PlanStep(step_number=3, description="Validate AST for read-only safety", target_table=None),
                PlanStep(step_number=4, description="Execute query via isolated MCP DB Server", target_table=None),
                PlanStep(step_number=5, description="Generate natural-language executive summary", target_table=None),
            ],
            reasoning="Analytical read query.",
        )


planner_agent = PlannerAgent()


def planner_node(state: AgentState) -> Dict[str, Any]:
    """LangGraph node wrapper for Planner Agent."""
    user_query = state.get("user_query", "")
    output = planner_agent.classify_and_plan(user_query)

    logger.info(f"Planner classified query as '{output.intent}' (Reason: {output.reasoning})")
    return {
        "intent": output.intent,
        "plan_steps": [s.model_dump() for s in output.plan_steps],
        "clarification_question": output.clarification_question,
    }
