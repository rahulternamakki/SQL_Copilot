# Governed AI Database Copilot — Step-by-Step Implementation Plan

A phase-by-phase build guide for the multi-agent, RAG-grounded, MCP-powered database assistant, mapped onto the 20-day solo build plan.

---

## 0. Before You Start — Environment & Repo Setup

**Goal:** a working skeleton you can build inside without re-plumbing later.

1. **Repo structure**
   ```
   /apps
     /web            → Next.js frontend
     /agent-service   → Python backend (LangGraph agents)
     /mcp-db-server   → MCP server exposing scoped DB tools
   /infra
     docker-compose.yml   → Postgres/MySQL sample DB, Qdrant, Redis (optional)
   /evals              → eval harness + test question sets
   ```
2. **Core stack decisions (from the plan, made concrete):**
   | Layer | Tool | Notes |
   |---|---|---|
   | Agent orchestration | **LangGraph** (Python) | State machine with explicit pause nodes for clarification/confirmation |
   | LLM calls | **Groq API** (`llama-3.3-70b-versatile`) | Free tier for dev & testing; swappable to Anthropic Claude in 1 line via `.env` later |
   | Structured output | **Pydantic** + Groq's tool-use / structured output | Forces SQL Generator and Safety Critic to return validated JSON, not free text |
   | DB access | **MCP server**, Python SDK (`mcp` package) | Only this process ever touches real DB credentials |
   | Vector store | **Qdrant** (self-hosted via Docker, or Qdrant Cloud free tier) | Namespace/collection per connected database |
   | Embeddings | Any solid embedding model (e.g. `voyage-3` via Voyage AI, or `text-embedding-3-small`) | Used for schema + glossary chunks and for the user's question |
   | Databases supported | **PostgreSQL** first, MySQL later | Postgres has the richest introspection tooling |
   | Frontend | **Next.js** (App Router) + Tailwind + shadcn/ui | Chat UI, confirmation modal, audit-log dashboard |
   | Secrets/credentials | Encrypted at rest (e.g. `libsodium`/`cryptography` Fernet) in your own DB, never passed to the LLM | A "credential vault" table, not env vars, since each user has their own DB |
   | Auth | Clerk / Auth.js (NextAuth) | You need user accounts before you need per-user DB connections |
   | LangChain | **Not used** — call the Groq SDK and Qdrant client directly | Fewer abstractions to explain under interview questioning; LangGraph alone covers orchestration, and the utility pieces (embeddings, chat calls) are thin enough to write directly |

3. **Local dev environment:** `docker-compose.yml` spinning up a sample Postgres (seeded with a small e-commerce dataset — customers/orders/products/refunds) + Qdrant. This becomes your demo database for the whole build.

---

## Phase 1 (Days 1–5): Foundations

**Deliverable:** a user can sign up, connect a database via credentials, and the system can introspect its schema and store a draft glossary.

### Step 1.1 — Connection UI + credential vault
- Build a "Connect Database" form (host, port, db name, user, password, SSL toggle).
- On submit: test the connection server-side, then encrypt and store credentials in a `connections` table (never in the browser, never in logs).
- Add a **read-only vs write-enabled** toggle at the connection level, defaulting to read-only — this is the "explicit opt-in per connection" from the safety section.

### Step 1.2 — MCP server with scoped DB tools
- Build `/apps/mcp-db-server` using the MCP Python SDK.
- Expose a small, fixed tool surface — not raw SQL execution as a free-for-all:
  - `list_schema(connection_id)`
  - `run_select(connection_id, sql)` — only allowed if the query parses as read-only
  - `run_write(connection_id, sql, confirmation_token)` — only allowed with a valid confirmation token issued after user approval
  - `begin_transaction / rollback / commit` helpers used internally by `run_write`
- This is the "badge system" from the plan: agents never get a raw DB connection string, only these tool calls.

### Step 1.3 — Schema introspection
- Use SQLAlchemy's `inspect()` (Postgres/MySQL) to pull tables, columns, types, foreign keys, and constraints.
- Store this as structured JSON per connection — this is your source of truth, refreshed every session per the plan's "never work from a stale schema" requirement.

### Step 1.4 — Auto-glossary draft
- One LLM call per connection: feed the schema JSON, ask the LLM (Groq `llama-3.3-70b-versatile`) to draft plain-language definitions for ambiguous or business-specific terms (e.g. "churned customer," "active order").
- Store as editable `glossary_terms` rows the user can correct in the UI before they're ever used in retrieval.

**End of Phase 1 checkpoint:** you can connect a DB, see its schema rendered in the UI, and see/edit an AI-drafted glossary. No agents yet.

---

## Phase 2 (Days 6–10): Core Agent Flow (Read Path)

**Deliverable:** a user can ask a plain-English read-only question and get back a correct query + results, including the ambiguity-clarification behavior.

### Step 2.1 — RAG ingestion pipeline
- Chunk the schema JSON (one chunk per table, one per column group) and the glossary (one chunk per term).
- Embed each chunk, upsert into a **Qdrant collection scoped to that connection_id** (per-tenant isolation from the plan).
- Trigger this pipeline on connect, and re-trigger on-demand ("refresh schema") rather than on every single session if that's too slow — but the *plan requires* a refresh-per-session check, so at minimum diff the live schema against the stored one at session start and re-embed only what changed.

### Step 2.2 — LangGraph state machine (read path first)
- Define the graph nodes: `planner → clarifier (conditional) → retriever → sql_generator → safety_critic → executor → explainer`.
- Start with just the read path: `planner → retriever → sql_generator → safety_critic → executor(select) → explainer`.
- Use LangGraph's conditional edges to branch on the Planner's classification (`read` / `write` / `ambiguous`).

### Step 2.3 — Planner agent
- System prompt: classify the user's message as `read`, `write`, or `ambiguous`; break multi-step asks into an ordered list of sub-questions.
- Output forced into a small Pydantic schema: `{ intent: "read"|"write"|"ambiguous", steps: [...] }`.

### Step 2.4 — Clarifier agent
- Only runs when `intent == "ambiguous"`.
- Given the user's question, checks for multiple valid interpretations (using the glossary + a lightweight heuristic/LLM check) and if found, returns a direct question to the user and **halts the graph** (LangGraph interrupt) until they respond.
- This is the "best employee" case from the plan — implement it as the first test case you hand-verify.

### Step 2.5 — Retriever agent (RAG)
- Embed the user's question, query the connection's Qdrant collection for top-k relevant schema/glossary chunks.
- Pass only those chunks forward — this is what keeps the SQL Generator's prompt small and grounded.

### Step 2.6 — SQL Generator agent
- Given the retrieved schema chunks + the user's question, generate SQL.
- Force output through Pydantic/Instructor into `{ sql: str, tables_touched: [...], operation_type: "SELECT"|"UPDATE"|"DELETE"|"INSERT" }` so a malformed query is caught by schema validation before it's even considered for execution.

### Step 2.7 — Executor (read-only for now)
- Calls the MCP server's `run_select` tool.
- On DB error, feed the error back to the SQL Generator for **exactly one** self-correction retry (per the plan), then fail gracefully with a plain-language explanation if it still fails.

### Step 2.8 — Explainer agent
- Converts raw rows into a short natural-language summary + a results table for the frontend.

**End of Phase 2 checkpoint:** the full read-only flow works end to end, including the clarification interrupt, and you can demo the "which customers haven't ordered in 90 days" example from the plan.

---

## Phase 3 (Days 11–15): Safety Layer (Write Path)

**Deliverable:** risky writes are previewed, require explicit confirmation, run inside a rollback-capable transaction, and are logged.

### Step 3.1 — Safety Critic agent
- Independent LLM call (deliberately separate from the SQL Generator, per the plan's "teller vs. approver" principle) that reviews the generated SQL + `operation_type` and assigns a risk level: `none` (SELECT), `low` (single-row scoped write), `high` (DELETE, mass UPDATE, no WHERE clause, sensitive table).
- Output forced into `{ risk: "none"|"low"|"high", reason: str, rows_affected_estimate: int }` — estimate row count via a `SELECT COUNT(*)` dry-run using the same WHERE clause before showing the preview.

### Step 3.2 — Confirmation flow
- If `risk != "none"`: Explainer generates the plain-language preview ("this will update 14 rows in orders, delete 2 in refunds") and the graph interrupts, returning a **pending action** to the frontend with a confirmation token.
- Frontend renders a confirmation modal showing the raw SQL (collapsible) + the plain-language diff.
- On user confirm, the token is sent back, and only then does the Executor call `run_write`.

### Step 3.3 — Transaction-wrapped writes + rollback
**Decision (locked in): commit + logged reverse statement**, not a held-open transaction. Reasoning:
- A held-open transaction with a timeout blocks/locks rows for other users of the same DB for the whole confirmation window — bad for anything beyond a single-user demo, and it doesn't survive a server restart mid-wait.
- Commit-then-log is safer for concurrent access and is what production systems actually do (it's how "undo send" works in most real tools).
- Implementation: before executing a write, the Safety Critic step already ran a dry-run `SELECT` to estimate rows affected (Step 3.1) — capture the **full before-state of those rows** (not just a count) at that point. After the write commits, store an auto-generated reverse statement (or the captured before-state, for a full row restore) in the `audit_log` row, with a rollback window (e.g. 5 minutes) during which the user can hit "Undo" to re-apply the reverse statement. After the window, the row is still visible in the audit log but no longer one-click reversible.
- This is now the single documented answer if an interviewer asks "how does rollback actually work" — no more open decision at build time.



### Step 3.4 — Permission toggles
- Connection-level: read-only vs write-enabled (already built in Phase 1) — enforce it at the MCP layer too, not just the UI, so a bypassed frontend can't skip it.
- Optionally: per-table write allow-list for extra caution on sensitive tables.

### Step 3.5 — Audit log
- Every prompt, generated SQL, risk assessment, confirmation decision, and outcome written to an `audit_log` table (connection_id, user_id, timestamp, prompt, sql, risk, confirmed_by_user, result, rolled_back).
- This log powers the dashboard in Phase 4 and is also your best interview artifact — screenshot it.

**End of Phase 3 checkpoint:** you can demo the "delete customers inactive 2 years" example — see the preview, confirm, watch it run in a transaction, and see it appear in the audit log.

---

## Phase 4 (Days 16–18): Trust & Proof

**Deliverable:** evidence the system actually works, not just a demo that works once.

### Step 4.1 — Self-correction retry loop (finish/harden)
- Confirm the exactly-one-retry rule from Step 2.7 is enforced everywhere (including write-path errors), and that a second failure returns a clear, honest explanation rather than a generic error.

### Step 4.2 — Audit log dashboard
- Simple table/list view in the frontend: filter by connection, risk level, date, confirmed/rolled-back status.

### Step 4.3 — Eval harness
- Build a fixed test set (20–40 questions) against your seeded sample DB, covering:
  - Straightforward reads (expect correct SQL first try)
  - Questions needing a self-correction retry (deliberately tricky phrasing)
  - Ambiguous questions (expect a clarification, not a guess)
  - Destructive queries (expect interception + confirmation, never silent execution)
- Score against the plan's own targets:
  | Metric | Target |
  |---|---|
  | Correct SQL on first try | ≥ 75% |
  | Correct after 1 self-correction retry | ≥ 90% |
  | Ambiguous questions correctly flagged | 100% |
  | Destructive queries correctly intercepted | 100% |
- Simplest implementation: a Python script that runs each test question through the graph programmatically and checks the output against an expected `operation_type`/`risk`/`clarification_expected` label — no need for a fancy eval framework to start.

**End of Phase 4 checkpoint:** you have a scored eval table you can show in an interview, with real numbers instead of "it worked when I tried it."

---

## Phase 5 (Days 19–20): Polish & Demo

1. Fix edge cases surfaced by the eval harness (this is where most of your remaining time should go).
2. Write the **README**: problem, architecture diagram, tech stack table, how to run locally (docker-compose up), eval results.
3. Draw the **architecture diagram** (agents, MCP server, Qdrant, DB, frontend) — a simple diagram tool or even a hand-drawn one photographed is fine; clarity matters more than polish.
4. Write a **3–5 minute demo script** covering, in order: (a) a normal read question, (b) the ambiguous "best employee" question, (c) a destructive delete with confirmation + rollback, (d) a 30-second look at the eval table and audit log.

---

## Known Open Decisions / Risks (read before you start)

Being upfront about these now avoids surprises mid-build, and gives you honest answers if asked in an interview.

| Item | Status | What to do about it |
|---|---|---|
| **No time buffer in the 20 days** | Real risk for a solo build | Treat Phase 3 (Safety Layer, Days 11–15) as the phase most likely to overrun — it's the most complex. If you're behind by Day 15, cut scope from Phase 4's eval set size (e.g. 20 questions instead of 40) before cutting anything from the safety layer itself. |
| **Rollback strategy** | Resolved — see Step 3.3 (commit + logged reverse statement, 5-minute undo window) | No action needed; just build to this spec. |
| **LangChain vs. raw SDKs** | Resolved — raw SDKs, no LangChain (see tech stack table) | No action needed. |
| **Concurrent users / multi-tenant load** | Not addressed by this plan, and out of scope for a 20-day solo interview project | Add one honest line to the README: "Designed for per-user isolation via Qdrant namespaces and scoped MCP credentials; not load-tested under concurrent write contention." Don't claim more than you built. |
| **Eval harness timing** | Squeezed at Days 16–18, right after the highest-risk phase | If Phase 3 overruns, start the eval question set (just the plain-text questions + expected labels, no code) on Day 10 in spare moments, so Day 16 is scoring, not writing questions from scratch. |
| **Ambiguity detection false positives/negatives** | Untested until the eval harness runs | Explicitly include a few *non*-ambiguous questions in your eval set (e.g. "list all customers") to confirm the Clarifier doesn't over-trigger and interrupt when it shouldn't — the plan only tests for missed ambiguity, not false alarms. |

## Order-of-Operations Summary (if you only remember one thing)

Build the **read path completely first** (Phases 1–2) before touching writes. It forces you to get connection management, schema introspection, RAG, and the agent graph working end-to-end on the lowest-risk operation. Writes, safety, and confirmation (Phase 3) are then a layer added on top of a graph that already works — not a parallel track you're debugging at the same time as the basics.

---

## Deployment — Can This Go on Any Cloud Platform?

**Yes.** Nothing in this stack ties you to one provider — every component is either a standard container or a managed service with equivalents everywhere. That's a deliberate side-effect of the choices already made (Docker Compose locally, MCP server as its own process, Qdrant as a separate service), not something bolted on later.

### What "cloud-ready" means here, piece by piece

| Component | How it deploys | Notes |
|---|---|---|
| **Next.js frontend** | Vercel (easiest, built for Next.js), or any container host | Vercel's free tier is enough for a demo/interview project |
| **Agent service (LangGraph + Python)** | Any container host — Render, Railway, Fly.io, AWS ECS/Fargate, Google Cloud Run, Azure Container Apps | Package as a Dockerfile; this is the same container whether it runs on your laptop or in the cloud |
| **MCP DB server** | Same container host as the agent service, or a separate small container | Keep it as its own process/container even in production — that process boundary is part of the "badge system" security model, not just a dev convenience |
| **Qdrant** | Qdrant Cloud (managed, free tier available), or self-hosted container on any of the above hosts | Managed is less to maintain for a solo project |
| **Postgres/MySQL (your sample demo DB)** | Any managed Postgres — Supabase, Neon, Railway, RDS, Cloud SQL | This is separate from the databases *users* connect — it's just where your own app data (accounts, connections, audit logs) lives |
| **Secrets (DB credentials, API keys)** | The host's built-in secrets manager (Vercel env vars, AWS Secrets Manager, etc.) | Never commit secrets to the repo — see `.gitignore` note below |

### A simple, cheap path for a demo deployment
1. Frontend → **Vercel** (free tier)
2. Agent service + MCP server → **Render** or **Railway** (both have simple Docker deploys and free/cheap tiers)
3. Qdrant → **Qdrant Cloud** free tier
4. App's own Postgres → **Supabase** or **Neon** free tier

This costs close to $0 for a portfolio/interview demo and doesn't lock you into anything — every piece can be swapped for AWS/GCP/Azure equivalents later without changing your code, only your deploy config.

### One thing to build in from Day 1, not bolt on later
Keep all environment-specific values (DB URLs, API keys, Qdrant endpoint) in environment variables from the start, never hardcoded — this is what actually makes "deploy anywhere" true rather than aspirational. Add this as part of Step 1.1, not as cleanup at Day 19.

---

## GitHub — Repo & Workflow Setup

Add this at the very start (Day 1, before Step 1.1), not at the end — a project built without version control from day one loses most of the benefit.

### Step 0.1 — Initialize the repo
1. `git init` in the project root, matching the `/apps`, `/infra`, `/evals` structure from the top of this plan.
2. Create the repo on GitHub, push the initial skeleton (empty folders with `.gitkeep`, or the docker-compose file).
3. **`.gitignore` from the very first commit** — must exclude: `.env`, `.env.local`, any credentials file, `node_modules`, `__pycache__`, `*.db`. This matters more here than in a typical project, since a leaked `.env` in this app could mean leaked *user* database credentials, not just your own API key.

### Step 0.2 — Branch strategy (solo-friendly, not overkill)
- `main` — always deployable/demo-ready.
- Feature branches per phase or step (e.g. `feat/mcp-db-server`, `feat/clarifier-agent`), merged into `main` via PR even solo — this gives you a clean commit history to point to in an interview, and PR descriptions double as a build log.
- Tag a release/commit at the end of each phase (`git tag phase-1-complete`) — an easy way to show progression if asked "walk me through how you built this."

### Step 0.3 — What goes in the repo vs. what doesn't
| In the repo | Not in the repo |
|---|---|
| All application code, Dockerfiles, docker-compose.yml | `.env` files, real credentials |
| `/evals` test question sets and eval scripts | Actual eval *results* with any real user data — keep results to your seeded sample DB only |
| README, architecture diagram (image or Mermaid) | Any exported audit log containing real data |
| A `.env.example` file listing required variable *names* only | The values for those variables |

### Step 0.4 — CI (optional but a strong interview signal)
A minimal **GitHub Actions** workflow is worth the ~1 hour it takes, given the eval harness already exists from Phase 4:
- On every push to `main`: run linting + the eval harness against the seeded sample DB, fail the build if the eval scores drop below the plan's own targets (≥75% first-try, 100% ambiguity/destructive-interception).
- This turns your Phase 4 eval table into a living check instead of a one-time screenshot — genuinely rare for a student project and worth calling out explicitly in the README.

### Step 0.5 — README checklist (ties back to Phase 5, Step 5.2)
Make sure the README explicitly includes: problem statement, architecture diagram, tech stack table, **local run instructions** (`docker-compose up`), **deployment instructions** (which host for which component, per the table above), eval results, and the "Known Open Decisions / Risks" section from this plan — don't hide known limitations, stating them clearly reads as maturity, not weakness.

