"""
Explainer Agent Node for Governed AI Database Copilot.
Converts raw query execution output into a concise natural-language summary and key takeaways.
"""

import logging
from typing import Dict, Any
from config import settings
from graph.state import AgentState

logger = logging.getLogger("explainer-node")


class ExplainerAgent:
    def explain_results(self, user_query: str, sql: str, result_data: Dict[str, Any]) -> str:
        """
        Synthesize natural-language summary using Groq LLM (or deterministic summary).
        """
        row_count = result_data.get("row_count", 0)
        columns = result_data.get("columns", [])
        rows = result_data.get("rows", [])
        sample_rows_str = str(rows[:5])

        if settings.groq_api_key:
            try:
                from groq import Groq
                client = Groq(api_key=settings.groq_api_key)

                system_prompt = (
                    "You are the Explainer Agent in an AI Database Copilot. "
                    "Provide a crisp, clear 2-3 sentence executive answer to the user's question based on the query results. "
                    "Highlight the primary takeaway and mention exact numerical values or key findings."
                )

                user_prompt = (
                    f"User Question: {user_query}\n"
                    f"Executed SQL: {sql}\n"
                    f"Total Rows: {row_count}\n"
                    f"Columns: {columns}\n"
                    f"Sample Data: {sample_rows_str}"
                )

                chat = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    model=settings.groq_model,
                    temperature=0.0,
                )

                summary = chat.choices[0].message.content
                if summary:
                    return summary.strip()
            except Exception as e:
                logger.warning(f"Groq Explainer call failed: {e}")

        # Deterministic Summary Formatter
        if row_count == 1 and len(columns) == 1:
            val = rows[0][0] if rows and rows[0] else "0"
            col_name = columns[0].replace("_", " ")
            return f"The calculation for **{col_name}** resulted in **{val}**."
        elif row_count > 0:
            return f"Query returned **{row_count} matching records**. The requested data has been compiled into the table below."
        else:
            return "Query executed successfully, but found 0 matching records for the specified criteria."


explainer_agent = ExplainerAgent()


def explainer_node(state: AgentState) -> Dict[str, Any]:
    """LangGraph node wrapper for Explainer Agent."""
    user_query = state.get("user_query", "")
    sql = state.get("generated_sql", "")
    exec_result = state.get("execution_result") or {}

    summary = explainer_agent.explain_results(user_query, sql, exec_result)

    return {
        "final_summary": summary,
        "messages": state.get("messages", []) + [{"role": "assistant", "content": summary}],
    }
