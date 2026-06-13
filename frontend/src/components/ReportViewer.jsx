import React, { useState } from 'react';
import { FileCheck, TrendingUp, TrendingDown } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ReportViewer({ report }) {
  const [activeTab, setActiveTab] = useState('summary');

  if (!report) {
    return (
      <div className="glass-panel flex-1 flex flex-col items-center justify-center text-center p-8">
        <FileCheck className="h-12 w-12 text-[#242f49] mb-4" />
        <h3 className="text-sm font-semibold text-slate-400 mb-1">Financial Report Panel</h3>
        <p className="text-xs text-slate-600 max-w-xs leading-relaxed">
          Select a stock or type a query in the console. The finalized investment advisor report will compile here.
        </p>
      </div>
    );
  }

  // If report is a simple string (from live LLM), render it directly
  if (typeof report === 'string') {
    return (
      <div className="glass-panel flex-1 flex flex-col min-h-0 overflow-hidden">
        <div className="bg-[#121824] px-4 py-4 border-b border-[#242f49] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-white tracking-wide uppercase">AI Research Report</h2>
            <span className="bg-[#10b981]/15 text-[#10b981] px-1.5 py-0.5 rounded font-mono text-[10px] border border-[#10b981]/25">
              LIVE GENERATION
            </span>
          </div>
        </div>
        <div className="flex-1 p-5 overflow-y-auto bg-[#0b0f17]">
          <div className="markdown-body text-xs text-slate-300 leading-relaxed font-sans">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {report}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    );
  }

  const { ticker, companyName, recommendation, targetPrice, currentPrice, upside, confidenceScore, sections } = report;

  const tabs = [
    { id: 'summary', label: 'Summary' },
    { id: 'overview', label: 'Company Overview' },
    { id: 'financials', label: 'Financials' },
    { id: 'valuation', label: 'Valuation' },
    { id: 'risks', label: 'Risks' },
    { id: 'recommendation', label: 'Consensus Rec' }
  ];

  // Regex to match citation brackets like [1] or [2]
  const renderContentWithCitations = (text) => {
    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, idx) => {
      const match = part.match(/^\[(\d+)\]$/);
      if (match) {
        return (
          <span 
            key={idx}
            className="inline-flex items-center justify-center font-mono font-bold text-[10px] text-[#10b981] bg-[#10b981]/15 px-1.5 py-0.5 rounded mx-0.5 border border-[#10b981]/20 select-none"
          >
            {part}
          </span>
        );
      }
      return <span key={idx}>{part}</span>;
    });
  };

  const isBuy = recommendation === 'BUY';

  return (
    <div className="glass-panel flex-1 flex flex-col min-h-0 overflow-hidden">
      {/* Report Header Card */}
      <div className="bg-[#121824] px-4 py-4 border-b border-[#242f49] flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-white tracking-wide uppercase">{companyName}</h2>
            <span className="bg-[#242f49] text-slate-300 px-1.5 py-0.5 rounded font-mono text-[10px]">
              {ticker}
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span>Market Price: <strong className="text-white">{currentPrice}</strong></span>
            <span>Target Value: <strong className="text-[#10b981]">{targetPrice}</strong></span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Target details */}
          <div className="text-right">
            <div className={`text-xs font-bold px-2.5 py-1 rounded inline-flex items-center gap-1 font-mono ${
              isBuy ? 'bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/25' : 'bg-[#ef4444]/15 text-[#ef4444] border border-[#ef4444]/25'
            }`}>
              {isBuy ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
              <span>{recommendation} ({upside})</span>
            </div>
            <div className="text-[9px] text-slate-500 mt-1 font-mono">
              Confidence Score: {confidenceScore}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-[#0b0f17] border-b border-[#242f49] px-2 flex gap-1 overflow-x-auto select-none shrink-0">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`px-3 py-2 text-[11px] font-semibold text-slate-400 hover:text-white border-b-2 border-transparent transition-all shrink-0 ${
              activeTab === t.id ? 'tab-active' : ''
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Report Content */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Main Text Panel */}
        <div className="flex-1 p-5 overflow-y-auto space-y-4">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest border-b border-[#242f49] pb-1.5 flex items-center justify-between">
            <span>{sections[activeTab].title}</span>
            <span className="text-[10px] text-slate-500 font-mono capitalize">Section {tabs.findIndex(t => t.id === activeTab) + 1} of 6</span>
          </h3>

          <div className="text-xs text-slate-300 leading-relaxed space-y-3 font-sans">
            {renderContentWithCitations(sections[activeTab].content)}
          </div>
        </div>
      </div>
    </div>
  );
}
