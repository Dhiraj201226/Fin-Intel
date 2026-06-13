import React, { useState, useEffect } from 'react';
import { Image, ExternalLink, RefreshCw, AlertCircle } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:7860";

export default function ChartVault() {
  const [charts, setCharts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCharts = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/charts_list`, {
        headers: { "X-API-Key": "test_key" }
      });
      if (!response.ok) throw new Error("Failed to fetch charts");
      const data = await response.json();
      setCharts(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCharts();
  }, []);

  return (
    <div className="glass-panel flex-1 flex flex-col min-h-0 overflow-hidden">
      {/* Header */}
      <div className="bg-[#121824] px-4 py-3 border-b border-[#242f49] flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <Image className="h-4 w-4 text-[#10b981]" />
          <h2 className="text-sm font-semibold text-white tracking-wider uppercase font-mono">
            Chart Vault
          </h2>
          <span className="bg-[#10b981]/15 text-[#10b981] px-1.5 py-0.5 rounded font-mono text-[9px] font-semibold border border-[#10b981]/25 ml-2">
            LAST 24 HOURS
          </span>
        </div>
        <button 
          onClick={fetchCharts}
          className="flex items-center gap-1.5 p-1.5 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors text-xs font-semibold"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 p-6 overflow-y-auto bg-[#0b0f17]">
        {loading && charts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-3">
            <RefreshCw className="h-8 w-8 animate-spin text-[#242f49]" />
            <p className="text-sm">Scanning temporary storage for generated charts...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-full text-[#ef4444] gap-3">
            <AlertCircle className="h-8 w-8" />
            <p className="text-sm">Error loading charts: {error}</p>
          </div>
        ) : charts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-3">
            <Image className="h-10 w-10 text-[#242f49]" />
            <h3 className="text-sm font-semibold text-slate-400">Vault Empty</h3>
            <p className="text-xs text-slate-600 max-w-sm text-center">
              No technical charts were generated in the last 24 hours. Use the Research Terminal to evaluate a stock.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {charts.map((chart, idx) => (
              <div key={idx} className="bg-[#121824] border border-[#242f49] rounded-lg overflow-hidden group hover:border-[#10b981] transition-colors">
                <div className="p-3 bg-[#1a2234] border-b border-[#242f49] flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-slate-300">
                    {chart.filename.split('_')[0]}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {new Date(chart.timestamp * 1000).toLocaleTimeString()}
                  </span>
                </div>
                <div className="relative aspect-video bg-black/50 p-2 flex items-center justify-center">
                  <img 
                    src={`${API_BASE_URL}${chart.url}`} 
                    alt={chart.filename}
                    className="max-h-full max-w-full object-contain rounded"
                  />
                  <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <a 
                      href={`${API_BASE_URL}${chart.url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-primary py-1.5 px-3 flex items-center gap-2 text-xs"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      <span>View Full Size</span>
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
