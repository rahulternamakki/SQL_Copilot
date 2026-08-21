"use client";

import React, { useState } from "react";
import {
  Sparkles,
  HelpCircle,
  ShieldCheck,
  Award,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  X,
  Play,
  Flame,
  Clock,
  Terminal,
  Layers,
  Database,
  Undo2,
} from "lucide-react";

interface DemoTourModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectPrompt: (prompt: string, targetTab?: "chat" | "transpiler" | "benchmark") => void;
}

const DEMO_STEPS = [
  {
    step: 1,
    badge: "Scenario 1: Grounded Analytical Read & Telemetry",
    icon: Sparkles,
    color: "emerald",
    title: "Zero-Hallucination Schema Grounding",
    description:
      "Executes a natural-language analytical question grounded against Qdrant vector embeddings. Inspects the AST for read-only safety, retrieves data through the isolated MCP database server, and surfaces real-time millisecond latency spans, token counts, and cost telemetry.",
    prompt: "Which customers haven't placed an order in the last 90 days?",
    targetTab: "chat" as const,
    highlights: [
      "Qdrant Semantic Schema & Glossary Search",
      "Groq LLaMA 3.3 70B SQL Synthesis",
      "Live Telemetry Bar (Latency, Tokens, Cost)",
      "Expandable Agent Node Latency Spans",
    ],
  },
  {
    step: 2,
    badge: "Scenario 2: Ambiguity Interception",
    icon: HelpCircle,
    color: "amber",
    title: "Zero-Guessing Clarifier Agent",
    description:
      "When a user asks a question with subjective or undefined business metrics (e.g. 'best employee' or 'churn rate'), the Clarifier Agent immediately halts execution, refuses to guess, and presents explicit disambiguation choices.",
    prompt: "Who is our best employee?",
    targetTab: "chat" as const,
    highlights: [
      "Human-in-the-Loop State Machine Interruption",
      "Disambiguation Options Formulated in UI",
      "Zero Hallucination Guarantee",
      "Resumes Seamlessly Once Clarified",
    ],
  },
  {
    step: 3,
    badge: "Scenario 3: Destructive Mutation & 1-Click Rollback",
    icon: Flame,
    color: "rose",
    title: "Teller vs. Approver Safety Layer & ACID Undo",
    description:
      "Destructive operations (DELETE / UPDATE / DROP) are intercepted by the Safety Critic. Displays a live 5-minute countdown clock, an interactive before-state row diff table, issues an HMAC confirmation token, and enables instant 1-click state rollback.",
    prompt: "Delete all inactive customer accounts who registered before 2022.",
    targetTab: "chat" as const,
    highlights: [
      "5-Minute Expiration Countdown Clock",
      "Interactive Before-State Row Diff Table",
      "Cryptographic HMAC-SHA256 Token",
      "1-Click Rollback State Restoration",
    ],
  },
  {
    step: 4,
    badge: "Scenario 4: Transpiler Studio & 30-Question Evals",
    icon: Award,
    color: "cyan",
    title: "Cross-Dialect SQL & Benchmark Scorecard",
    description:
      "Explore the Cross-Dialect SQL Transpiler Studio (converting Snowflake, MySQL, BigQuery into PostgreSQL) and view the automated 30-question evaluation benchmark scorecard achieving 100% precision.",
    prompt: "SELECT TOP 5 * FROM customers ORDER BY created_at DESC (TSQL)",
    targetTab: "benchmark" as const,
    highlights: [
      "Snowflake / MySQL / BigQuery to Postgres Transpilation",
      "30 Categorized Benchmark Questions",
      "100% Ambiguity Interception Score",
      "100% Destructive Write Interception Score",
    ],
  },
];

export default function DemoTourModal({ isOpen, onClose, onSelectPrompt }: DemoTourModalProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  if (!isOpen) return null;

  const current = DEMO_STEPS[currentStepIndex];
  const IconComponent = current.icon;

  const handleLaunchScenario = () => {
    onSelectPrompt(current.prompt, current.targetTab);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl rounded-3xl bg-[#0a0f1d] border border-slate-700/80 shadow-2xl overflow-hidden flex flex-col">
        {/* Top Header */}
        <div className="p-6 bg-gradient-to-r from-slate-900 via-[#0d1424] to-slate-900 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Governed Database Copilot — Guided Demo Tour
              </h3>
              <p className="text-xs text-slate-400">
                Interactive 4-Step Walkthrough for Interviews & Technical Presentations
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

        {/* Step Progress Bar */}
        <div className="grid grid-cols-4 border-b border-slate-800 bg-slate-950/60">
          {DEMO_STEPS.map((step, idx) => (
            <button
              key={step.step}
              onClick={() => setCurrentStepIndex(idx)}
              className={`py-3 px-2 text-center text-xs font-semibold border-b-2 transition flex items-center justify-center gap-1.5 ${
                currentStepIndex === idx
                  ? "border-emerald-400 text-emerald-300 bg-emerald-500/5"
                  : "border-transparent text-slate-500 hover:text-slate-300"
              }`}
            >
              <span className="h-5 w-5 rounded-full bg-slate-800 flex items-center justify-center text-[10px] font-mono">
                {step.step}
              </span>
              <span className="hidden sm:inline">Scenario {step.step}</span>
            </button>
          ))}
        </div>

        {/* Modal Main Body */}
        <div className="p-6 space-y-5 flex-1 overflow-y-auto custom-scrollbar">
          {/* Badge & Title */}
          <div className="space-y-1.5">
            <span
              className={`text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full border ${
                current.color === "emerald"
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                  : current.color === "amber"
                  ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                  : current.color === "rose"
                  ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                  : "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
              }`}
            >
              {current.badge}
            </span>
            <h4 className="text-lg font-bold text-white">{current.title}</h4>
            <p className="text-xs text-slate-300 leading-relaxed font-normal">{current.description}</p>
          </div>

          {/* Key Feature Highlights Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {current.highlights.map((h, i) => (
              <div key={i} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                <span className="text-slate-200">{h}</span>
              </div>
            ))}
          </div>

          {/* Test Prompt Box */}
          <div className="p-4 rounded-2xl bg-[#060a14] border border-slate-800 space-y-2">
            <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block font-semibold">
              Demo Execution Prompt
            </span>
            <div className="font-mono text-xs text-emerald-300 break-all">{current.prompt}</div>
          </div>
        </div>

        {/* Modal Footer Controls */}
        <div className="p-5 bg-slate-900/80 border-t border-slate-800 flex items-center justify-between">
          <button
            onClick={() => setCurrentStepIndex((prev) => Math.max(0, prev - 1))}
            disabled={currentStepIndex === 0}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Previous</span>
          </button>

          <div className="flex items-center gap-3">
            <button
              onClick={handleLaunchScenario}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold flex items-center gap-2 transition shadow-lg shadow-emerald-950/60"
            >
              <Play className="h-4 w-4" />
              <span>Launch This Scenario in Copilot</span>
            </button>

            <button
              onClick={() => setCurrentStepIndex((prev) => Math.min(DEMO_STEPS.length - 1, prev + 1))}
              disabled={currentStepIndex === DEMO_STEPS.length - 1}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <span>Next</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
