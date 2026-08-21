"use client";

import React, { useState, useEffect } from "react";
import {
  Database,
  Search,
  RotateCcw,
  Key,
  Link2,
  Table,
  Hash,
  Layers,
  Loader2,
  AlertCircle,
  Eye,
  X,
  Clock,
  Sparkles,
  CheckCircle2,
  FileCode,
} from "lucide-react";
import { api, SchemaData, SchemaTable, TableSampleData } from "@/lib/api";

interface SchemaViewerProps {
  connectionId: string;
}

export default function SchemaViewer({ connectionId }: SchemaViewerProps) {
  const [schemaData, setSchemaData] = useState<SchemaData | null>(null);
  const [selectedTable, setSelectedTable] = useState<SchemaTable | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sample Data Modal State
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [sampleData, setSampleData] = useState<TableSampleData | null>(null);
  const [loadingSample, setLoadingSample] = useState(false);

  const fetchSchema = async (forceRefresh = false) => {
    if (!connectionId) return;
    if (forceRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const data = forceRefresh ? await api.refreshSchema(connectionId) : await api.getSchema(connectionId);
      setSchemaData(data);
      if (data.tables.length > 0) {
        setSelectedTable(data.tables[0]);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to load database schema");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleOpenSamplePreview = async (tableName: string) => {
    setPreviewModalOpen(true);
    setLoadingSample(true);
    setSampleData(null);
    try {
      const data = await api.getTableSample(connectionId, tableName, 10);
      setSampleData(data);
    } catch (err) {
      console.error("Failed to load sample data:", err);
    } finally {
      setLoadingSample(false);
    }
  };

  useEffect(() => {
    fetchSchema(false);
  }, [connectionId]);

  const filteredTables = schemaData?.tables.filter((t) =>
    t.table_name.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const totalColumns = schemaData?.tables.reduce((acc, t) => acc + t.columns.length, 0) || 0;
  const totalForeignKeys = schemaData?.tables.reduce((acc, t) => acc + t.foreign_keys.length, 0) || 0;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-slate-400 space-y-3">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
        <p className="text-xs font-medium text-slate-300">Introspecting live database catalog...</p>
        <p className="text-[11px] text-slate-500">Extracting tables, primary keys, and foreign key relations</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => fetchSchema(true)}
            className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded-lg transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!schemaData || schemaData.tables.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-slate-400 space-y-2 text-xs">
        <Database className="h-8 w-8 text-slate-600" />
        <p>No tables detected in this database.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Top Schema Stats Banner */}
      <div className="px-6 py-3 border-b border-slate-800/80 bg-slate-900/40 flex items-center justify-between text-xs shrink-0">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Database Engine:</span>
            <span className="font-mono text-emerald-400 uppercase font-semibold">
              {schemaData.database_type}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Tables:</span>
            <span className="font-mono text-white font-semibold">{schemaData.table_count}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Columns:</span>
            <span className="font-mono text-white font-semibold">{totalColumns}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Foreign Keys:</span>
            <span className="font-mono text-indigo-400 font-semibold">{totalForeignKeys}</span>
          </div>
        </div>

        <button
          onClick={() => fetchSchema(true)}
          disabled={refreshing}
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 transition border border-slate-700"
        >
          <RotateCcw className={`h-3.5 w-3.5 text-emerald-400 ${refreshing ? "animate-spin" : ""}`} />
          <span>{refreshing ? "Refreshing..." : "Refresh Schema"}</span>
        </button>
      </div>

      {/* Main Workspace Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Tables Sidebar List */}
        <div className="w-64 border-r border-slate-800 bg-slate-900/40 flex flex-col shrink-0">
          <div className="p-3 border-b border-slate-800 space-y-2">
            <div className="relative">
              <Search className="h-3.5 w-3.5 text-slate-500 absolute left-2.5 top-2.5" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search tables..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono transition"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
            {filteredTables.map((t) => {
              const isSelected = selectedTable?.table_name === t.table_name;

              return (
                <button
                  key={t.table_name}
                  onClick={() => setSelectedTable(t)}
                  className={`w-full text-left px-3 py-2.5 rounded-xl text-xs font-mono flex items-center justify-between transition ${
                    isSelected
                      ? "bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/40 shadow-sm"
                      : "text-slate-300 hover:bg-slate-800/60"
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <Table className={`h-3.5 w-3.5 ${isSelected ? "text-emerald-400" : "text-slate-500"}`} />
                    <span className="truncate">{t.table_name}</span>
                  </div>
                  {t.approximate_row_count !== null && (
                    <span className="text-[10px] text-slate-500 font-sans shrink-0">
                      {t.approximate_row_count} rows
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Table Columns & Relationships Detail */}
        <div className="flex-1 flex flex-col bg-slate-950/40 overflow-hidden">
          {selectedTable && (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Table Header Bar */}
              <div className="p-4 border-b border-slate-800 bg-slate-900/30 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold font-mono text-white flex items-center gap-2">
                    <Table className="h-4 w-4 text-emerald-400" />
                    {selectedTable.table_name}
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {selectedTable.columns.length} columns • {selectedTable.primary_keys.length} PK • {selectedTable.foreign_keys.length} FK relations
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleOpenSamplePreview(selectedTable.table_name)}
                    className="px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-medium flex items-center gap-1.5 transition"
                  >
                    <Eye className="h-3.5 w-3.5" />
                    <span>Preview Sample Data</span>
                  </button>
                </div>
              </div>

              {/* Columns Table */}
              <div className="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-4">
                <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-900/50 shadow-lg">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-950 border-b border-slate-800 text-slate-400 font-medium">
                        <th className="py-2.5 px-4">Column Name</th>
                        <th className="py-2.5 px-4">Data Type</th>
                        <th className="py-2.5 px-4">Key / Attributes</th>
                        <th className="py-2.5 px-4">Nullable</th>
                        <th className="py-2.5 px-4">Default Value</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-200">
                      {selectedTable.columns.map((col) => {
                        const isPk = selectedTable.primary_keys.includes(col.name);
                        const fk = selectedTable.foreign_keys.find((f) => f.constrained_columns.includes(col.name));

                        return (
                          <tr key={col.name} className="hover:bg-slate-800/30 transition">
                            <td className="py-2.5 px-4 font-mono font-medium text-emerald-300">
                              {col.name}
                            </td>
                            <td className="py-2.5 px-4 font-mono text-slate-300 text-[11px]">
                              <span className="px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700">
                                {col.type}
                              </span>
                            </td>
                            <td className="py-2.5 px-4">
                              <div className="flex items-center gap-1.5 flex-wrap">
                                {isPk && (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] font-mono font-semibold">
                                    <Key className="h-2.5 w-2.5" /> PRIMARY KEY
                                  </span>
                                )}
                                {fk && (
                                  <span
                                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-mono font-medium"
                                    title={`References ${fk.referred_table}(${fk.referred_columns.join(", ")})`}
                                  >
                                    <Link2 className="h-2.5 w-2.5" /> FK → {fk.referred_table}({fk.referred_columns.join(",")})
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-2.5 px-4 text-slate-400">
                              {col.nullable ? "YES" : "NO"}
                            </td>
                            <td className="py-2.5 px-4 font-mono text-[11px] text-slate-400 truncate max-w-[150px]">
                              {col.default || "-"}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Foreign Key Relations Card */}
                {selectedTable.foreign_keys.length > 0 && (
                  <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2 text-xs">
                    <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                      <Link2 className="h-3.5 w-3.5 text-indigo-400" /> Foreign Key Relationships
                    </span>
                    <div className="space-y-1.5 font-mono text-[11px]">
                      {selectedTable.foreign_keys.map((fk, idx) => (
                        <div key={idx} className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 flex items-center gap-2">
                          <span className="text-emerald-400">{selectedTable.table_name}.{fk.constrained_columns.join(", ")}</span>
                          <span className="text-slate-500">──references──▶</span>
                          <span className="text-indigo-300">{fk.referred_table}.{fk.referred_columns.join(", ")}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Sample Data Preview Modal */}
      {previewModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-6 z-50 animate-in fade-in">
          <div className="bg-[#0b101d] border border-slate-700/80 rounded-2xl max-w-4xl w-full p-6 shadow-2xl space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <Table className="h-5 w-5 text-emerald-400" />
                <div>
                  <h3 className="text-base font-semibold text-white font-mono">
                    {selectedTable?.table_name} — Live Sample Preview
                  </h3>
                  <p className="text-xs text-slate-400">AST Read-Only query executed via MCP Server</p>
                </div>
              </div>
              <button
                onClick={() => setPreviewModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-auto rounded-xl border border-slate-800 bg-slate-950/80 custom-scrollbar">
              {loadingSample ? (
                <div className="flex flex-col items-center justify-center p-12 text-slate-400 space-y-2 text-xs">
                  <Loader2 className="h-6 w-6 animate-spin text-emerald-400" />
                  <p>Fetching table sample rows...</p>
                </div>
              ) : sampleData && sampleData.rows.length > 0 ? (
                <table className="w-full text-left text-xs border-collapse font-mono">
                  <thead>
                    <tr className="bg-slate-900 border-b border-slate-800 text-slate-400">
                      {sampleData.columns.map((c) => (
                        <th key={c} className="py-2.5 px-3 whitespace-nowrap text-emerald-300 font-medium">
                          {c}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80 text-slate-200">
                    {sampleData.rows.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/40">
                        {row.map((val, cIdx) => (
                          <td key={cIdx} className="py-2 px-3 whitespace-nowrap text-slate-300 text-[11px]">
                            {val !== null ? String(val) : <span className="text-slate-600 italic">null</span>}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="p-8 text-center text-slate-500 text-xs">No sample rows returned.</div>
              )}
            </div>

            <div className="flex justify-between items-center text-xs text-slate-400 pt-2 border-t border-slate-800">
              <span>Execution Time: <strong className="text-emerald-400 font-mono">{sampleData?.execution_time_ms || 0} ms</strong></span>
              <button
                onClick={() => setPreviewModalOpen(false)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
