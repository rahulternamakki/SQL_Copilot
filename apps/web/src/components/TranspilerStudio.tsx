"use client";

import React, { useState } from "react";
import {
  Code2,
  ArrowRightLeft,
  Copy,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Sparkles,
  Zap,
  Play,
  Terminal,
} from "lucide-react";
import { api, TranspileResult } from "@/lib/api";

export default function TranspilerStudio() {
  const [sourceDialect, setSourceDialect] = useState("snowflake");
  const [inputSQL, setInputSQL] = useState(
    "SELECT * FROM orders WHERE DATEADD('day', -30, CURRENT_TIMESTAMP()) < order_date;"
  );
  const [outputSQL, setOutputSQL] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [result, setResult] = useState<TranspileResult | null>(null);

  const handleTranspile = async () => {
    if (!inputSQL.trim()) return;
    setLoading(true);
    try {
      const res = await api.transpileSQL(inputSQL, sourceDialect);
      setResult(res);
      setOutputSQL(res.transpiled_sql);
    } catch (err: any) {
      console.error("Transpilation failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(outputSQL);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const loadPreset = (dialect: string, sql: string) => {
    setSourceDialect(dialect);
    setInputSQL(sql);
    setOutputSQL("");
    setResult(null);
  };

  return (
    <div className="flex flex-col h-full overflow-hidden bg-slate-950/40 p-6 space-y-4">
      {/* Header Banner */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <ArrowRightLeft className="h-4 w-4 text-emerald-400" />
            Cross-Dialect SQL Transpiler Studio (Step 4.3)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Converts queries from Snowflake, MySQL, BigQuery, SQLite, and TSQL into PostgreSQL 16 standard dialect using AST transpilation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl text-xs">
            <span className="text-slate-400">Source Dialect:</span>
            <select
              value={sourceDialect}
              onChange={(e) => setSourceDialect(e.target.value)}
              className="bg-transparent text-emerald-400 font-semibold focus:outline-none cursor-pointer capitalize"
            >
              <option value="snowflake" className="bg-slate-900 text-slate-200">Snowflake</option>
              <option value="mysql" className="bg-slate-900 text-slate-200">MySQL</option>
              <option value="bigquery" className="bg-slate-900 text-slate-200">BigQuery</option>
              <option value="tsql" className="bg-slate-900 text-slate-200">TSQL (SQL Server)</option>
              <option value="sqlite" className="bg-slate-900 text-slate-200">SQLite</option>
              <option value="oracle" className="bg-slate-900 text-slate-200">Oracle</option>
            </select>
          </div>

          <button
            onClick={handleTranspile}
            disabled={loading}
            className="px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-2 transition shadow-lg shadow-emerald-950/50"
          >
            {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
            <span>Transpile to PostgreSQL</span>
          </button>
        </div>
      </div>

      {/* Preset Dialect Buttons */}
      <div className="flex items-center gap-2 text-xs overflow-x-auto">
        <span className="text-slate-500 font-medium whitespace-nowrap flex items-center gap-1">
          <Zap className="h-3 w-3 text-amber-400" /> Presets:
        </span>
        <button
          onClick={() =>
            loadPreset(
              "snowflake",
              "SELECT * FROM orders WHERE DATEADD('day', -30, CURRENT_TIMESTAMP()) < order_date;"
            )
          }
          className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition"
        >
          ❄️ Snowflake DATEADD
        </button>
        <button
          onClick={() =>
            loadPreset("mysql", "SELECT IFNULL(discount_percent, 0) FROM order_items LIMIT 10;")
          }
          className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition"
        >
          🐬 MySQL IFNULL
        </button>
        <button
          onClick={() =>
            loadPreset(
              "bigquery",
              "SELECT TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY) AS cut_off_date;"
            )
          }
          className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition"
        >
          🔍 BigQuery TIMESTAMP_SUB
        </button>
        <button
          onClick={() =>
            loadPreset("tsql", "SELECT TOP 5 id, first_name, email FROM customers ORDER BY created_at DESC;")
          }
          className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition"
        >
          🪟 TSQL TOP 5
        </button>
      </div>

      {/* Side-by-Side Dual Editor Stage */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1 overflow-hidden">
        {/* Left: Source SQL Editor */}
        <div className="flex flex-col rounded-2xl border border-slate-800 bg-[#080d1a] overflow-hidden shadow-xl">
          <div className="px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <Terminal className="h-3.5 w-3.5 text-slate-400" />
              <span className="font-semibold text-slate-300 uppercase tracking-wide">
                Source ({sourceDialect})
              </span>
            </div>
            <span className="text-[10px] font-mono text-slate-500">Input SQL</span>
          </div>

          <textarea
            value={inputSQL}
            onChange={(e) => setInputSQL(e.target.value)}
            placeholder="Paste your source dialect SQL here..."
            className="flex-1 w-full bg-slate-950/60 p-4 font-mono text-xs text-slate-200 resize-none focus:outline-none custom-scrollbar leading-relaxed"
          />
        </div>

        {/* Right: Target PostgreSQL 16 Output */}
        <div className="flex flex-col rounded-2xl border border-slate-800 bg-[#080d1a] overflow-hidden shadow-xl">
          <div className="px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <Code2 className="h-3.5 w-3.5 text-emerald-400" />
              <span className="font-semibold text-emerald-300 uppercase tracking-wide">
                Target (PostgreSQL 16)
              </span>
            </div>
            {outputSQL && (
              <button
                onClick={handleCopy}
                className="px-2.5 py-0.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-mono flex items-center gap-1 transition"
              >
                {copied ? <CheckCircle2 className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                <span>{copied ? "Copied" : "Copy"}</span>
              </button>
            )}
          </div>

          <pre className="flex-1 w-full bg-slate-950/60 p-4 font-mono text-xs text-emerald-300 overflow-auto custom-scrollbar leading-relaxed">
            {outputSQL || "-- Transpiled PostgreSQL 16 output will appear here..."}
          </pre>
        </div>
      </div>

      {/* Transpilation Result Banner */}
      {result && (
        <div
          className={`p-3.5 rounded-xl text-xs flex items-center justify-between animate-in fade-in ${
            result.success
              ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-300"
              : "bg-rose-500/10 border border-rose-500/30 text-rose-300"
          }`}
        >
          <div className="flex items-center gap-2">
            {result.success ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
            )}
            <span>{result.notes || result.error}</span>
          </div>
          <span className="font-mono text-[10px] bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
            sqlglot AST
          </span>
        </div>
      )}
    </div>
  );
}
