# Web Frontend (`/apps/web`)

The **Governed AI Database Copilot Web Frontend** is built using **Next.js 15 (App Router)**, **React 19**, **TypeScript**, and **Tailwind CSS**.

## Features
- **Interactive Multi-Agent Thought Visualizer**: Live step-by-step trace of agent reasoning (Planner -> Clarifier -> Retriever -> SQL Generator -> Safety Critic -> Executor -> Explainer).
- **Ambiguity Interception UI**: Prompts the user when queries are inherently ambiguous (e.g. "best employee") before generating or executing SQL.
- **Destructive Write Confirmation Modal**: Displays estimated row counts, before-state samples, raw SQL, and 5-minute undo windows before issuing execution tokens.
- **Schema & Business Glossary Explorer**: Live explorer for introspected tables and business definitions.
- **Full Audit Trail Dashboard**: Filterable history of queries, execution times, risk levels, and one-click rollback triggers.

## Running Locally

```bash
cd apps/web
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.
