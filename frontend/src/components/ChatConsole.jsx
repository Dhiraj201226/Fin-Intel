import React, { useRef, useEffect } from 'react';
import { Send, Terminal, Play, Cpu, HelpCircle, RefreshCw } from 'lucide-react';

export default function ChatConsole({ 
  logs, 
  loading, 
  query, 
  setQuery, 
  onSubmit, 
  onReset,
  suggestedQueries 
}) {
  const logEndRef = useRef(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="glass-panel flex-1 flex flex-col min-h-0 overflow-hidden terminal-scan">
      {/* Header */}
      <div className="bg-[#121824] px-4 py-3 border-b border-[#242f49] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-[#10b981]" />
          <span className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
            FinIntel ReAct Reasoning Engine Console
          </span>
          <span className="bg-[#10b981]/15 text-[#10b981] px-1.5 py-0.5 rounded font-mono text-[9px] font-semibold border border-[#10b981]/25">
            ACTIVE
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={onReset}
            title="Reset Terminal Session"
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-mono">
            <span className="status-indicator bg-[#10b981] pulse-green"></span>
            <span>Online</span>
          </div>
        </div>
      </div>

      {/* Logs Console */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3 font-mono text-xs bg-[#0b0f17]">
        {logs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
            <Cpu className="h-10 w-10 text-[#242f49] animate-pulse" />
            <div className="space-y-1.5 max-w-sm">
              <h3 className="text-sm font-semibold text-slate-400">Awaiting Research Instruction</h3>
              <p className="text-xs text-slate-600">
                Input a company ticker or ask an investment analysis question. The agent will autonomously spin up a ReAct planning loop.
              </p>
            </div>
            {/* Suggested prompts */}
            <div className="pt-2 w-full max-w-md">
              <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold mb-2">
                Suggested Research Queries
              </div>
              <div className="grid grid-cols-1 gap-1.5">
                {suggestedQueries.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => setQuery(q)}
                    className="text-left bg-[#121824] hover:bg-[#1a2234] border border-[#242f49] hover:border-slate-600 rounded p-2 text-[11px] text-slate-400 hover:text-white transition-colors"
                  >
                    &gt; {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {logs.map((log, idx) => {
              if (log.type === "thought") {
                return (
                  <div key={idx} className="border-l-2 border-[#f59e0b] pl-3 py-0.5">
                    <span className="text-[#f59e0b] font-bold block mb-1">🧠 [THOUGHT]</span>
                    <p className="text-slate-300 leading-relaxed">{log.text}</p>
                  </div>
                );
              } else if (log.type === "action") {
                return (
                  <div key={idx} className="bg-[#10b981]/5 border border-[#10b981]/20 rounded p-2.5 flex items-start gap-2.5">
                    <span className="bg-[#10b981]/15 text-[#10b981] p-1 rounded font-bold text-[9px] font-mono select-none">
                      ACTION
                    </span>
                    <div className="flex-1 min-w-0">
                      <span className="text-[#10b981] font-semibold font-mono break-all">
                        {log.text}
                      </span>
                    </div>
                  </div>
                );
              } else if (log.type === "observation") {
                return (
                  <div key={idx} className="bg-[#3b82f6]/5 border border-[#3b82f6]/20 rounded p-2.5 flex items-start gap-2.5">
                    <span className="bg-[#3b82f6]/15 text-[#3b82f6] p-1 rounded font-bold text-[9px] font-mono select-none">
                      OBSERV
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-slate-400 whitespace-pre-wrap leading-relaxed">{log.text}</p>
                    </div>
                  </div>
                );
              } else if (log.type === "error") {
                return (
                  <div key={idx} className="bg-[#ef4444]/5 border border-[#ef4444]/20 rounded p-2.5 flex items-start gap-2.5">
                    <span className="bg-[#ef4444]/15 text-[#ef4444] p-1 rounded font-bold text-[9px] font-mono select-none">
                      ERROR
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-[#ef4444] whitespace-pre-wrap leading-relaxed">{log.text}</p>
                    </div>
                  </div>
                );
              }
              return null;
            })}

            {loading && (
              <div className="flex items-center gap-2 border-l-2 border-[#10b981] pl-3 py-1 text-slate-500 animate-pulse">
                <span className="status-indicator bg-[#10b981] pulse-green"></span>
                <span>Agent is reasoning and querying hierarchy database...</span>
              </div>
            )}
            <div ref={logEndRef} />
          </div>
        )}
      </div>

      {/* Input controls */}
      <div className="bg-[#121824] p-3 border-t border-[#242f49]">
        <form 
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit();
          }}
          className="flex items-center gap-2"
        >
          <span className="font-mono text-[#10b981] font-semibold text-xs pl-1 select-none">
            $
          </span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
            placeholder="Search company (e.g. AAPL) or type query, e.g. Evaluate TSLA margin issues..."
            className="flex-1 bg-transparent border-none text-xs text-white placeholder-slate-600 focus:outline-none py-1.5"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="btn-primary py-1.5 px-3.5 text-xs h-8 shrink-0"
          >
            {loading ? (
              <Cpu className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <>
                <Send className="h-3 w-3" />
                <span>Execute</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
