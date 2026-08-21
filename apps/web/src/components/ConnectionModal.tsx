"use client";

import React, { useState } from "react";
import {
  Database,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Loader2,
  X,
  Lock,
  Eye,
  EyeOff,
  Zap,
  Activity,
  KeyRound,
  Server,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api";

interface ConnectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (connectionId: string) => void;
}

export default function ConnectionModal({ isOpen, onClose, onSuccess }: ConnectionModalProps) {
  const [formData, setFormData] = useState({
    connection_id: "",
    display_name: "E-Commerce Demo Database",
    db_type: "postgresql",
    host: "localhost",
    port: 5432,
    database: "ecommerce_demo",
    username: "postgres",
    password: "postgres",
    ssl_mode: "disable",
    read_only: true,
  });

  const [showPassword, setShowPassword] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; latencyMs?: number } | null>(null);

  if (!isOpen) return null;

  const handleQuickFill = () => {
    setFormData({
      connection_id: "conn_ecommerce_demo",
      display_name: "E-Commerce Demo DB",
      db_type: "postgresql",
      host: "localhost",
      port: 5432,
      database: "ecommerce_demo",
      username: "postgres",
      password: "postgres",
      ssl_mode: "disable",
      read_only: true,
    });
    setTestResult(null);
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    const start = performance.now();
    try {
      const payload = {
        ...formData,
        connection_id: formData.connection_id || `conn_${Date.now()}`,
      };
      const res = await api.testConnection(payload);
      const latency = Math.round(performance.now() - start);
      setTestResult({ success: true, message: res.message || "Connection successful! Ready for introspection.", latencyMs: latency });
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || "Connection failed";
      setTestResult({ success: false, message: msg });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const connId = formData.connection_id || `conn_${Date.now()}`;
      const payload = { ...formData, connection_id: connId };
      await api.saveConnection(payload);
      onSuccess(connId);
      onClose();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || "Failed to save connection";
      setTestResult({ success: false, message: msg });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
      <div className="bg-[#0b101d] border border-slate-700/80 rounded-2xl max-w-xl w-full p-6 shadow-2xl shadow-emerald-950/20 space-y-5">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                Connect New Database
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  Step 1.1
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Credentials encrypted via AES-128 Fernet in local vault • Zero LLM access
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800/60 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Quick Fill Preset Card */}
        <div className="p-3 rounded-xl bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Zap className="h-4 w-4 text-emerald-400 shrink-0" />
            <span className="text-xs text-slate-200 font-medium">Local Seeded E-Commerce Database</span>
          </div>
          <button
            type="button"
            onClick={handleQuickFill}
            className="px-3 py-1 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black text-xs font-semibold transition shadow-md shadow-emerald-950/40"
          >
            Load Preset
          </button>
        </div>

        {/* Connection Form */}
        <form onSubmit={handleSave} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Display Name</label>
              <input
                type="text"
                required
                value={formData.display_name}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                placeholder="Production PostgreSQL"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500 transition"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Database Engine</label>
              <select
                value={formData.db_type}
                onChange={(e) => setFormData({ ...formData, db_type: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500 transition"
              >
                <option value="postgresql">PostgreSQL 14 / 15 / 16</option>
                <option value="mysql">MySQL (Coming Soon)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2">
              <label className="block text-slate-400 mb-1 font-medium">Host Address</label>
              <input
                type="text"
                required
                value={formData.host}
                onChange={(e) => setFormData({ ...formData, host: e.target.value })}
                placeholder="localhost"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono transition"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Port</label>
              <input
                type="number"
                required
                value={formData.port}
                onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) || 5432 })}
                placeholder="5432"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono transition"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Database Name</label>
              <input
                type="text"
                required
                value={formData.database}
                onChange={(e) => setFormData({ ...formData, database: e.target.value })}
                placeholder="ecommerce_demo"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono transition"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Database User</label>
              <input
                type="text"
                required
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                placeholder="postgres"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-medium">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="••••••••"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 pr-10 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono transition"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-200"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {/* READ-ONLY TOGGLE (CRITICAL ARCHITECTURAL SAFETY PRINCIPLE) */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                <span className="font-semibold text-slate-200">Enforce Read-Only Mode (Default)</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.read_only}
                  onChange={(e) => setFormData({ ...formData, read_only: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-600"></div>
              </label>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              {formData.read_only
                ? "🔒 Guarded Read Mode: All mutating statements (UPDATE/DELETE/INSERT/DROP) are rejected at the AST level by the MCP server."
                : "⚠️ Write-Enabled Opt-in: Destructive writes require explicit confirmation tokens and 5-minute auto-rollback logging."}
            </p>
          </div>

          {/* Real-time Test Ping Feedback */}
          {testResult && (
            <div
              className={`p-3 rounded-xl flex items-center justify-between text-xs animate-in fade-in ${
                testResult.success
                  ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-300"
                  : "bg-rose-500/10 border border-rose-500/30 text-rose-300"
              }`}
            >
              <div className="flex items-center gap-2">
                {testResult.success ? (
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
                ) : (
                  <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                )}
                <span>{testResult.message}</span>
              </div>
              {testResult.latencyMs !== undefined && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                  {testResult.latencyMs} ms
                </span>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={handleTest}
              disabled={testing}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium flex items-center gap-1.5 transition border border-slate-700"
            >
              {testing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Activity className="h-3.5 w-3.5 text-emerald-400" />}
              <span>Test Connection</span>
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium flex items-center gap-1.5 transition shadow-lg shadow-emerald-950/50"
            >
              {saving && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              <span>Save & Introspect</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
