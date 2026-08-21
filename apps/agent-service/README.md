# Agent Service (`/apps/agent-service`)

The **Agent Service** is the central multi-agent orchestrator built with **FastAPI** and **LangGraph**. It directs user questions through a stateful reasoning pipeline without using monolithic abstractions (calling the Groq SDK and Qdrant client directly).

## Agent Pipeline Nodes
1. **Planner**: Classifies query intent into `read`, `write`, or `ambiguous`, and decomposes multi-step questions.
2. **Clarifier**: Triggers when intent is `ambiguous` to prompt the user and pause graph execution before any SQL is generated.
3. **Retriever**: Queries Qdrant for top-$k$ relevant schema chunks and business glossary terms.
4. **SQL Generator**: Produces syntactically validated SQL enforced via Pydantic schema validation.
5. **Safety Critic**: Independent risk reviewer enforcing teller-vs-approver validation, dry-run affected row count checks, and user confirmation modals for high-risk operations.
6. **Executor**: Dispatches validated queries to the MCP Database Server with a strict 1-retry self-correction loop.
7. **Explainer**: Translates raw results into plain-language summaries and structured tables.
