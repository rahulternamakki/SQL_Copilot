"use client";

import React, { useState, useEffect } from "react";
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
  Plus,
  ChevronDown,
  Server,
  Zap,
} from "lucide-react";
import { api, DatabaseConnection } from "@/lib/api";
import ConnectionModal from "@/components/ConnectionModal";
import SchemaViewer from "@/components/SchemaViewer";
import GlossaryEditor from "@/components/GlossaryEditor";
import ChatPlayground from "@/components/ChatPlayground";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"chat" | "schema" | "glossary" | "audit">("chat");
  const [connections, setConnections] = useState<DatabaseConnection[]>([]);
  const [activeConnectionId, setActiveConnectionId] = useState<string>("conn_ecommerce_demo");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [backendHealth, setBackendHealth] = useState<any>(null);

  const loadConnections = async () => {
    try {
      const list = await api.listConnections();
      setConnections(list);
      if (list.length > 0 && !list.some((c) => c.connection_id === activeConnectionId)) {
        setActiveConnectionId(list[0].connection_id);
      }
    } catch (err) {
      console.warn("Could not load connections:", err);
    }
  };

  const loadHealth = async () => {
    try {
      const data = await api.checkHealth();
      setBackendHealth(data);
    } catch (err) {
      setBackendHealth(null);
    }
  };

  useEffect(() => {
    loadConnections();
    loadHealth();
  }, []);

  const activeConn = connections.find((c) => c.connection_id === activeConnectionId) || {
    connection_id: "conn_ecommerce_demo",
    display_name: "E-Commerce Demo DB",
    db_type: "postgresql",
    host: "localhost",
    port: 5432,
    database: "ecommerce_demo",
    username: "postgres",
    ssl_mode: "disable",
    read_only: true,
  };

  return (
    <div className="flex h-screen flex-col bg-[#060911] text-slate-100 overflow-hidden">
      {/* Top Navigation Bar */}
      <header className="h-16 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold shadow-sm shadow-emerald-950/40">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base font-semibold tracking-tight text-white flex items-center gap-2">
              Governed AI Database Copilot
              <span className="text-xs font-mono font-normal bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20">
                Phase 2 Core Agent Flow
              </span>
            </h1>
            <p className="text-xs text-slate-400">RAG-Grounded • Multi-Agent Orchestration • MCP Isolation</p>
          </div>
        </div>

        {/* Status Indicators & Connection Selector */}
        <div className="flex items-center gap-3">
          {/* Connection Dropdown */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-xs shadow-sm">
            <Database className="h-4 w-4 text-emerald-400 shrink-0" />
            <select
              value={activeConnectionId}
              onChange={(e) => setActiveConnectionId(e.target.value)}
              className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer"
            >
              {connections.length > 0 ? (
                connections.map((c) => (
                  <option key={c.connection_id} value={c.connection_id} className="bg-slate-900 text-slate-200">
                    {c.display_name} ({c.database})
                  </option>
                ))
              ) : (
                <option value="conn_ecommerce_demo" className="bg-slate-900 text-slate-200">
                  E-Commerce Demo DB (localhost)
                </option>
              )}
            </select>
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                activeConn.read_only
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 font-semibold"
                  : "bg-amber-500/10 text-amber-400 border-amber-500/30 font-semibold"
              }`}
            >
              {activeConn.read_only ? "READ-ONLY" : "WRITE-ENABLED"}
            </span>
          </div>

          {/* Add Connection Button */}
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 border border-slate-700 transition"
          >
            <Plus className="h-3.5 w-3.5 text-emerald-400" />
            <span>Connect DB</span>
          </button>

          {/* Backend Status Indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-300">LangGraph Agent: Online (8000)</span>
          </div>
        </div>
      </header>

      {/* Main Workspace Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Navigation Bar */}
        <aside className="w-64 border-r border-slate-800/80 bg-slate-900/40 flex flex-col shrink-0">
          <div className="p-3 border-b border-slate-800/60">
            <nav className="space-y-1">
              <button
                onClick={() => setActiveTab("chat")}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition ${
                  activeTab === "chat"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`}
              >
                <Sparkles className="h-4 w-4 text-emerald-400" />
                <span>Chat & Multi-Agent Flow</span>
              </button>

              <button
                onClick={() => setActiveTab("schema")}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition ${
                  activeTab === "schema"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`}
              >
                <Layers className="h-4 w-4" />
                <span>Schema Explorer</span>
              </button>

              <button
                onClick={() => setActiveTab("glossary")}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition ${
                  activeTab === "glossary"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`}
              >
                <BookOpen className="h-4 w-4" />
                <span>Business Glossary (RAG)</span>
              </button>

              <button
                onClick={() => setActiveTab("audit")}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition ${
                  activeTab === "audit"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`}
              >
                <History className="h-4 w-4" />
                <span>Audit Trail</span>
              </button>
            </nav>
          </div>

          {/* Quick Benchmark Guide */}
          <div className="flex-1 overflow-y-auto p-3.5 space-y-3 custom-scrollbar">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-1 flex items-center gap-1">
              <Zap className="h-3 w-3 text-amber-400" />
              <span>Phase 2 Benchmarks</span>
            </div>
            <div className="space-y-2 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1">
                <span className="font-semibold text-emerald-300 block">1. Read-Only Retrieval</span>
                <p className="text-[11px] text-slate-400">
                  RAG grounds query context using Qdrant vector search.
                </p>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1">
                <span className="font-semibold text-amber-300 block">2. Ambiguity Interception</span>
                <p className="text-[11px] text-slate-400">
                  Clarifier agent halts execution on ill-defined terms like &quot;best employee&quot;.
                </p>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1">
                <span className="font-semibold text-cyan-300 block">3. Self-Correction Retry</span>
                <p className="text-[11px] text-slate-400">
                  Single-retry feedback loop on database errors.
                </p>
              </div>
            </div>
          </div>
        </aside>

        {/* Center Main Stage */}
        <main className="flex-1 flex flex-col bg-slate-950/40 overflow-hidden">
          {activeTab === "chat" && <ChatPlayground connectionId={activeConnectionId} />}

          {activeTab === "schema" && <SchemaViewer connectionId={activeConnectionId} />}

          {activeTab === "glossary" && <GlossaryEditor connectionId={activeConnectionId} />}

          {activeTab === "audit" && (
            <div className="p-6 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <History className="h-4 w-4 text-emerald-400" />
                Audit Trail & Rollback History
              </h3>
              <p className="text-xs text-slate-400">
                Every prompt, generated SQL, Safety Critic risk score, and confirmation decision is securely logged.
              </p>
              <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-900/50">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 border-b border-slate-800 text-slate-400">
                    <tr>
                      <th className="p-3">Timestamp</th>
                      <th className="p-3">Operation / Risk</th>
                      <th className="p-3">User Prompt</th>
                      <th className="p-3">SQL Executed</th>
                      <th className="p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300 font-mono">
                    <tr>
                      <td className="p-3 text-slate-500 text-[11px]">Just now</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px]">
                          SELECT (none)
                        </span>
                      </td>
                      <td className="p-3 font-sans">Which customers haven&apos;t placed an order in 90 days?</td>
                      <td className="p-3 text-emerald-400 text-[11px] truncate max-w-xs">
                        SELECT c.id, c.email FROM customers c ...
                      </td>
                      <td className="p-3 text-emerald-400 font-sans">Success (4 rows)</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Connection Modal */}
      <ConnectionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={(id) => {
          loadConnections();
          setActiveConnectionId(id);
        }}
      />
    </div>
  );
}
