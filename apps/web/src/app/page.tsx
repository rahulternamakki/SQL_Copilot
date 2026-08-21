"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  Database,
  Terminal,
  Sparkles,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  Lock,
  Layers,
  Search,
  BookOpen,
  History,
  Send,
  HelpCircle,
  Clock,
  ArrowRight,
} from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"chat" | "schema" | "glossary" | "audit">("chat");
  const [inputQuery, setInputQuery] = useState("Which customers haven't placed an order in the last 90 days?");
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  return (
    <div className="flex h-screen flex-col bg-[#070b14] text-slate-100 overflow-hidden">
      {/* Top Navigation Bar */}
      <header className="h-16 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base font-semibold tracking-tight text-white flex items-center gap-2">
              Governed AI Database Copilot
              <span className="text-xs font-mono font-normal bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20">
                Phase 0 Setup
              </span>
            </h1>
            <p className="text-xs text-slate-400">RAG-Grounded • MCP Tool Isolation • Multi-Agent Safety</p>
          </div>
        </div>

        {/* Status Indicators & Connection Selector */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/60 text-xs">
            <Database className="h-4 w-4 text-emerald-400" />
            <span className="text-slate-300 font-medium">ecommerce_demo</span>
            <span className="bg-emerald-500/20 text-emerald-300 text-[10px] font-mono px-1.5 py-0.5 rounded">
              READ-ONLY
            </span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/60 text-xs">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-300">Agent Service: Online (Port 8000)</span>
          </div>
        </div>
      </header>

      {/* Main Workspace Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <aside className="w-72 border-r border-slate-800/80 bg-slate-900/40 flex flex-col shrink-0">
          <div className="p-3 border-b border-slate-800/60">
            <div className="grid grid-cols-4 gap-1 p-1 bg-slate-950/60 rounded-lg border border-slate-800/60 text-xs">
              <button
                onClick={() => setActiveTab("chat")}
                className={`py-1.5 rounded flex items-center justify-center gap-1 transition ${
                  activeTab === "chat" ? "bg-emerald-500/20 text-emerald-300 font-medium" : "text-slate-400 hover:text-slate-200"
                }`}
                title="Chat"
              >
                <Sparkles className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => setActiveTab("schema")}
                className={`py-1.5 rounded flex items-center justify-center gap-1 transition ${
                  activeTab === "schema" ? "bg-emerald-500/20 text-emerald-300 font-medium" : "text-slate-400 hover:text-slate-200"
                }`}
                title="Schema Explorer"
              >
                <Layers className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => setActiveTab("glossary")}
                className={`py-1.5 rounded flex items-center justify-center gap-1 transition ${
                  activeTab === "glossary" ? "bg-emerald-500/20 text-emerald-300 font-medium" : "text-slate-400 hover:text-slate-200"
                }`}
                title="Business Glossary"
              >
                <BookOpen className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => setActiveTab("audit")}
                className={`py-1.5 rounded flex items-center justify-center gap-1 transition ${
                  activeTab === "audit" ? "bg-emerald-500/20 text-emerald-300 font-medium" : "text-slate-400 hover:text-slate-200"
                }`}
                title="Audit Trail"
              >
                <History className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          {/* Sidebar Content Panels */}
          <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
            {activeTab === "chat" && (
              <div className="space-y-4">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Example Benchmarks</div>
                <div className="space-y-2">
                  <button
                    onClick={() => setInputQuery("Which customers haven't placed an order in the last 90 days?")}
                    className="w-full text-left text-xs p-2.5 rounded-lg bg-slate-800/40 hover:bg-slate-800/80 border border-slate-700/40 text-slate-300 transition"
                  >
                    🔍 <span className="font-medium">Read Query:</span> Inactive customers in 90 days
                  </button>
                  <button
                    onClick={() => setInputQuery("Who is our best employee?")}
                    className="w-full text-left text-xs p-2.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-200 transition"
                  >
                    ⚠️ <span className="font-medium">Ambiguity Test:</span> "Best employee" disambiguation
                  </button>
                  <button
                    onClick={() => {
                      setInputQuery("Delete all inactive customer accounts who signed up before 2022.");
                      setShowConfirmModal(true);
                    }}
                    className="w-full text-left text-xs p-2.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-200 transition"
                  >
                    🛡️ <span className="font-medium">Destructive Write:</span> Mass DELETE with preview & rollback
                  </button>
                </div>
              </div>
            )}

            {activeTab === "schema" && (
              <div className="space-y-3">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Seeded Tables (Postgres)</div>
                {["customers", "orders", "order_items", "products", "refunds", "audit_logs"].map((tbl) => (
                  <div key={tbl} className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-700/40 text-xs">
                    <div className="font-mono text-emerald-400 flex items-center gap-1.5">
                      <Database className="h-3.5 w-3.5" />
                      {tbl}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === "glossary" && (
              <div className="space-y-3">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Business Glossary</div>
                {[
                  { term: "churned customer", desc: "No order in 180+ days or status='churned'" },
                  { term: "gross sales", desc: "SUM(total_amount) of completed orders" },
                  { term: "best employee", desc: "AMBIGUOUS - triggers clarifier interrupt" },
                ].map((g, idx) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-700/40 text-xs space-y-1">
                    <div className="font-semibold text-emerald-300">{g.term}</div>
                    <div className="text-slate-400 text-[11px]">{g.desc}</div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === "audit" && (
              <div className="space-y-3">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Recent Audit Trail</div>
                <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-700/40 text-[11px] space-y-1">
                  <div className="flex justify-between text-slate-400">
                    <span>SELECT (none)</span>
                    <span>Just now</span>
                  </div>
                  <div className="font-mono text-emerald-400 truncate">SELECT * FROM customers WHERE ...</div>
                </div>
              </div>
            )}
          </div>
        </aside>

        {/* Center Main Stage */}
        <main className="flex-1 flex flex-col bg-slate-950/40 overflow-hidden">
          {/* Agent Pipeline Visualizer Bar */}
          <div className="h-12 border-b border-slate-800/80 bg-slate-900/30 px-6 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">LangGraph Pipeline:</span>
              <div className="flex items-center gap-1.5 text-[11px]">
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">Planner</span>
                <ArrowRight className="h-3 w-3 text-slate-600" />
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">Clarifier</span>
                <ArrowRight className="h-3 w-3 text-slate-600" />
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">Retriever (RAG)</span>
                <ArrowRight className="h-3 w-3 text-slate-600" />
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">SQL Generator</span>
                <ArrowRight className="h-3 w-3 text-slate-600" />
                <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono">Safety Critic</span>
                <ArrowRight className="h-3 w-3 text-slate-600" />
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">Executor (MCP)</span>
              </div>
            </div>
          </div>

          {/* Conversation & Results Canvas */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
            {/* User message mockup */}
            <div className="flex gap-3 max-w-2xl">
              <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-semibold text-slate-300 shrink-0">
                You
              </div>
              <div className="p-3.5 rounded-xl bg-slate-800/80 border border-slate-700/60 text-sm text-slate-200">
                {inputQuery}
              </div>
            </div>

            {/* Agent Thought & Execution Card */}
            <div className="flex gap-3 max-w-3xl">
              <div className="h-8 w-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-xs font-semibold text-emerald-400 shrink-0">
                AI
              </div>
              <div className="flex-1 space-y-3">
                {/* Agent Thought Trace */}
                <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2 text-xs">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5" /> Reasoning & Grounding Trace
                    </span>
                    <span className="font-mono text-[10px] bg-slate-800 px-2 py-0.5 rounded">Groq LLaMA 3.3 70B</span>
                  </div>
                  <p className="text-slate-300">
                    Retrieved schema for <code className="text-emerald-300 font-mono">customers</code> and <code className="text-emerald-300 font-mono">orders</code>. Identified business rule from glossary for inactive customer evaluation.
                  </p>
                </div>

                {/* Generated SQL Code Block */}
                <div className="rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                  <div className="bg-slate-900/80 px-4 py-2 flex items-center justify-between border-b border-slate-800 text-xs">
                    <span className="font-mono text-slate-400 flex items-center gap-1.5">
                      <Terminal className="h-3.5 w-3.5 text-emerald-400" /> Synthesized SQL Query
                    </span>
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                      AST Verified Read-Only
                    </span>
                  </div>
                  <pre className="p-4 text-xs font-mono text-emerald-300 overflow-x-auto">
{`SELECT c.id, c.first_name, c.last_name, c.email, MAX(o.order_date) AS last_order_date
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.first_name, c.last_name, c.email
HAVING MAX(o.order_date) < NOW() - INTERVAL '90 days' OR MAX(o.order_date) IS NULL
ORDER BY last_order_date ASC NULLS FIRST;`}
                  </pre>
                </div>

                {/* Natural Language Explanation */}
                <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-sm text-slate-300 space-y-2">
                  <p>
                    Found <strong>4 customers</strong> who have not placed an order in the past 90 days (or have never placed an order).
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Query Input Bar */}
          <div className="p-4 border-t border-slate-800/80 bg-slate-900/50">
            <div className="flex gap-2 max-w-4xl mx-auto">
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Ask any database question (e.g. 'Show monthly revenue by category')..."
                className="flex-1 bg-slate-950/80 border border-slate-700/80 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/60 transition"
              />
              <button className="px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm flex items-center gap-2 transition shadow-lg shadow-emerald-900/30">
                <Send className="h-4 w-4" />
                <span>Run</span>
              </button>
            </div>
          </div>
        </main>
      </div>

      {/* Destructive Write Confirmation Modal Preview */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-rose-500/40 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center gap-3 text-rose-400">
              <div className="p-2 rounded-xl bg-rose-500/10 border border-rose-500/20">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white">High-Risk Destructive Action Preview</h3>
                <p className="text-xs text-rose-300">Safety Critic intercepted a mass modification</p>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <div className="flex justify-between text-slate-400">
                <span>Estimated Rows Affected:</span>
                <span className="font-mono font-bold text-rose-400">3 Customers</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Target Table:</span>
                <span className="font-mono text-slate-200">customers</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Undo Window:</span>
                <span className="text-emerald-400 font-medium">5 Minutes (Auto-Reverse Logged)</span>
              </div>
            </div>

            <div className="text-xs text-slate-300">
              Plain-language preview: <span className="font-medium text-slate-100">This query will permanently delete 3 customer records who signed up before 2022 and are marked inactive.</span>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setShowConfirmModal(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
              >
                Cancel
              </button>
              <button
                onClick={() => setShowConfirmModal(false)}
                className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium flex items-center gap-1.5 transition"
              >
                <Lock className="h-3.5 w-3.5" />
                <span>Confirm & Issue Execution Token</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
