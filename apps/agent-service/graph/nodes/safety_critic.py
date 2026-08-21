"""
Safety Critic Agent Node for Governed AI Database Copilot.
Independent inspector enforcing the 'Teller vs. Approver' principle.
Validates read-only AST safety, estimates row impacts, and tags risk levels.
"""

import logging
import sqlglot
from sqlglot import exp
from typing import Dict, Any, Literal
from graph.state import AgentState, SafetyCriticOutput

logger = logging.getLogger("safety-critic-node")


class SafetyCriticAgent:
    def inspect_sql(self, sql: str, operation_type: str) -> SafetyCriticOutput:
        """
        Inspect generated SQL AST and assign risk level.
        """
        try:
            parsed = sqlglot.parse_one(sql)
        except Exception as e:
            return SafetyCriticOutput(
                risk_level="high",
                is_safe_to_execute_automatically=False,
                risk_reasons=[f"SQL Syntax Error during AST parsing: {str(e)}"],
                estimated_rows_affected=0,
                requires_user_confirmation=True,
                plain_language_preview="Query rejected due to invalid syntax.",
            )

        root_key = parsed.key.upper() if parsed else "UNKNOWN"
        is_select = isinstance(parsed, (exp.Select, exp.Union)) and root_key in ["SELECT", "UNION"]
        has_forbidden = bool(parsed.find(exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter))

        if is_select and not has_forbidden:
            return SafetyCriticOutput(
                risk_level="none",
                is_safe_to_execute_automatically=True,
                risk_reasons=[],
                estimated_rows_affected=0,
                requires_user_confirmation=False,
                plain_language_preview="Read-only analytical query. Safe for automatic execution.",
            )

        # Destructive or Modifying operation detected
        is_destructive = root_key in ["DELETE", "DROP", "TRUNCATE"] or (root_key == "UPDATE" and not parsed.find(exp.Where))
        risk: Literal["none", "low", "high"] = "high" if is_destructive else "low"

        return SafetyCriticOutput(
            risk_level=risk,
            is_safe_to_execute_automatically=False,
            risk_reasons=[f"Modifying operation detected ({root_key}). User confirmation required."],
            estimated_rows_affected=1,
            requires_user_confirmation=True,
            plain_language_preview=f"This will execute a {root_key} statement on the database.",
        )


safety_critic_agent = SafetyCriticAgent()


def safety_critic_node(state: AgentState) -> Dict[str, Any]:
    """LangGraph node wrapper for Safety Critic Agent."""
    sql = state.get("generated_sql", "")
    op_type = state.get("operation_type", "SELECT")

    critique = safety_critic_agent.inspect_sql(sql, op_type)
    logger.info(f"Safety Critic evaluated SQL -> Risk: '{critique.risk_level}', Safe: {critique.is_safe_to_execute_automatically}")

    return {
        "risk_level": critique.risk_level,
        "requires_confirmation": critique.requires_user_confirmation,
        "plain_language_preview": critique.plain_language_preview,
    }
