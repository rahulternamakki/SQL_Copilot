# Governed AI Database Copilot

> A multi-agent, RAG-grounded, MCP-powered database assistant designed for high reliability, zero hallucinated SQL, explicit ambiguity clarification, and deterministic write safety.

---

## 🏛️ System Architecture

```
 +-------------------------------------------------------------------------------+
 |                           Next.js Web Frontend (apps/web)                     |
 |  - Chat & Thought Stream    - Disambiguation Prompt    - Destructive Modal    |
 |  - Schema & Glossary View   - Audit Log Dashboard      - DB Connection Form   |
 +---------------------------------------+---------------------------------------+
                                         | REST / SSE (JSON)
                                         v
 +-------------------------------------------------------------------------------+
 |                         Agent Service (apps/agent-service)                    |
 |                                                                               |
 |   [Planner Node] ----(ambiguous)----> [Clarifier Node] (Interrupt to User)    |
 |          |                                                                    |
 |       (read/write)                                                            |
 |          v                                                                    |
 |   [Retriever Node] <===> [Qdrant Vector DB (infra)] (Schema + Glossary RAG)   |
 |          v                                                                    |
 |   [SQL Generator Node] (Groq LLaMA 3.3 70B + Pydantic JSON validation)        |
 |          v                                                                    |
 |   [Safety Critic Node] (Independent LLM check + dry-run SELECT COUNT(*))      |
 |          |                                                                    |
 |      (risk > none) ----> [Confirmation Interrupt] (Requires User Token)       |
 |          v                                                                    |
 |   [Executor Node] <====================+                                      |
 |          v                             | Tool Protocol (JSON-RPC)             |
 |   [Explainer Node]                     v                                      |
 +-------------------------------------------------------------------------------+
                                          |
                                          v
 +-------------------------------------------------------------------------------+
 |                       MCP DB Server (apps/mcp-db-server)                      |
 |  - Encrypted Credential Vault (Fernet)                                        |
 |  - Scoped Tools: list_schema, run_select, run_write(token), dry_run_preview    |
 |  - AST-Level Read-Only & Scope Validation (sqlglot)                           |
 +---------------------------------------+---------------------------------------+
                                         | SQLAlchemy
                                         v
 +-------------------------------------------------------------------------------+
 |                     PostgreSQL Database (infra / seeded e-commerce)           |
 +-------------------------------------------------------------------------------+
```

---

## 📦 Repository Structure

```
├── /apps
│   ├── /web              # Next.js 15 App Router frontend (React 19, TypeScript, Tailwind)
│   ├── /agent-service    # Python backend (FastAPI, LangGraph multi-agent orchestration, Groq, Qdrant)
│   └── /mcp-db-server    # Python MCP server exposing scoped DB tools & Fernet credential vault
├── /infra
│   ├── docker-compose.yml # PostgreSQL 16 (e-commerce seed) & Qdrant vector database
│   └── /init-db           # 01-seed-ecommerce.sql with customers, orders, products, refunds, etc.
├── /evals
│   ├── /dataset          # Benchmark test cases (straightforward, ambiguous, self-correction, destructive)
│   └── eval_runner.py    # Automated benchmark scoring harness
├── .github/workflows     # CI pipeline (Python tests, eval smoke test, Next.js build checks)
├── .env.example          # Template environment variable configuration
└── README.md             # This document
```

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- **Docker & Docker Compose** (Docker v20+)
- **Python 3.11+**
- **Node.js v20+** & `npm`

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your Groq API key:
```bash
cp .env.example .env
```

### 3. Spin Up Infrastructure (PostgreSQL & Qdrant)
```bash
cd infra
docker compose up -d
```
*Verify containers are running:*
- PostgreSQL: `localhost:5432` (Database: `ecommerce_demo`, User: `postgres`, Password: `postgres`)
- Qdrant REST: `http://localhost:6333`
- Qdrant Dashboard: `http://localhost:6333/dashboard`

### 4. Start MCP Database Server
```bash
cd apps/mcp-db-server
pip install -r requirements.txt
python server.py
```

### 5. Start Agent Service
```bash
cd apps/agent-service
pip install -r requirements.txt
python main.py
```

### 6. Start Web Frontend
```bash
cd apps/web
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to access the Governed AI Database Copilot dashboard.

---

## 🎯 Evaluation Benchmark Targets

| Metric | Target | Description |
|---|---|---|
| **Correct SQL on First Try** | ≥ 75% | Synthesizes syntactically correct and semantically accurate SQL without error. |
| **Correct after 1 Retry** | ≥ 90% | Successfully self-corrects on syntax/schema errors using the DB error feedback loop. |
| **Ambiguity Flagging Rate** | 100% | Never guesses on ill-defined terms (e.g. "best employee"); always interrupts to clarify. |
| **Destructive Query Interception** | 100% | Never executes unconfirmed `DELETE`/`UPDATE` or mass modifications without user confirmation token. |

To run the automated evaluation harness:
```bash
python evals/eval_runner.py
```

---

## 🔒 Security & Governance Principles

1. **Badge System (Zero Direct DB Access)**: AI agents only interact with database tools through the Model Context Protocol (MCP) server boundary.
2. **AST-Enforced Read Safety**: Queries are parsed with `sqlglot` to structurally reject non-read statements on analytical endpoints.
3. **Teller vs. Approver**: SQL generation and Safety Critic risk evaluation run in separate, independent steps.
4. **Commit + Logged Reverse Statement Rollback**: Write operations capture row before-states and log reversible statements with a 5-minute undo window.
