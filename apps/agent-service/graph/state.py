"""
State definitions for LangGraph orchestration in Governed AI Database Copilot.
"""

from typing import List, Dict, Any, Optional, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    step_number: int
    description: str
    target_table: Optional[str] = None


class PlannerOutput(BaseModel):
    intent: Literal["read", "write", "ambiguous"] = Field(
        description="Classification of query intent: read-only analytical query, write modification, or ambiguous concept requiring clarification."
    )
    steps: List[PlanStep] = Field(default_factory=list, description="Ordered decomposition of the query steps.")
    plan_steps: List[PlanStep] = Field(default_factory=list, description="Alias for steps.")
    reasoning: Optional[str] = Field(default=None, description="Explanation for classification.")
    ambiguity_reason: Optional[str] = Field(
        default=None, description="Explanation if intent is classified as ambiguous."
    )
    clarification_question: Optional[str] = Field(
        default=None, description="Optional clarification prompt if ambiguous."
    )

    def model_post_init(self, __context: Any) -> None:
        if not self.steps and self.plan_steps:
            self.steps = self.plan_steps
        elif not self.plan_steps and self.steps:
            self.plan_steps = self.steps
        if not self.ambiguity_reason and self.reasoning and self.intent == "ambiguous":
            self.ambiguity_reason = self.reasoning
        elif not self.reasoning and self.ambiguity_reason:
            self.reasoning = self.ambiguity_reason


class SchemaChunk(BaseModel):
    chunk_id: str
    chunk_type: Literal["table", "column_group", "glossary_term"]
    content: str
    table_name: Optional[str] = None
    similarity_score: float = 0.0


class SQLGeneratorOutput(BaseModel):
    sql: str = Field(description="The complete, syntactically valid SQL statement.")
    tables_touched: List[str] = Field(description="List of all tables referenced in the query.")
    operation_type: Literal["SELECT", "UPDATE", "DELETE", "INSERT", "TRUNCATE", "DROP", "ALTER", "OTHER"] = Field(
        description="Type of SQL operation."
    )
    reasoning: str = Field(description="Brief explanation of how the SQL addresses the user question.")


class SafetyCriticOutput(BaseModel):
    risk_level: Literal["none", "low", "high"] = Field(
        description="'none' for SELECT, 'low' for scoped single-row write, 'high' for bulk write/delete/unconstrained update."
    )
    is_safe_to_execute_automatically: bool = Field(
        description="True only if risk is 'none' or pre-approved read query."
    )
    risk_reasons: List[str] = Field(default_factory=list, description="List of risk factors identified.")
    estimated_rows_affected: int = Field(default=0, description="Estimated row count affected by this operation.")
    requires_user_confirmation: bool = Field(default=False)
    plain_language_preview: Optional[str] = Field(
        default=None, description="Human-readable preview of what will change."
    )


class AgentState(TypedDict):
    """
    Global state passing through the LangGraph workflow:
    planner -> clarifier (interrupt) -> retriever -> sql_generator -> safety_critic -> executor -> explainer
    """
    connection_id: str
    user_query: str
    messages: List[Dict[str, str]]
    
    # Planner
    intent: Optional[Literal["read", "write", "ambiguous"]]
    plan_steps: List[Dict[str, Any]]
    
    # Clarifier
    clarification_question: Optional[str]
    user_clarification_response: Optional[str]
    
    # Retriever (RAG)
    retrieved_chunks: List[Dict[str, Any]]
    
    # SQL Generator
    generated_sql: Optional[str]
    operation_type: Optional[str]
    tables_touched: List[str]
    
    # Safety Critic ("Teller vs. Approver")
    risk_level: Optional[Literal["none", "low", "high"]]
    requires_confirmation: bool
    plain_language_preview: Optional[str]
    confirmation_token: Optional[str]
    user_confirmed: Optional[bool]
    
    # Executor & MCP
    execution_result: Optional[Dict[str, Any]]
    retry_count: int
    error_message: Optional[str]
    
    # Explainer
    final_summary: Optional[str]
