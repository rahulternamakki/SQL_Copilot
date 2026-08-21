"use client";

import React from "react";
import {
  ShieldCheck,
  Layers,
  Database,
  Lock,
  Cpu,
  ArrowRight,
  CheckCircle2,
  X,
  Server,
  Zap,
  RotateCcw,
  Sparkles,
} from "lucide-react";

interface ArchitectureModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ArchitectureModal({ isOpen, onClose }: ArchitectureModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl max-h-[90vh] rounded-3xl bg-[#0a0f1d] border border-slate-700/80 shadow-2xl overflow-hidden flex flex-col">
        {/* Top Header */}
        <div className="p-6 bg-gradient-to-r from-slate-900 via-[#0d1424] to-slate-900 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Governed Database Copilot — System Architecture & Design
              </h3>
              <p className="text-xs text-slate-400">
                Process-Isolated 3-Tier Security Model with Human-in-the-Loop Multi-Agent Governance
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Modal Main Body */}
        <div className="p-6 space-y-6 flex-1 overflow-y-auto custom-scrollbar">
          {/* Architectural Layer 1: Frontend Dashboard */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-white font-bold text-sm">
                <span className="h-6 w-6 rounded-lg bg-emerald-500/20 text-emerald-300 flex items-center justify-center text-xs font-mono">
                  1
                </span>
                <span>Layer 1: Ultra-Premium Frontend Dashboard (Next.js 14 App Router)</span>
              </div>
              <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20">
                Port 3000
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed font-normal">
              Provides the interactive Chat Playground, live per-node execution telemetry, the high-hazard Confirmation Hazard Card with before-state row diff preview, the Cross-Dialect SQL Transpiler Studio, and the 1-Click Rollback Banner.
            </p>
          </div>

          {/* Architectural Layer 2: Multi-Agent Orchestration */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-white font-bold text-sm">
                <span className="h-6 w-6 rounded-lg bg-purple-500/20 text-purple-300 flex items-center justify-center text-xs font-mono">
                  2
                </span>
                <span>Layer 2: Multi-Agent State Machine (LangGraph + Groq LLaMA 3.3 70B)</span>
              </div>
              <span className="text-[10px] font-mono bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded border border-purple-500/20">
                Port 8000
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
                <strong className="text-cyan-300 block font-mono text-[11px]">Planner & Clarifier</strong>
                <p className="text-[11px] text-slate-400">Classifies intent & halts for human clarification on ambiguous terms.</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
                <strong className="text-emerald-300 block font-mono text-[11px]">Retriever & SQL Gen</strong>
                <p className="text-[11px] text-slate-400">Pulls Qdrant chunks & synthesizes accurate PostgreSQL queries with self-correction.</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
                <strong className="text-rose-300 block font-mono text-[11px]">Safety Critic Agent</strong>
                <p className="text-[11px] text-slate-400">Enforces Teller vs. Approver isolation & issues HMAC confirmation tokens.</p>
              </div>
            </div>
          </div>

          {/* Architectural Layer 3: Process-Isolated MCP DB Server */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-white font-bold text-sm">
                <span className="h-6 w-6 rounded-lg bg-cyan-500/20 text-cyan-300 flex items-center justify-center text-xs font-mono">
                  3
                </span>
                <span>Layer 3: Isolated Database Server & Security Vault (Model Context Protocol)</span>
              </div>
              <span className="text-[10px] font-mono bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded border border-cyan-500/20">
                Port 8001
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
                <strong className="text-amber-300 block font-mono text-[11px]">AES-128 Fernet Credential Vault</strong>
                <p className="text-[11px] text-slate-400">Database passwords never reach the LLM or frontend. All credentials remain encrypted at rest.</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
                <strong className="text-emerald-300 block font-mono text-[11px]">ACID Rollback Manager & SQLite Log</strong>
                <p className="text-[11px] text-slate-400">Captures before-state JSON row snapshots and computes inverse SQL for 1-click state reversion.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-5 bg-slate-900/80 border-t border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>Zero raw passwords exposed in prompt context</span>
          </div>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition"
          >
            Close Guide
          </button>
        </div>
      </div>
    </div>
  );
}
