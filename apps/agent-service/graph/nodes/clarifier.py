"""
Clarifier Agent Node for Governed AI Database Copilot.
Handles ambiguous business concepts by halting execution and soliciting explicit user clarification.
"""

import json
import logging
from typing import Dict, Any, List
from config import settings
from graph.state import AgentState

logger = logging.getLogger("clarifier-node")


class ClarifierAgent:
    def formulate_clarification(self, user_query: str, reason: str) -> Dict[str, Any]:
        """
        Formulate clear question and multiple-choice options for the user.
        """
        query_lower = user_query.lower()
        
        if "best employee" in query_lower or "top employee" in query_lower:
            return {
                "question": "How would you like to define 'best employee'?",
                "options": [
                    {"label": "Highest Total Sales Revenue", "hint": "SUM(orders.total_amount) by employee/agent"},
                    {"label": "Most Orders Processed", "hint": "COUNT(orders.id) completed"},
                    {"label": "Customer Satisfaction / Fastest Support", "hint": "Based on refund & support resolution"},
                ],
                "explanation": "The database contains sales, order volume, and support tables. Please select the business metric to query.",
            }
        elif "churn" in query_lower:
            return {
                "question": "Which definition of customer churn should we apply?",
                "options": [
                    {"label": "Inactive for 90+ Days", "hint": "No order placed in last 90 days"},
                    {"label": "Inactive for 180+ Days", "hint": "Standard e-commerce 6-month threshold"},
                    {"label": "Explicitly Marked 'churned'", "hint": "WHERE customers.status = 'churned'"},
                ],
                "explanation": "Churn can be calculated as inactivity period or explicit customer status.",
            }

        # LLM generated clarification if configured
        if settings.groq_api_key:
            try:
                from groq import Groq
                client = Groq(api_key=settings.groq_api_key)
                
                system_prompt = (
                    "You are the Clarifier Agent. The user's query is ambiguous. "
                    "Formulate a direct question and 2-3 concrete interpretation options for the user. "
                    "Respond with JSON: {\"question\": \"...\", \"options\": [{\"label\": \"...\", \"hint\": \"...\"}], \"explanation\": \"...\"}"
                )

                chat = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Query: {user_query}\nReason: {reason}"},
                    ],
                    model=settings.groq_model,
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
                return json.loads(chat.choices[0].message.content or "{}")
            except Exception as e:
                logger.warning(f"Groq clarifier call error: {e}")

        return {
            "question": f"Please clarify your request: '{user_query}'",
            "options": [
                {"label": "Option A: Overall Aggregation", "hint": "Aggregate across all active records"},
                {"label": "Option B: Detailed Breakdown", "hint": "Group by category and timeframe"},
            ],
            "explanation": reason or "The request requires specific business criteria before query execution.",
        }


clarifier_agent = ClarifierAgent()


def clarifier_node(state: AgentState) -> Dict[str, Any]:
    """LangGraph node wrapper for Clarifier Agent."""
    user_query = state.get("user_query", "")
    reason = state.get("clarification_question", "")
    clarification_payload = clarifier_agent.formulate_clarification(user_query, reason)

    return {
        "clarification_question": clarification_payload["question"],
        "messages": state.get("messages", []) + [
            {"role": "assistant", "content": f"⚠️ Clarification Needed: {clarification_payload['question']}"}
        ],
        "final_summary": f"Clarification Required: {clarification_payload['question']}",
    }
