import React, { useState } from 'react';
import { Database, FileCode, CheckCircle, AlertTriangle, Layers, Search, Cpu, Trash2 } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:7860";

export default function MemoryVault({ episodicLogs, vectorLogs }) {
  const [subTab, setSubTab] = useState('episodic');
  const [search, setSearch] = useState('');

  const safeEpisodic = Array.isArray(episodicLogs) ? episodicLogs : [];
  const safeVector = Array.isArray(vectorLogs) ? vectorLogs : [];

  const filteredEpisodic = safeEpisodic.filter(log => 
    (log.query || '').toLowerCase().includes(search.toLowerCase()) ||
    (log.status || '').toLowerCase().includes(search.toLowerCase())
  );

  const filteredVector = safeVector.filter(log => 
    (log.ticker || '').toLowerCase().includes(search.toLowerCase()) ||
    (log.snippet || '').toLowerCase().includes(search.toLowerCase()) ||
    (log.tier || '').toLowerCase().includes(search.toLowerCase())
  );

  const handleDeleteItem = async (type, id) => {
    if (window.confirm(`Delete this ${type} memory permanently?`)) {
      try {
        await fetch(`${API_BASE_URL}/api/memory/${type}/${id}`, {
          method: "DELETE",
          headers: { "X-API-Key": "test_key" }
        });
        window.location.reload();
      } catch (err) {
        alert("Failed to delete: " + err.message);
      }
    }
  };

  return (
    <div className="glass-panel p-5 flex flex-col gap-4 min-h-0 overflow-hidden">
      {/* Header */}
      <div className="flex justify-between items-start shrink-0">
        <div>
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <Database className="h-4 w-4 text-[#8b5cf6]" />
            <span>Memory Vault Databases</span>
          </h3>
          <p className="text-[10px] text-slate-500">
            Inspect long-term vector facts (ChromaDB) and episodic error recovery history (SQLite).
          </p>
        </div>
        <button
          onClick={async () => {
            if (window.confirm("Are you sure you want to permanently delete all Memory Vault databases?")) {
              try {
                await fetch(`${API_BASE_URL}/api/memory`, { method: "DELETE" });
                window.location.reload();
              } catch(e) {
                console.error(e);
              }
            }
          }}
          className="flex items-center gap-1.5 py-1 px-2.5 rounded bg-[#ef4444]/10 border border-[#ef4444]/30 text-[#ef4444] hover:bg-[#ef4444]/20 transition-all font-mono text-[10px]"
        >
          <Trash2 className="h-3.5 w-3.5" />
          Clear Memory
        </button>
      </div>

      {/* Database Tabs & Search Bar */}
      <div className="flex flex-col sm:flex-row justify-between gap-3 border-b border-[#242f49] pb-3 shrink-0">
        <div className="flex gap-2 font-mono text-[10px]">
          <button
            onClick={() => { setSubTab('episodic'); setSearch(''); }}
            className={`py-1.5 px-3 rounded border flex items-center gap-1.5 transition-all ${
              subTab === 'episodic'
                ? 'border-[#8b5cf6] bg-[#8b5cf6]/10 text-[#8b5cf6]'
                : 'border-[#242f49] text-slate-400 hover:border-slate-600'
            }`}
          >
            <Database className="h-3.5 w-3.5" />
            SQLite: Episodic Memory
          </button>
          <button
            onClick={() => { setSubTab('vector'); setSearch(''); }}
            className={`py-1.5 px-3 rounded border flex items-center gap-1.5 transition-all ${
              subTab === 'vector'
                ? 'border-[#8b5cf6] bg-[#8b5cf6]/10 text-[#8b5cf6]'
                : 'border-[#242f49] text-slate-400 hover:border-slate-600'
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            ChromaDB: Long-Term Vectors
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search memory records..."
            className="bg-[#0b0f17] border border-[#242f49] rounded px-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-[#8b5cf6] w-48 font-mono"
          />
        </div>
      </div>

      {/* Main Database Views */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {subTab === 'episodic' ? (
          /* SQLite Episodic list */
          <div className="space-y-3 font-mono text-[10px]">
            {filteredEpisodic.length === 0 ? (
              <div className="text-center p-6 text-slate-600">No episodic logs match search.</div>
            ) : (
              filteredEpisodic.map((log, idx) => (
                <div key={idx} className="border border-[#242f49] rounded p-3 bg-[#121824]/20 space-y-2">
                  <div className="flex justify-between items-center border-b border-[#242f49] pb-1.5">
                    <span className="text-[#8b5cf6] font-bold">{log.id}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-slate-500">{log.timestamp}</span>
                      <button onClick={() => handleDeleteItem('episodic', log.id)} className="text-slate-500 hover:text-[#ef4444] transition-colors">
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    <div>
                      <span className="text-slate-500 block">Query:</span>
                      <span className="text-slate-200">{log.query}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Status:</span>
                      <span className={`inline-flex items-center gap-1 font-bold ${
                        log.status === 'SUCCESS' ? 'text-[#10b981]' : 'text-[#f59e0b]'
                      }`}>
                        {log.status === 'SUCCESS' ? <CheckCircle className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
                        {log.status}
                      </span>
                    </div>
                  </div>
                    <div className="pt-1.5 border-t border-[#242f49]/60">
                      <span className="text-slate-500 block">Orchestrated Tools:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {(log.toolsUsed || []).map((t, tid) => (
                          <span key={tid} className="bg-[#242f49] text-slate-300 px-1.5 py-0.2 rounded">
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  {log.failures !== "None" && (
                    <div className="pt-1.5 border-t border-[#242f49]/60 space-y-1">
                      <span className="text-[#ef4444] font-bold block">🚨 Tool Mismatch / Failure:</span>
                      <span className="text-slate-300 block bg-[#ef4444]/5 border border-[#ef4444]/20 p-2 rounded">
                        {log.failures}
                      </span>
                      <span className="text-[#10b981] font-bold block mt-1">✓ Automated Recovery Sequence:</span>
                      <span className="text-slate-300 block bg-[#10b981]/5 border border-[#10b981]/20 p-2 rounded">
                        {log.recovery}
                      </span>
                    </div>
                  )}
                  <div className="pt-1.5 border-t border-[#242f49]/60">
                    <span className="text-slate-500 block">Reasoning Strategy:</span>
                    <span className="text-slate-400 block mt-1 italic">{log.strategy}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        ) : (
          /* ChromaDB Vector list */
          <div className="space-y-3 font-mono text-[10px]">
            {filteredVector.length === 0 ? (
              <div className="text-center p-6 text-slate-600">No vectors match search.</div>
            ) : (
              filteredVector.map((log, idx) => (
                <div key={idx} className="border border-[#242f49] rounded p-3 bg-[#121824]/20 space-y-2">
                  <div className="flex justify-between items-center border-b border-[#242f49] pb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[#10b981] font-bold">{log.id}</span>
                      <span className="bg-[#8b5cf6]/10 text-[#8b5cf6] px-1.5 py-0.2 rounded font-bold border border-[#8b5cf6]/20">
                        {log.ticker}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-slate-500 font-bold">{log.tier}</span>
                      <button onClick={() => handleDeleteItem('vector', log.id)} className="text-slate-500 hover:text-[#ef4444] transition-colors">
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500 block mb-1">Vector Coordinates (1536-dim snippet):</span>
                    <div className="bg-[#0b0f17] border border-[#242f49] p-2 rounded text-[#8b5cf6] text-[9px] truncate">
                      {log.vector}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Text Chunk Payload:</span>
                    <p className="text-slate-300 leading-normal bg-[#0b0f17] border border-[#242f49] p-2 rounded mt-1 whitespace-pre-wrap">
                      {log.snippet}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
