"use client";

import React, { useState, useEffect } from "react";
import { BookOpen, Sparkles, Plus, Trash2, Edit2, Check, X, AlertTriangle, Loader2, Save, Tag } from "lucide-react";
import { api, GlossaryTerm } from "@/lib/api";

interface GlossaryEditorProps {
  connectionId: string;
}

export default function GlossaryEditor({ connectionId }: GlossaryEditorProps) {
  const [terms, setTerms] = useState<GlossaryTerm[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<GlossaryTerm>>({});
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTermForm, setNewTermForm] = useState({
    term: "",
    definition: "",
    target_table: "",
    target_column: "",
    business_rule: "",
    is_ambiguous: false,
    disambiguation_hint: "",
  });

  const fetchTerms = async () => {
    if (!connectionId) return;
    setLoading(true);
    try {
      const data = await api.listGlossary(connectionId);
      setTerms(data);
    } catch (err) {
      console.error("Failed to load glossary:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTerms();
  }, [connectionId]);

  const handleAutoGenerate = async () => {
    setGenerating(true);
    try {
      const newTerms = await api.generateGlossary(connectionId);
      setTerms(newTerms);
    } catch (err) {
      console.error("Auto-generate failed:", err);
    } finally {
      setGenerating(false);
    }
  };

  const handleStartEdit = (t: GlossaryTerm) => {
    setEditingId(t.id);
    setEditForm(t);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditForm({});
  };

  const handleSaveEdit = async (termId: string) => {
    try {
      const updated = await api.updateGlossaryTerm(connectionId, termId, editForm);
      setTerms(terms.map((t) => (t.id === termId ? updated : t)));
      setEditingId(null);
    } catch (err) {
      console.error("Failed to update term:", err);
    }
  };

  const handleDelete = async (termId: string) => {
    try {
      await api.deleteGlossaryTerm(connectionId, termId);
      setTerms(terms.filter((t) => t.id !== termId));
    } catch (err) {
      console.error("Failed to delete term:", err);
    }
  };

  const handleCreateNew = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await api.createGlossaryTerm(connectionId, newTermForm);
      setTerms([...terms, created]);
      setShowAddForm(false);
      setNewTermForm({
        term: "",
        definition: "",
        target_table: "",
        target_column: "",
        business_rule: "",
        is_ambiguous: false,
        disambiguation_hint: "",
      });
    } catch (err) {
      console.error("Failed to create term:", err);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden bg-slate-950/40">
      {/* Header Bar */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/30 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-emerald-400" />
            Business Glossary & Semantic Mapping
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Defines business rules and flags ambiguous terms before RAG retrieval and SQL generation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddForm(true)}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 transition"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add Term</span>
          </button>
          <button
            onClick={handleAutoGenerate}
            disabled={generating}
            className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium flex items-center gap-1.5 transition shadow-lg shadow-emerald-950/40"
          >
            {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
            <span>{generating ? "Drafting with Groq..." : "Auto-Draft with AI"}</span>
          </button>
        </div>
      </div>

      {/* Main Content List */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
        {/* Add New Term Modal/Form */}
        {showAddForm && (
          <form onSubmit={handleCreateNew} className="p-4 rounded-xl bg-slate-900 border border-emerald-500/40 space-y-3 text-xs">
            <div className="flex justify-between items-center text-emerald-400 font-semibold">
              <span>Add New Business Term</span>
              <button type="button" onClick={() => setShowAddForm(false)} className="text-slate-400 hover:text-slate-200">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <input
                type="text"
                required
                placeholder="Business Term (e.g. churned customer)"
                value={newTermForm.term}
                onChange={(e) => setNewTermForm({ ...newTermForm, term: e.target.value })}
                className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
              />
              <input
                type="text"
                placeholder="Target Table (e.g. customers)"
                value={newTermForm.target_table}
                onChange={(e) => setNewTermForm({ ...newTermForm, target_table: e.target.value })}
                className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
              />
            </div>
            <textarea
              required
              rows={2}
              placeholder="Plain language business definition..."
              value={newTermForm.definition}
              onChange={(e) => setNewTermForm({ ...newTermForm, definition: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
            />
            <input
              type="text"
              placeholder="SQL Business Rule Filter (e.g. WHERE status = 'churned')"
              value={newTermForm.business_rule}
              onChange={(e) => setNewTermForm({ ...newTermForm, business_rule: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
            />
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 text-slate-300">
                <input
                  type="checkbox"
                  checked={newTermForm.is_ambiguous}
                  onChange={(e) => setNewTermForm({ ...newTermForm, is_ambiguous: e.target.checked })}
                  className="rounded bg-slate-950 border-slate-700 text-emerald-500"
                />
                <span>Flag as Ambiguous (triggers Clarifier agent)</span>
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-3 py-1 rounded-lg bg-slate-800 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
                >
                  Save Term
                </button>
              </div>
            </div>
          </form>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center p-12 text-slate-400 space-y-2 text-xs">
            <Loader2 className="h-6 w-6 animate-spin text-emerald-400" />
            <p>Loading business glossary...</p>
          </div>
        ) : terms.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-slate-400 space-y-3 text-xs border border-dashed border-slate-800 rounded-2xl">
            <BookOpen className="h-8 w-8 text-slate-600" />
            <p className="text-slate-300 font-medium">No business terms defined yet.</p>
            <p className="text-slate-500 max-w-sm text-center">
              Click &quot;Auto-Draft with AI&quot; to automatically analyze the database schema and generate domain definitions.
            </p>
            <button
              onClick={handleAutoGenerate}
              disabled={generating}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium flex items-center gap-2 transition"
            >
              <Sparkles className="h-4 w-4" />
              <span>Auto-Draft with Groq LLaMA 3.3 70B</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {terms.map((term) => {
              const isEditing = editingId === term.id;

              return (
                <div
                  key={term.id}
                  className={`p-4 rounded-xl border transition space-y-3 ${
                    term.is_ambiguous
                      ? "bg-amber-500/5 border-amber-500/30 hover:border-amber-500/50"
                      : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  {isEditing ? (
                    <div className="space-y-2 text-xs">
                      <input
                        type="text"
                        value={editForm.term || ""}
                        onChange={(e) => setEditForm({ ...editForm, term: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white font-semibold"
                      />
                      <textarea
                        rows={2}
                        value={editForm.definition || ""}
                        onChange={(e) => setEditForm({ ...editForm, definition: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200"
                      />
                      <input
                        type="text"
                        placeholder="SQL Business Rule"
                        value={editForm.business_rule || ""}
                        onChange={(e) => setEditForm({ ...editForm, business_rule: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200"
                      />
                      <div className="flex justify-end gap-2 pt-1">
                        <button
                          onClick={handleCancelEdit}
                          className="px-2.5 py-1 rounded bg-slate-800 text-slate-300"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => handleSaveEdit(term.id)}
                          className="px-3 py-1 rounded bg-emerald-600 text-white font-medium flex items-center gap-1"
                        >
                          <Save className="h-3 w-3" /> Save
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="text-sm font-semibold text-white capitalize flex items-center gap-2">
                            {term.term}
                            {term.is_ambiguous && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-medium">
                                <AlertTriangle className="h-3 w-3" /> Ambiguous (Clarifier Required)
                              </span>
                            )}
                          </h4>
                          {term.target_table && (
                            <span className="inline-block mt-1 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                              Table: {term.target_table}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleStartEdit(term)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                            title="Edit"
                          >
                            <Edit2 className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => handleDelete(term.id)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800"
                            title="Delete"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>

                      <p className="text-xs text-slate-300 leading-relaxed">
                        {term.definition}
                      </p>

                      {term.business_rule && (
                        <div className="p-2 rounded-lg bg-slate-950/80 border border-slate-800/80 text-[11px] font-mono text-emerald-300">
                          <span className="text-slate-500 block text-[10px] uppercase font-sans">SQL Rule</span>
                          {term.business_rule}
                        </div>
                      )}

                      {term.disambiguation_hint && (
                        <div className="text-[11px] text-amber-300/90 italic">
                          💡 Hint: {term.disambiguation_hint}
                        </div>
                      )}
                    </>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
