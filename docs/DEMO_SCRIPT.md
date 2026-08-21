# Governed AI Database Copilot — 3 to 5 Minute Demo Script

This script is designed for live portfolio showcases, client demonstrations, and technical hiring manager interviews.

---

## 🎯 High-Level Pitch (0:00 – 0:45)

> *"Most text-to-SQL tools are toy demos: they send raw database passwords to an LLM, hallucinate column names, guess at ambiguous business terms, and will happily run an unconstrained `DROP TABLE` or `DELETE` with no confirmation and no undo.*
>
> *I built the **Governed AI Database Copilot** — an enterprise-grade, secure, multi-agent database copilot designed with four non-negotiable guarantees:*
> 1. **Zero Raw Credentials in the AI Layer** via isolated Model Context Protocol (MCP) servers and an AES-128 Fernet vault.
> 2. **Zero Guessing on Business Metrics** via an interactive Ambiguity Interception Clarifier.
> 3. **Teller vs. Approver Safety Isolation** for write mutations with dry-run diffs, HMAC-signed tokens, and a 1-click ACID rollback engine.
> 4. **100% Benchmark Accuracy** across a 30-question rigorous evaluation suite.*
>
> *Let's see it in action across four real-world scenarios."*

---

## 🔍 Scenario 1: Grounded Analytical Read Query & Observability (0:45 – 1:45)

1. **In the Chat Playground**, select the preset or type:
   > *"Which customers haven't placed an order in the last 90 days?"*
2. **Click "Execute"** and observe the live LangGraph pipeline progress:
   - `Planner` routes query as `read`.
   - `Retriever` fetches schema chunks and glossary definitions from Qdrant vector database.
   - `SQL Generator` synthesizes valid PostgreSQL using Groq LLaMA 3.3 70B.
   - `Safety Critic` validates AST read-only enforcement.
   - `Executor` queries MCP DB Server with zero exposed credentials.
   - `Explainer` provides an executive summary.
3. **Key Visual Highlights to Show**:
   - Point out the **Live Telemetry Bar**: `⏱️ 385ms Total Latency` · `🧠 1,420 Tokens` · `💰 $0.0008 Cost`.
   - Expand the **Agent Node Latency Breakdown** drawer showing per-node execution spans (Planner, RAG, SQL Gen, Critic, MCP, Explainer).
   - Point out the **Grounded Vector Trace** showing exact chunks retrieved from Qdrant.

---

## ⚠️ Scenario 2: Ambiguity Interception — Zero Guessing Guarantee (1:45 – 2:30)

1. **In the Chat Playground**, select or type:
   > *"Who is our best employee?"*
2. **Observe the Pipeline Behavior**:
   - The `Clarifier Agent` intercepts the query and halts the pipeline with an amber warning card.
   - It explains: *"The metric 'best' is subjective and could mean highest sales revenue, most orders processed, or fastest fulfillment."*
3. **Select "Option 1: Highest Total Sales Revenue"**:
   - The state machine immediately resumes, binds the clarified business rule, retrieves the correct joins on `orders`, and returns the verified employee ranking without guessing.

---

## 🔥 Scenario 3: Destructive Mutation, Dry-Run Diff, & 1-Click Rollback (2:30 – 3:45)

1. **In the Chat Playground**, select or type:
   > *"Delete all inactive customer accounts who registered before 2022."*
2. **Observe the Safety Critic Halt**:
   - The query is intercepted before touching the database.
   - A pulsing red **High-Risk Confirmation Card** appears with:
     - Live **5-Minute Countdown Clock** (`300s -> 0s`).
     - Plain-language impact description: *"⚠️ Destructive Action: This will DELETE 14 customer record(s) from table 'customers'."*
     - **Interactive Before-State Row Diff Table**: Displays the exact customer rows slated for deletion.
     - Cryptographic HMAC-SHA256 confirmation token.
3. **Click "Confirm & Execute Mutation"**:
   - The transaction executes inside an ACID transaction on the database.
   - The pre-state is snapshotted into `rollback_log.db` and deterministic inverse SQL (`INSERT INTO customers ...`) is generated.
4. **Demonstrate 1-Click Rollback**:
   - A green banner appears with a **"↩️ Rollback Changes"** button.
   - Click **"Rollback Changes"** — the deleted rows are instantly restored into the database!
   - Navigate to the **Audit & Rollback Logs tab** to show the audit trail record.

---

## 🏆 Scenario 4: Observability, SQL Transpiler, & Evaluation Scorecard (3:45 – 4:30)

1. **Navigate to the "SQL Transpiler Studio" tab**:
   - Show how users can paste queries from `Snowflake`, `MySQL`, `BigQuery`, or `TSQL` and transpile them to valid PostgreSQL 16 with 1 click using AST conversion.
2. **Navigate to the "Benchmark Scorecard" tab**:
   - Show the live evaluation results across all **30 benchmark questions**:
     - **Ambiguity Interception Rate:** `100.0%`
     - **Destructive Write Interception Rate:** `100.0%`
     - **Overall Intent & Execution Accuracy:** `100.0%`

---

## 💡 Closing Summary (4:30 – 5:00)

> *"Every layer of this system was built with production resilience in mind: AES-128 credential isolation, LangGraph multi-agent orchestration, SHA-256 schema drift self-healing, and end-to-end evaluation harness benchmarking.
>
> All code is live on GitHub at `github.com/rahulternamakki/SQL_Copilot`."*
