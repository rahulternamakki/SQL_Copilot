"use client";

import React, { useState, useEffect } from "react";
import {
  AlertOctagon,
  ShieldAlert,
  Clock,
  CheckCircle2,
  XCircle,
  Table,
  Loader2,
  ArrowRight,
  Flame,
} from "lucide-react";

interface ConfirmationCardProps {
  sql: string;
  previewText: string;
  token: string;
  sampleRows?: any[][];
  columns?: string[];
  estimatedRows?: number;
  onConfirm: (token: string) => Promise<void>;
  onCancel: () => void;
}

export default function ConfirmationCard({
  sql,
  previewText,
  token,
  sampleRows = [],
  columns = [],
  estimatedRows = 0,
  onConfirm,
  onCancel,
}: ConfirmationCardProps) {
  const [timeLeft, setTimeLeft] = useState(300); // 5 minutes in seconds
  const [isConfirming, setIsConfirming] = useState(false);

  useEffect(() => {
    if (timeLeft <= 0) return;
    const interval = setInterval(() => {
      setTimeLeft((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [timeLeft]);

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  const handleConfirmClick = async () => {
    setIsConfirming(true);
    try {
      await onConfirm(token);
    } finally {
      setIsConfirming(false);
    }
  };

  const isExpired = timeLeft <= 0;

  return (
    <div className="p-6 rounded-2xl bg-gradient-to-b from-rose-950/40 via-[#0d1222] to-[#090d18] border-2 border-rose-500/50 shadow-2xl shadow-rose-950/40 space-y-4 animate-in fade-in duration-300">
      {/* Header with Hazard Badge & 5-Minute Timer */}
      <div className="flex items-center justify-between border-b border-rose-500/30 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400 border border-rose-500/40 animate-pulse">
            <Flame className="h-5 w-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-rose-300 flex items-center gap-2">
              High-Risk Destructive Action — Human Confirmation Required
            </h4>
            <p className="text-xs text-slate-400">
              Safety Critic halted execution • Transaction rollback snapshot will be captured before mutating
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-mono">
          <Clock className="h-3.5 w-3.5" />
          <span className="font-bold">{isExpired ? "EXPIRED" : formatTime(timeLeft)}</span>
        </div>
      </div>

      {/* Impact Explanation */}
      <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-200 space-y-1">
        <span className="font-semibold text-rose-400 uppercase text-[10px] tracking-wider block">
          Plain Language Impact
        </span>
        <p className="leading-relaxed font-medium">{previewText}</p>
      </div>

      {/* Before-State Row Diff Preview Table */}
      {sampleRows && sampleRows.length > 0 && (
        <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-950/90 space-y-1.5">
          <div className="px-3.5 py-2 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5 font-semibold text-slate-300">
              <Table className="h-3.5 w-3.5 text-rose-400" />
              <span>Before-State Row Diff (Sample {sampleRows.length} rows to be modified/deleted)</span>
            </div>
            <span className="text-[10px] font-mono text-slate-500">Live Snapshot</span>
          </div>

          <div className="overflow-x-auto max-h-48 custom-scrollbar">
            <table className="w-full text-left text-xs border-collapse font-mono">
              <thead>
                <tr className="bg-slate-900/60 border-b border-slate-800 text-slate-400">
                  {columns.map((col) => (
                    <th key={col} className="py-2 px-3 whitespace-nowrap text-rose-300 text-[11px]">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {sampleRows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-rose-950/20 transition">
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="py-1.5 px-3 whitespace-nowrap text-[11px] text-slate-300">
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

      {/* SQL Code Box */}
      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 font-mono text-xs text-rose-300/90 break-all leading-relaxed">
        {sql}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-2">
        <button
          onClick={onCancel}
          disabled={isConfirming}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition flex items-center gap-1.5"
        >
          <XCircle className="h-4 w-4" />
          <span>Cancel & Abort</span>
        </button>

        <button
          onClick={handleConfirmClick}
          disabled={isConfirming || isExpired}
          className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white text-xs font-bold transition flex items-center gap-2 shadow-lg shadow-rose-950/60 disabled:opacity-50"
        >
          {isConfirming ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <AlertOctagon className="h-4 w-4" />
          )}
          <span>
            {isExpired
              ? "Token Expired"
              : isConfirming
              ? "Executing Transaction & Snapshot..."
              : "Confirm & Execute Mutation"}
          </span>
        </button>
      </div>
    </div>
  );
}
