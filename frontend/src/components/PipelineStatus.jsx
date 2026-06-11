import React from 'react';
import { Search, ChevronRight, FileText, Globe, CheckCircle } from 'lucide-react';

export default function PipelineStatus({ activeTier }) {
  const tiers = [
    { id: 1, label: "SEC Vector DB", desc: "Audited Ground Truth", icon: FileText, color: "text-[#10b981]", bg: "bg-[#10b981]/15" },
    { id: 2, label: "Web Search", desc: "Live Internet Fallback", icon: Globe, color: "text-[#3b82f6]", bg: "bg-[#3b82f6]/15" }
  ];

  return (
    <div className="glass-panel p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 uppercase tracking-wider">
          <Search className="h-4 w-4 text-[#10b981]" />
          <span>Hierarchy Resource Retrieval Track</span>
        </div>
        <div className="text-[10px] text-slate-500 font-mono">
          Hierarchy: SEC DB &gt; Web Search
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 items-center">
        {tiers.map((t, idx) => {
          const isActive = activeTier === t.id;
          const isCompleted = activeTier > t.id;
          const isPending = activeTier < t.id;

          let borderClass = "border-[#242f49]";
          let glowClass = "";
          let bgClass = "bg-[#0b0f17]/50";

          if (isActive) {
            borderClass = t.id === 1 ? "border-[#10b981]" : "border-[#3b82f6]";
            glowClass = t.id === 1 ? "shadow-[0_0_10px_rgba(16,185,129,0.2)]" : "shadow-[0_0_10px_rgba(59,130,246,0.2)]";
            bgClass = t.bg;
          } else if (isCompleted) {
            borderClass = "border-[#10b981]/50";
            bgClass = "bg-[#10b981]/5";
          }

          const IconComponent = t.icon;

          return (
            <div key={t.id} className="flex items-center gap-2">
              <div className={`flex-1 rounded p-2.5 border transition-all duration-300 flex items-center gap-2.5 ${borderClass} ${glowClass} ${bgClass}`}>
                <div className={`p-1.5 rounded ${isActive ? 'bg-[#0b0f17]/60' : 'bg-transparent'}`}>
                  <IconComponent className={`h-5 w-5 ${isActive || isCompleted ? t.color : 'text-slate-600'}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className={`text-sm font-semibold truncate ${isActive ? 'text-white' : isCompleted ? 'text-[#10b981]' : 'text-slate-500'}`}>
                      {t.label}
                    </span>
                    {isCompleted && (
                      <CheckCircle className="h-4 w-4 text-[#10b981] shrink-0" />
                    )}
                  </div>
                  <span className="text-xs text-slate-500 block truncate">{t.desc}</span>
                </div>
              </div>
              {idx < 1 && (
                <ChevronRight className="h-5 w-5 text-slate-600 shrink-0 mx-2" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
