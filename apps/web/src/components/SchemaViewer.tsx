"use client";

import React, { useState, useEffect } from "react";
import { Database, Search, RotateCcw, Key, Link2, Table, Hash, Layers, Loader2, AlertCircle } from "lucide-react";
import { api, SchemaData, SchemaTable } from "@/lib/api";

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

  useEffect(() => {
    fetchSchema(false);
  }, [connectionId]);

  const filteredTables = schemaData?.tables.filter((t) =>
    t.table_name.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-slate-400 space-y-3">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
        <p className="text-xs">Introspecting live database schema...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 shrink-0" />
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
        <p>No tables found in this database.</p>
      </div>
    );
  }

  return (
    <div className="flex h-full overflow-hidden">
      {/* Tables List Sidebar */}
      <div className="w-64 border-r border-slate-800 bg-slate-900/40 flex flex-col shrink-0">
        <div className="p-3 border-b border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-emerald-400" /> Tables ({schemaData.table_count})
            </span>
            <button
              onClick={() => fetchSchema(true)}
              disabled={refreshing}
              title="Refresh Schema"
              className="p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            >
              <RotateCcw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin text-emerald-400" : ""}`} />
            </button>
          </div>
          <div className="relative">
            <Search className="h-3.5 w-3.5 text-slate-500 absolute left-2.5 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search tables..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
          {filteredTables.map((t) => (
            <button
              key={t.table_name}
              onClick={() => setSelectedTable(t)}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs font-mono flex items-center justify-between transition ${
                selectedTable?.table_name === t.table_name
                  ? "bg-emerald-500/20 text-emerald-300 font-medium border border-emerald-500/30"
                  : "text-slate-300 hover:bg-slate-800/60"
              }`}
            >
              <span className="truncate">{t.table_name}</span>
              {t.approximate_row_count !== null && (
                <span className="text-[10px] text-slate-500 font-sans">
                  {t.approximate_row_count} rows
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Selected Table Columns Details */}
      <div className="flex-1 flex flex-col bg-slate-950/40 overflow-hidden">
        {selectedTable && (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Table Details Header */}
            <div className="p-4 border-b border-slate-800 bg-slate-900/30 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold font-mono text-white flex items-center gap-2">
                  <Table className="h-4 w-4 text-emerald-400" />
                  {selectedTable.table_name}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {selectedTable.columns.length} columns • {selectedTable.primary_keys.length} primary keys • {selectedTable.foreign_keys.length} foreign keys
                </p>
              </div>
              <div className="text-[11px] font-mono text-slate-400 bg-slate-800/60 px-2.5 py-1 rounded-lg border border-slate-700/50">
                Type: {schemaData.database_type.toUpperCase()}
              </div>
            </div>

            {/* Columns Table */}
            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
              <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-900/50">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-950 border-b border-slate-800 text-slate-400 font-medium">
                      <th className="py-2.5 px-4">Column Name</th>
                      <th className="py-2.5 px-4">Data Type</th>
                      <th className="py-2.5 px-4">Key / Attributes</th>
                      <th className="py-2.5 px-4">Nullable</th>
                      <th className="py-2.5 px-4">Default</th>
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
                            {col.type}
                          </td>
                          <td className="py-2.5 px-4">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              {isPk && (
                                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] font-mono">
                                  <Key className="h-2.5 w-2.5" /> PK
                                </span>
                              )}
                              {fk && (
                                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-mono" title={`References ${fk.referred_table}(${fk.referred_columns.join(", ")})`}>
                                  <Link2 className="h-2.5 w-2.5" /> FK → {fk.referred_table}
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
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
