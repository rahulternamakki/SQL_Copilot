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
  Flame,
  Undo2,
  ArrowRightLeft,
  Award,
  Activity,
  Play,
} from "lucide-react";
import { api, DatabaseConnection, AuditLogEntry, DriftResult } from "@/lib/api";
import ConnectionModal from "@/components/ConnectionModal";
import SchemaViewer from "@/components/SchemaViewer";
import GlossaryEditor from "@/components/GlossaryEditor";
import ChatPlayground from "@/components/ChatPlayground";
import TranspilerStudio from "@/components/TranspilerStudio";
import BenchmarkScorecard from "@/components/BenchmarkScorecard";
import DemoTourModal from "@/components/DemoTourModal";
import ArchitectureModal from "@/components/ArchitectureModal";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"chat" | "schema" | "glossary" | "audit" | "transpiler" | "benchmark">("chat");
  const [connections, setConnections] = useState<DatabaseConnection[]>([]);
  const [activeConnectionId, setActiveConnectionId] = useState<string>("conn_ecommerce_demo");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);
  const [isArchModalOpen, setIsArchModalOpen] = useState(false);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [driftStatus, setDriftStatus] = useState<DriftResult | null>(null);
  const [selectedPrompt, setSelectedPrompt] = useState<string | undefined>(undefined);

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

  const checkDrift = async (connId: string) => {
    try {
      const res = await api.checkSchemaDrift(connId);
      if (res.has_drift) {
        setDriftStatus(res);
      }
    } catch (err) {
      console.warn("Schema drift check warning:", err);
    }
  };

  const loadAuditLogs = async () => {
    setLoadingLogs(true);
    try {
      const logs = await api.getAuditLogs(activeConnectionId);
      setAuditLogs(logs);
    } catch (err) {
      console.warn("Could not load audit logs:", err);
    } finally {
      setLoadingLogs(false);
    }
  };

  useEffect(() => {
    loadConnections();
  }, []);

  useEffect(() => {
    if (activeConnectionId) {
      checkDrift(activeConnectionId);
    }
  }, [activeConnectionId]);

  useEffect(() => {
    if (activeTab === "audit") {
      loadAuditLogs();
    }
  }, [activeTab, activeConnectionId]);

  const handleRollbackAudit = async (rollbackId: string) => {
    try {
      await api.rollbackOperation(activeConnectionId, rollbackId);
      loadAuditLogs();
    } catch (err: any) {
      alert(`Rollback failed: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleLaunchDemoScenario = (prompt: string, targetTab: "chat" | "transpiler" | "benchmark" = "chat") => {
    setSelectedPrompt(prompt);
    setActiveTab(targetTab);
  };

  const activeConn = connections.find((c) => c.connection_id === activeConnectionId) || {
    connection_id: "conn_ecommerce_demo",
    display_name: "E-Commerce Demo DB",
    db_type: "postgresql",
    host: "localhost",
    port: 5432,
    database: "ecommerce_demo",
    username: "postgres",
    ssl_mode: "disable",
    read_only: false,
  };

  return (
    <div className="flex h-screen flex-col bg-[#060911] text-slate-100 overflow-hidden font-sans">
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
                Phase 5 Production Ready
              </span>
            </h1>
            <p className="text-xs text-slate-400">Telemetry • Schema Drift Healing • Cross-Dialect SQL • 100% Verified Evals</p>
          </div>
        </div>

        {/* Status Indicators & Action Buttons */}
        <div className="flex items-center gap-3">
          {/* Guided Demo Tour Button */}
          <button
            onClick={() => setIsDemoModalOpen(true)}
            className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-emerald-950/60 transition"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Guided Demo Tour</span>
          </button>

          {/* Architecture Visualizer Button */}
          <button
            onClick={() => setIsArchModalOpen(true)}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 border border-slate-700 transition"
          >
            <Layers className="h-3.5 w-3.5 text-cyan-400" />
            <span>Architecture</span>
          </button>

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
        </div>
      </header>

      {/* Schema Drift Self-Healing Alert Banner (Step 4.2) */}
      {driftStatus && driftStatus.has_drift && (
        <div className="px-6 py-2.5 bg-amber-500/15 border-b border-amber-500/30 text-xs text-amber-200 flex items-center justify-between animate-in fade-in">
          <div className="flex items-center gap-2 font-medium">
            <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
            <span>{driftStatus.message}</span>
          </div>
          <button
            onClick={() => setDriftStatus(null)}
            className="text-[10px] font-mono bg-amber-500/20 px-2 py-0.5 rounded text-amber-300 hover:bg-amber-500/30 transition"
          >
            Dismiss
          </button>
        </div>
      )}

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
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`}
              >
                <Sparkles className="h-4 w-4 text-emerald-400" />
                <span>Chat & Multi-Agent</span>
              </button>

              <button
                onClick={() => setActiveTab("transpiler")}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition ${
                  activeTab === "transpiler"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`}
              >
                <ArrowRightLeft className="h-4 w-4 text-cyan-400" />
                <span>SQL Transpiler Studio</span>
              </button>

              <button
                onClick={() => setActiveTab("benchmark")}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition ${
                  activeTab === "benchmark"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`}
              >
                <Award className="h-4 w-4 text-amber-400" />
                <span>Benchmark Scorecard (30)</span>
              </button>

              <button
                onClick={() => setActiveTab("schema")}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition ${
                  activeTab === "schema"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold"
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
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold"
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
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`}
              >
                <History className="h-4 w-4" />
                <span>Audit & Rollback Logs</span>
              </button>
            </nav>
          </div>

          {/* Hardening Guarantees Sidebar */}
          <div className="flex-1 overflow-y-auto p-3.5 space-y-3 custom-scrollbar">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-1 flex items-center gap-1">
              <ShieldCheck className="h-3 w-3 text-emerald-400" />
              <span>Production Guarantees</span>
            </div>
            <div className="space-y-2 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1">
                <span className="font-semibold text-cyan-400 block">1. Full Observability</span>
                <p className="text-[11px] text-slate-400">
                  Node spans, token counts, and cost telemetry tracked in real time.
                </p>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1">
                <span className="font-semibold text-emerald-400 block">2. Self-Healing Schema</span>
                <p className="text-[11px] text-slate-400">
                  SHA-256 drift detection auto-updates vector embeddings when tables change.
                </p>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1">
                <span className="font-semibold text-rose-400 block">3. 100% Write & Ambiguity Intercept</span>
                <p className="text-[11px] text-slate-400">
                  Zero unconfirmed mutations · Zero hallucinated criteria.
                </p>
              </div>
            </div>
          </div>
        </aside>

        {/* Center Main Stage */}
        <main className="flex-1 flex flex-col bg-slate-950/40 overflow-hidden">
          {activeTab === "chat" && (
            <ChatPlayground connectionId={activeConnectionId} initialPrompt={selectedPrompt} />
          )}

          {activeTab === "transpiler" && <TranspilerStudio />}

          {activeTab === "benchmark" && (
            <BenchmarkScorecard
              onSelectPrompt={(p) => {
                setSelectedPrompt(p);
                setActiveTab("chat");
              }}
            />
          )}

          {activeTab === "schema" && <SchemaViewer connectionId={activeConnectionId} />}

          {activeTab === "glossary" && <GlossaryEditor connectionId={activeConnectionId} />}

          {activeTab === "audit" && (
            <div className="flex-1 flex flex-col p-6 space-y-4 overflow-hidden">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <History className="h-4 w-4 text-emerald-400" />
                    Transaction Audit Trail & 1-Click Rollback Console
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Step 3.3: Every mutating operation captures a pre-state snapshot and computed inverse SQL in local rollback storage.
                  </p>
                </div>
                <button
                  onClick={loadAuditLogs}
                  className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 border border-slate-700 transition"
                >
                  <RotateCcw className={`h-3.5 w-3.5 ${loadingLogs ? "animate-spin" : ""}`} />
                  <span>Refresh Logs</span>
                </button>
              </div>

              <div className="flex-1 rounded-2xl border border-slate-800 overflow-hidden bg-[#0c1220] shadow-xl flex flex-col">
                <div className="overflow-x-auto flex-1 custom-scrollbar">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-950 border-b border-slate-800 text-slate-400 font-medium font-mono">
                        <th className="p-3.5">Timestamp</th>
                        <th className="p-3.5">Rollback ID</th>
                        <th className="p-3.5">Operation</th>
                        <th className="p-3.5">Table</th>
                        <th className="p-3.5">Rows Affected</th>
                        <th className="p-3.5">SQL Statement</th>
                        <th className="p-3.5">Status</th>
                        <th className="p-3.5 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300 font-mono">
                      {auditLogs.length === 0 ? (
                        <tr>
                          <td colSpan={8} className="p-8 text-center text-slate-500 font-sans">
                            No write mutations recorded in this connection yet.
                          </td>
                        </tr>
                      ) : (
                        auditLogs.map((log) => (
                          <tr key={log.rollback_id} className="hover:bg-slate-900/40 transition">
                            <td className="p-3.5 text-slate-500 text-[11px] whitespace-nowrap">
                              {log.created_at || "Recent"}
                            </td>
                            <td className="p-3.5 text-emerald-400 text-[11px] font-bold">
                              {log.rollback_id}
                            </td>
                            <td className="p-3.5">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  log.operation_type === "DELETE"
                                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                                    : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                                }`}
                              >
                                {log.operation_type}
                              </span>
                            </td>
                            <td className="p-3.5 text-slate-200">{log.table_name}</td>
                            <td className="p-3.5 text-slate-200">{log.rows_affected}</td>
                            <td className="p-3.5 text-slate-400 text-[11px] truncate max-w-xs font-mono">
                              {log.original_sql}
                            </td>
                            <td className="p-3.5">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] ${
                                  log.status === "active"
                                    ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-semibold"
                                    : "bg-slate-800 text-slate-400 font-sans"
                                }`}
                              >
                                {log.status.toUpperCase()}
                              </span>
                            </td>
                            <td className="p-3.5 text-right">
                              {log.status === "active" ? (
                                <button
                                  onClick={() => handleRollbackAudit(log.rollback_id)}
                                  className="px-2.5 py-1 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[11px] font-sans font-medium flex items-center gap-1 ml-auto transition"
                                >
                                  <Undo2 className="h-3 w-3" />
                                  <span>Rollback</span>
                                </button>
                              ) : (
                                <span className="text-[11px] text-slate-500 font-sans">Rolled Back</span>
                              )}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
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

      {/* Guided Demo Tour Modal */}
      <DemoTourModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
        onSelectPrompt={handleLaunchDemoScenario}
      />

      {/* Architecture Visualizer Modal */}
      <ArchitectureModal
        isOpen={isArchModalOpen}
        onClose={() => setIsArchModalOpen(false)}
      />
    </div>
  );
}
