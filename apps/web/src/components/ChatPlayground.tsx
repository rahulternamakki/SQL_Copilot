"use client";

import React, { useState } from "react";
import {
  Send,
  Sparkles,
  Terminal,
  ShieldCheck,
  AlertTriangle,
  Database,
  ArrowRight,
  Copy,
  CheckCircle2,
  Loader2,
  HelpCircle,
  Clock,
  Layers,
  ChevronDown,
  ChevronUp,
  Table,
  Zap,
  RotateCcw,
  Undo2,
  Check,
  Coins,
  Cpu,
  Activity,
} from "lucide-react";
import { api, ChatResponse, WriteConfirmResult } from "@/lib/api";
import ConfirmationCard from "./ConfirmationCard";

interface ChatPlaygroundProps {
  connectionId: string;
  initialPrompt?: string;
}

export default function ChatPlayground({ connectionId, initialPrompt }: ChatPlaygroundProps) {
  const [query, setQuery] = useState(
    initialPrompt || "Which customers haven't placed an order in the last 90 days?"
  );
  const [loading, setLoading] = useState(false);
  const [clarifying, setClarifying] = useState(false);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [copiedSQL, setCopiedSQL] = useState(false);
  const [showTraceDetails, setShowTraceDetails] = useState(true);
  const [showSpanDrawer, setShowSpanDrawer] = useState(false);

  // Write Confirmation & Rollback State (Phase 3)
  const [writeResult, setWriteResult] = useState<WriteConfirmResult | null>(null);
  const [isRollingBack, setIsRollingBack] = useState(false);
  const [rollbackSuccess, setRollbackSuccess] = useState(false);

  const handleSendQuery = async (customQuery?: string) => {
    const q = customQuery || query;
    if (!q.trim() || !connectionId) return;

    setLoading(true);
    setResponse(null);
    setWriteResult(null);
    setRollbackSuccess(false);

    try {
      const res = await api.sendChatMessage(connectionId, q);
      setResponse(res);
    } catch (err) {
      console.error("Chat execution error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleClarificationSelect = async (optionLabel: string) => {
    if (!response) return;
    setClarifying(true);

    try {
      const res = await api.submitClarification(connectionId, response.query, optionLabel, response.session_id);
      setResponse(res);
    } catch (err) {
      console.error("Clarification error:", err);
    } finally {
      setClarifying(false);
    }
  };

  const handleConfirmWrite = async (token: string) => {
    if (!response || !response.generated_sql) return;
    try {
      const res = await api.confirmWriteOperation(
        connectionId,
        response.generated_sql,
        token,
        response.session_id
      );
      setWriteResult(res);
      setResponse({
        ...response,
        requires_confirmation: false,
        final_summary: `✅ Successfully executed transaction. ${res.rows_affected} row(s) mutated. Rollback snapshot active.`,
      });
    } catch (err: any) {
      alert(`Write failed: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleExecuteRollback = async () => {
    if (!writeResult) return;
    setIsRollingBack(true);
    try {
      await api.rollbackOperation(connectionId, writeResult.rollback_id);
      setRollbackSuccess(true);
    } catch (err: any) {
      alert(`Rollback failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsRollingBack(false);
    }
  };

  const copySQL = (sql: string) => {
    navigator.clipboard.writeText(sql);
    setCopiedSQL(true);
    setTimeout(() => setCopiedSQL(false), 2000);
  };

  // Pipeline Step Status Calculator
  const getStepStatus = (stepName: string) => {
    if (!response && !loading) return "idle";
    if (loading) return "running";

    if (stepName === "planner") return "completed";
    if (stepName === "clarifier") {
      return response?.intent === "ambiguous" ? "halted" : "skipped";
    }
    if (response?.intent === "ambiguous") return "idle";

    if (stepName === "retriever" || stepName === "sql_generator") {
      return response?.generated_sql ? "completed" : "idle";
    }
    if (stepName === "safety_critic") {
      return response?.requires_confirmation ? "halted" : "completed";
    }
    if (stepName === "executor") {
      return response?.execution_result || writeResult ? "completed" : "idle";
    }
    if (stepName === "explainer") return response?.final_summary ? "completed" : "idle";
    return "completed";
  };

  return (
    <div className="flex flex-col h-full overflow-hidden bg-slate-950/40">
      {/* Dynamic LangGraph Pipeline Status Header */}
      <div className="px-6 py-3 border-b border-slate-800/80 bg-slate-900/40 flex items-center justify-between text-xs shrink-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-slate-400 font-medium">LangGraph Pipeline:</span>
          <div className="flex items-center gap-1.5 text-[11px]">
            {/* Planner */}
            <span
              className={`px-2.5 py-0.5 rounded-md font-mono transition ${
                getStepStatus("planner") === "completed"
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  : "bg-slate-800 text-slate-400"
              }`}
            >
              Planner
            </span>
            <ArrowRight className="h-3 w-3 text-slate-600" />

            {/* Clarifier */}
            <span
              className={`px-2.5 py-0.5 rounded-md font-mono transition ${
                getStepStatus("clarifier") === "halted"
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse font-semibold"
                  : getStepStatus("clarifier") === "skipped"
                  ? "bg-slate-800/60 text-slate-500 line-through"
                  : "bg-slate-800 text-slate-400"
              }`}
            >
              Clarifier
            </span>
            <ArrowRight className="h-3 w-3 text-slate-600" />

            {/* Retriever */}
            <span
              className={`px-2.5 py-0.5 rounded-md font-mono transition ${
                getStepStatus("retriever") === "completed"
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  : "bg-slate-800 text-slate-400"
              }`}
            >
              Retriever
            </span>
            <ArrowRight className="h-3 w-3 text-slate-600" />

            {/* SQL Generator */}
            <span
              className={`px-2.5 py-0.5 rounded-md font-mono transition ${
                getStepStatus("sql_generator") === "completed"
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  : "bg-slate-800 text-slate-400"
              }`}
            >
              SQL Gen
            </span>
            <ArrowRight className="h-3 w-3 text-slate-600" />

            {/* Safety Critic */}
            <span
              className={`px-2.5 py-0.5 rounded-md font-mono transition ${
                getStepStatus("safety_critic") === "halted"
                  ? "bg-rose-500/20 text-rose-300 border border-rose-500/50 animate-pulse font-bold"
                  : getStepStatus("safety_critic") === "completed"
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  : "bg-slate-800 text-slate-400"
              }`}
            >
              Safety Critic
            </span>
            <ArrowRight className="h-3 w-3 text-slate-600" />

            {/* Executor */}
            <span
              className={`px-2.5 py-0.5 rounded-md font-mono transition ${
                getStepStatus("executor") === "completed"
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  : "bg-slate-800 text-slate-400"
              }`}
            >
              Executor
            </span>
          </div>
        </div>

        {response && (
          <div className="flex items-center gap-2">
            <span
              className={`text-[11px] font-mono px-2 py-0.5 rounded border ${
                response.risk_level === "high"
                  ? "text-rose-400 bg-rose-500/10 border-rose-500/30 font-bold"
                  : "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
              }`}
            >
              Risk: {response.risk_level?.toUpperCase() || "NONE"}
            </span>
            {response.retry_count > 0 && (
              <span className="text-[11px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                Self-Corrected ({response.retry_count} retry)
              </span>
            )}
          </div>
        )}
      </div>

      {/* Main Conversation Stream */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
        {/* User Query Bubble */}
        <div className="flex gap-3 max-w-3xl">
          <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-300 shrink-0">
            You
          </div>
          <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 text-sm text-slate-200 shadow-md">
            {response ? response.query : query}
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex gap-3 max-w-3xl animate-in fade-in">
            <div className="h-8 w-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-xs font-semibold text-emerald-400 shrink-0">
              <Loader2 className="h-4 w-4 animate-spin text-emerald-400" />
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 space-y-2">
              <p className="font-medium text-slate-300">Orchestrating multi-agent reasoning flow...</p>
              <div className="flex items-center gap-2 text-[11px] text-slate-500">
                <span>Classifying intent</span>
                <span>•</span>
                <span>Safety inspection & dry run</span>
                <span>•</span>
                <span>Synthesizing SQL with Groq LLaMA 3.3 70B</span>
              </div>
            </div>
          </div>
        )}

        {/* Ambiguity Interception Card (Phase 2 Step 2.4) */}
        {response && response.intent === "ambiguous" && (
          <div className="flex gap-3 max-w-3xl animate-in fade-in">
            <div className="h-8 w-8 rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-xs font-semibold text-amber-400 shrink-0">
              <AlertTriangle className="h-4 w-4" />
            </div>
            <div className="flex-1 p-5 rounded-2xl bg-gradient-to-b from-amber-500/10 to-amber-950/20 border border-amber-500/40 space-y-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-amber-500/20 pb-2.5">
                <div className="flex items-center gap-2 text-amber-300 font-semibold text-sm">
                  <HelpCircle className="h-4 w-4" />
                  <span>Ambiguity Intercepted — Clarifier Agent Halted</span>
                </div>
                <span className="text-[10px] font-mono bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded">
                  Zero Hallucination Guarantee
                </span>
              </div>

              <p className="text-xs text-slate-200 font-medium">
                {response.clarification_question || "The query contains ambiguous business criteria. Please clarify your intent:"}
              </p>

              <div className="space-y-2">
                <button
                  onClick={() => handleClarificationSelect("Highest Total Sales Revenue Processed")}
                  disabled={clarifying}
                  className="w-full text-left p-3 rounded-xl bg-slate-900/80 hover:bg-emerald-950/40 border border-slate-700/80 hover:border-emerald-500/40 text-xs text-slate-200 transition flex items-center justify-between group"
                >
                  <div>
                    <span className="font-semibold text-emerald-300 block">Option 1: Highest Total Sales Revenue</span>
                    <span className="text-[11px] text-slate-400">Sum of all completed orders associated with the employee</span>
                  </div>
                  <ArrowRight className="h-4 w-4 text-slate-500 group-hover:text-emerald-400 transition" />
                </button>

                <button
                  onClick={() => handleClarificationSelect("Most Successfully Completed Orders")}
                  disabled={clarifying}
                  className="w-full text-left p-3 rounded-xl bg-slate-900/80 hover:bg-emerald-950/40 border border-slate-700/80 hover:border-emerald-500/40 text-xs text-slate-200 transition flex items-center justify-between group"
                >
                  <div>
                    <span className="font-semibold text-emerald-300 block">Option 2: Most Orders Processed</span>
                    <span className="text-[11px] text-slate-400">Total volume count of customer orders processed</span>
                  </div>
                  <ArrowRight className="h-4 w-4 text-slate-500 group-hover:text-emerald-400 transition" />
                </button>
              </div>

              {clarifying && (
                <div className="flex items-center gap-2 text-xs text-amber-300 pt-1">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Resuming LangGraph execution with selected criteria...</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Phase 3 Destructive Action Confirmation Card */}
        {response && response.requires_confirmation && response.confirmation_token && (
          <div className="flex gap-3 max-w-4xl animate-in fade-in">
            <div className="h-8 w-8 rounded-full bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-xs font-semibold text-rose-400 shrink-0">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div className="flex-1">
              <ConfirmationCard
                sql={response.generated_sql || ""}
                previewText={response.plain_language_preview || "Modifying operation requires authorization."}
                token={response.confirmation_token}
                sampleRows={response.sample_rows}
                columns={response.columns}
                onConfirm={handleConfirmWrite}
                onCancel={() => setResponse(null)}
              />
            </div>
          </div>
        )}

        {/* Phase 3 1-Click Rollback Banner */}
        {writeResult && (
          <div className="flex gap-3 max-w-4xl animate-in fade-in">
            <div className="h-8 w-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-xs font-semibold text-emerald-400 shrink-0">
              <Check className="h-4 w-4" />
            </div>
            <div className="flex-1 p-5 rounded-2xl bg-gradient-to-r from-emerald-950/40 to-slate-900 border border-emerald-500/30 shadow-xl space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-emerald-300 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" />
                    Transaction Executed Successfully ({writeResult.rows_affected} rows affected)
                  </h4>
                  <p className="text-xs text-slate-400">
                    Rollback ID: <strong className="font-mono text-emerald-400">{writeResult.rollback_id}</strong>
                  </p>
                </div>

                {!rollbackSuccess ? (
                  <button
                    onClick={handleExecuteRollback}
                    disabled={isRollingBack}
                    className="px-4 py-2 rounded-xl bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/40 text-xs font-semibold flex items-center gap-1.5 transition"
                  >
                    {isRollingBack ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Undo2 className="h-3.5 w-3.5" />}
                    <span>↩️ Rollback Changes (Within 5 mins)</span>
                  </button>
                ) : (
                  <span className="px-3 py-1.5 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-bold flex items-center gap-1">
                    <CheckCircle2 className="h-3.5 w-3.5" /> State Rolled Back!
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Read Query Answer & Results (When NOT waiting for confirmation) */}
        {response && response.generated_sql && !response.requires_confirmation && !writeResult && (
          <div className="flex gap-3 max-w-4xl animate-in fade-in">
            <div className="h-8 w-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-xs font-semibold text-emerald-400 shrink-0">
              AI
            </div>
            <div className="flex-1 space-y-4">
              {/* Phase 4 Live Observability Telemetry Floating Bar */}
              {response.telemetry && (
                <div className="px-3.5 py-2 rounded-xl bg-[#0b1120] border border-slate-800 text-xs flex items-center justify-between text-slate-400 shadow-sm flex-wrap gap-2">
                  <div className="flex items-center gap-3 font-mono text-[11px]">
                    <span className="flex items-center gap-1 text-slate-300">
                      <Clock className="h-3 w-3 text-emerald-400" />
                      <strong>{response.telemetry.total_latency_ms} ms</strong>
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1 text-slate-300">
                      <Cpu className="h-3 w-3 text-cyan-400" />
                      <strong>{response.telemetry.total_tokens} tokens</strong>
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1 text-slate-300">
                      <Coins className="h-3 w-3 text-amber-400" />
                      <strong>${response.telemetry.estimated_cost_usd}</strong>
                    </span>
                  </div>

                  <button
                    onClick={() => setShowSpanDrawer(!showSpanDrawer)}
                    className="text-[11px] font-sans text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition"
                  >
                    <Activity className="h-3 w-3" />
                    <span>{showSpanDrawer ? "Hide Spans" : "View Node Spans"}</span>
                  </button>
                </div>
              )}

              {/* Phase 4 Agent Execution Node Spans Breakdown */}
              {showSpanDrawer && response.telemetry && (
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-2 animate-in fade-in">
                  <span className="font-semibold text-slate-300 text-[11px] uppercase tracking-wider block">
                    Agent Node Execution Spans (OpenTelemetry / LangSmith Trace)
                  </span>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {response.telemetry.spans.map((s, idx) => (
                      <div key={idx} className="p-2 rounded-lg bg-slate-900 border border-slate-800 font-mono text-[11px] flex justify-between items-center">
                        <span className="text-slate-400 truncate">{s.node_name}</span>
                        <span className="text-emerald-400 font-bold ml-2">{s.duration_ms} ms</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Agent Trace */}
              <div className="p-4 rounded-2xl bg-[#0c1220] border border-slate-800 space-y-3 text-xs shadow-md">
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => setShowTraceDetails(!showTraceDetails)}
                    className="font-semibold text-emerald-400 flex items-center gap-1.5 hover:text-emerald-300 transition"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Agent Grounding & Vector Trace ({response.retrieved_chunks.length} chunks)</span>
                    {showTraceDetails ? <ChevronUp className="h-3 w-3 ml-1" /> : <ChevronDown className="h-3 w-3 ml-1" />}
                  </button>
                  <span className="font-mono text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">
                    Groq LLaMA 3.3 70B
                  </span>
                </div>

                {showTraceDetails && (
                  <div className="space-y-2 pt-1 text-slate-300 border-t border-slate-800/80">
                    <p className="text-[11px] text-slate-400">
                      Grounded tables referenced:{" "}
                      <strong className="text-emerald-300 font-mono font-medium">
                        {response.tables_touched.join(", ") || "customers"}
                      </strong>
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {response.retrieved_chunks.slice(0, 4).map((c, idx) => (
                        <div key={idx} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 text-[11px]">
                          <span className="font-mono text-emerald-400 block font-medium truncate">{c.title}</span>
                          <p className="text-slate-400 line-clamp-2 mt-0.5">{c.content}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Synthesized SQL Query Card */}
              <div className="rounded-2xl overflow-hidden border border-slate-800 bg-[#080d1a] shadow-xl">
                <div className="bg-slate-900/90 px-4 py-2.5 flex items-center justify-between border-b border-slate-800 text-xs">
                  <div className="flex items-center gap-2">
                    <Terminal className="h-3.5 w-3.5 text-emerald-400" />
                    <span className="font-mono font-semibold text-slate-300">Synthesized SQL Statement</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      AST Verified Read-Only
                    </span>
                    <button
                      onClick={() => copySQL(response.generated_sql || "")}
                      className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-mono flex items-center gap-1 transition"
                    >
                      {copiedSQL ? <CheckCircle2 className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                      <span>{copiedSQL ? "Copied" : "Copy"}</span>
                    </button>
                  </div>
                </div>

                <pre className="p-4 text-xs font-mono text-emerald-300 overflow-x-auto leading-relaxed bg-slate-950/60 custom-scrollbar">
                  {response.generated_sql}
                </pre>
              </div>

              {/* Executive Summary */}
              {response.final_summary && (
                <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-500/5 to-cyan-500/5 border border-emerald-500/20 text-sm text-slate-200 leading-relaxed shadow-md space-y-1">
                  <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                    Executive Summary
                  </div>
                  <p>{response.final_summary}</p>
                </div>
              )}

              {/* Execution Results Data Table */}
              {response.execution_result && (
                <div className="rounded-2xl border border-slate-800 overflow-hidden bg-[#0c1220] shadow-xl space-y-2">
                  <div className="px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <Table className="h-3.5 w-3.5 text-emerald-400" />
                      <span className="font-semibold text-slate-200">Execution Results</span>
                      <span className="text-[11px] font-mono text-slate-400">
                        ({response.execution_result.row_count} rows returned)
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      <span>{response.execution_result.execution_time_ms} ms</span>
                    </span>
                  </div>

                  <div className="overflow-x-auto max-h-72 custom-scrollbar">
                    <table className="w-full text-left text-xs border-collapse font-mono">
                      <thead>
                        <tr className="bg-slate-950 border-b border-slate-800 text-slate-400">
                          {response.execution_result.columns.map((col) => (
                            <th key={col} className="py-2.5 px-4 whitespace-nowrap text-emerald-300 font-semibold">
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 text-slate-300">
                        {response.execution_result.rows.map((row, rIdx) => (
                          <tr key={rIdx} className="hover:bg-slate-900/40 transition">
                            {row.map((cell, cIdx) => (
                              <td key={cIdx} className="py-2 px-4 whitespace-nowrap text-[11px]">
                                {cell !== null ? String(cell) : <span className="text-slate-600 italic">null</span>}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Preset Quick Prompt Bar with Write Tests */}
      <div className="px-6 py-2 border-t border-slate-800/80 bg-slate-900/40 flex items-center gap-2 overflow-x-auto text-xs shrink-0">
        <span className="text-slate-500 font-medium whitespace-nowrap flex items-center gap-1">
          <Zap className="h-3 w-3 text-amber-400" /> Presets:
        </span>
        <button
          onClick={() => handleSendQuery("Which customers haven't placed an order in the last 90 days?")}
          className="px-3 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 whitespace-nowrap transition"
        >
          🔍 Inactive 90 Days
        </button>
        <button
          onClick={() => handleSendQuery("Who is our best employee?")}
          className="px-3 py-1 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 whitespace-nowrap transition"
        >
          ⚠️ Test Ambiguity (Best Employee)
        </button>
        <button
          onClick={() => handleSendQuery("Delete all inactive customer accounts who registered before 2022.")}
          className="px-3 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 whitespace-nowrap transition font-semibold"
        >
          🔥 Test Destructive Delete & Rollback
        </button>
        <button
          onClick={() => handleSendQuery("Update unit price for all products in category 'Furniture' to add a 15% inflation increase.")}
          className="px-3 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 whitespace-nowrap transition font-semibold"
        >
          🔥 Test Bulk Update & Rollback
        </button>
      </div>

      {/* Bottom Query Input Bar */}
      <div className="p-4 border-t border-slate-800 bg-[#090e1a] shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendQuery();
          }}
          className="flex gap-2 max-w-4xl mx-auto"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask any database question (e.g. 'Delete inactive accounts' or 'Show sales')..."
            className="flex-1 bg-slate-950 border border-slate-700/80 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition font-normal"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm flex items-center gap-2 transition shadow-lg shadow-emerald-950/60"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            <span>Execute</span>
          </button>
        </form>
      </div>
    </div>
  );
}
