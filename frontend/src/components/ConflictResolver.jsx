import React from 'react';
import { GitMerge, ShieldAlert, CheckCircle2, ChevronRight, Award } from 'lucide-react';

export default function ConflictResolver({ conflicts }) {
  return (
    <div className="glass-panel p-5 flex flex-col gap-4 min-h-0 overflow-y-auto">
      <div>
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <GitMerge className="h-4 w-4 text-[#ef4444]" />
          <span>Conflict Resolution Engine Lab</span>
        </h3>
        <p className="text-[10px] text-slate-500">
          Reviews mismatched numeric data across tiers, performs verification, selects the highest reliability source, and logs discrepancies.
        </p>
      </div>

      <div className="space-y-4 flex-1">
        {conflicts.map((conflict, idx) => (
          <div 
            key={idx} 
            className="border border-[#242f49] rounded-lg overflow-hidden bg-[#121824]/40"
          >
            {/* Header Banner */}
            <div className="bg-[#ef4444]/10 border-b border-[#242f49] px-3.5 py-2 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-[#ef4444] animate-pulse" />
                <span className="text-xs font-bold text-slate-200 uppercase font-mono">
                  {conflict.ticker}: {conflict.metric}
                </span>
              </div>
              <span className="bg-[#ef4444]/15 text-[#ef4444] px-1.5 py-0.5 rounded text-[8px] font-mono font-bold border border-[#ef4444]/25">
                DISCREPANCY DETECTED
              </span>
            </div>

            {/* Mismatched Sources */}
            <div className="p-3.5 space-y-2 border-b border-[#242f49] bg-[#0b0f17]/60">
              <div className="text-[9px] uppercase tracking-wider text-slate-500 font-semibold mb-1">
                Comparing Source Inputs:
              </div>
              <div className="grid grid-cols-1 gap-2">
                {conflict.values.map((v, vidx) => {
                  const isSec = v.tier.includes("Tier 1") || v.tier.includes("Tier 2");
                  return (
                    <div 
                      key={vidx}
                      className="flex items-center justify-between p-2 rounded bg-[#121824] border border-[#242f49] text-[10px] font-mono"
                    >
                      <div className="flex items-center gap-2">
                        <span className={`w-1.5 h-1.5 rounded-full ${isSec ? 'bg-[#10b981]' : 'bg-[#f59e0b]'}`} />
                        <span className="text-slate-300 font-semibold">{v.source}</span>
                        <span className={`px-1.5 py-0.2 rounded text-[8px] ${
                          isSec ? 'bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/25' : 'bg-[#f59e0b]/10 text-[#f59e0b] border border-[#f59e0b]/25'
                        }`}>
                          {v.tier}
                        </span>
                      </div>
                      <div className="text-white font-bold">{v.value}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Resolution Block */}
            <div className="p-3.5 bg-[#10b981]/5 space-y-2 text-[10px] font-mono">
              <div className="flex items-center justify-between border-b border-[#10b981]/20 pb-1.5">
                <div className="flex items-center gap-1 text-[#10b981] font-bold">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>RESOLUTION: SUCCESS</span>
                </div>
                <div className="text-slate-400">
                  Confidence Score: <span className="text-[#10b981] font-bold">{conflict.resolution.confidence}</span>
                </div>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-slate-400">Selected Value:</span>
                <span className="text-white font-bold bg-[#10b981]/15 px-2 py-0.5 rounded border border-[#10b981]/25 text-xs">
                  {conflict.resolution.selected}
                </span>
              </div>
              <div className="text-slate-400 leading-normal bg-[#0b0f17] border border-[#242f49] p-2 rounded">
                <strong className="text-[#10b981]">Action:</strong> {conflict.resolution.action}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
