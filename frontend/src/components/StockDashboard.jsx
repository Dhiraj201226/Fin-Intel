import React from 'react';
import { DollarSign, Landmark, Percent, Layers, BarChart2 } from 'lucide-react';

export default function StockDashboard({ stock }) {
  if (!stock) return null;

  // Generate SVG coordinates for a simple beautiful stock chart based on symbol
  const getChartPoints = (symbol) => {
    const charts = {
      AAPL: "10,90 40,75 70,80 100,50 130,45 160,35 190,20 220,15 250,25 280,10",
      TSLA: "10,20 40,35 70,40 100,60 130,75 160,85 190,70 220,95 250,80 280,90",
      MSFT: "10,70 40,75 70,60 100,55 130,40 160,45 190,30 220,25 250,15 280,12"
    };
    return charts[symbol] || "10,50 280,50";
  };

  const isUp = !stock.change.includes('-');

  return (
    <div className="glass-panel p-5 flex flex-col gap-4 min-h-0 overflow-y-auto">
      {/* Header Info */}
      <div className="flex justify-between items-center border-b border-[#242f49] pb-3">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide">{stock.name}</h3>
          <span className="font-mono text-[10px] text-slate-500">{stock.sector} | {stock.industry}</span>
        </div>
        <div className="text-right">
          <div className="font-mono font-bold text-sm text-white">{stock.price}</div>
          <div className={`font-mono text-[10px] font-bold ${isUp ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
            {stock.change}
          </div>
        </div>
      </div>

      {/* Grid Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div className="bg-[#0b0f17] border border-[#242f49] rounded p-2.5 font-mono text-[10px]">
          <div className="flex items-center gap-1.5 text-slate-500 mb-1">
            <DollarSign className="h-3.5 w-3.5" />
            <span>MARKET CAP</span>
          </div>
          <div className="text-slate-200 font-bold">{stock.marketCap}</div>
        </div>
        <div className="bg-[#0b0f17] border border-[#242f49] rounded p-2.5 font-mono text-[10px]">
          <div className="flex items-center gap-1.5 text-slate-500 mb-1">
            <BarChart2 className="h-3.5 w-3.5" />
            <span>P/E RATIO</span>
          </div>
          <div className="text-slate-200 font-bold">{stock.peRatio}</div>
        </div>
        <div className="bg-[#0b0f17] border border-[#242f49] rounded p-2.5 font-mono text-[10px]">
          <div className="flex items-center gap-1.5 text-slate-500 mb-1">
            <Percent className="h-3.5 w-3.5" />
            <span>DIV YIELD</span>
          </div>
          <div className="text-slate-200 font-bold">{stock.dividendYield}</div>
        </div>
        <div className="bg-[#0b0f17] border border-[#242f49] rounded p-2.5 font-mono text-[10px]">
          <div className="flex items-center gap-1.5 text-slate-500 mb-1">
            <Layers className="h-3.5 w-3.5" />
            <span>BETA</span>
          </div>
          <div className="text-slate-200 font-bold">{stock.beta}</div>
        </div>
      </div>

      {/* Dynamic Mini SVG Chart */}
      <div className="bg-[#0b0f17]/80 border border-[#242f49] rounded p-3 space-y-2">
        <div className="flex justify-between items-center text-[9px] uppercase tracking-wider text-slate-500 font-mono font-bold">
          <span>Price Action Trend (Simulated)</span>
          <span className={isUp ? 'text-[#10b981]' : 'text-[#ef4444]'}>
            {isUp ? '📈 Bullish Momentum' : '📉 Bearish Pressure'}
          </span>
        </div>
        <div className="h-28 relative">
          <svg className="w-full h-full overflow-visible" viewBox="0 0 290 100" preserveAspectRatio="none">
            {/* Chart Gradient */}
            <defs>
              <linearGradient id={`gradient-${stock.symbol}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={isUp ? "#10b981" : "#ef4444"} stopOpacity="0.15" />
                <stop offset="100%" stopColor={isUp ? "#10b981" : "#ef4444"} stopOpacity="0.0" />
              </linearGradient>
            </defs>
            {/* Grid lines */}
            <line x1="0" y1="25" x2="290" y2="25" stroke="#1c263c" strokeDasharray="3" strokeWidth="0.5" />
            <line x1="0" y1="50" x2="290" y2="50" stroke="#1c263c" strokeDasharray="3" strokeWidth="0.5" />
            <line x1="0" y1="75" x2="290" y2="75" stroke="#1c263c" strokeDasharray="3" strokeWidth="0.5" />

            {/* Sparkline Area */}
            <path
              d={`M 10,100 L ${getChartPoints(stock.symbol)} L 280,100 Z`}
              fill={`url(#gradient-${stock.symbol})`}
              stroke="none"
            />
            {/* Sparkline */}
            <polyline
              fill="none"
              stroke={isUp ? "#10b981" : "#ef4444"}
              strokeWidth="2.5"
              points={getChartPoints(stock.symbol)}
            />
          </svg>
        </div>
      </div>

      {/* Historical Financials Table */}
      <div className="space-y-2 font-mono text-[10px]">
        <span className="text-slate-500 uppercase font-bold tracking-wider block">Historical Financial Statements</span>
        <div className="border border-[#242f49] rounded overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#121824] border-b border-[#242f49] text-slate-400 font-bold">
                <th className="p-2">Metric</th>
                {stock.financials.years.map(y => (
                  <th key={y} className="p-2 text-right">{y}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-[#242f49]/40 hover:bg-[#121824]/20 text-slate-300">
                <td className="p-2">Revenue</td>
                {stock.financials.revenue.map((r, i) => (
                  <td key={i} className="p-2 text-right text-white font-semibold">{r}</td>
                ))}
              </tr>
              <tr className="border-b border-[#242f49]/40 hover:bg-[#121824]/20 text-slate-300">
                <td className="p-2">Net Income</td>
                {stock.financials.netIncome.map((n, i) => (
                  <td key={i} className="p-2 text-right">{n}</td>
                ))}
              </tr>
              <tr className="hover:bg-[#121824]/20 text-slate-300">
                <td className="p-2">Free Cash Flow</td>
                {stock.financials.freeCashFlow.map((f, i) => (
                  <td key={i} className="p-2 text-right">{f}</td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Competitors List */}
      <div className="space-y-2 font-mono text-[10px]">
        <span className="text-slate-500 uppercase font-bold tracking-wider block">Relative Valuation Matrices</span>
        <div className="border border-[#242f49] rounded overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#121824] border-b border-[#242f49] text-slate-400 font-bold">
                <th className="p-2">Peer Ticker</th>
                <th className="p-2">Company Name</th>
                <th className="p-2 text-right">Market Cap</th>
                <th className="p-2 text-right">P/E</th>
              </tr>
            </thead>
            <tbody>
              {stock.competitors.map((peer, i) => (
                <tr key={i} className="border-b border-[#242f49]/40 hover:bg-[#121824]/20 text-slate-300">
                  <td className="p-2 text-[#3b82f6] font-bold">{peer.symbol}</td>
                  <td className="p-2 truncate max-w-[80px]">{peer.name}</td>
                  <td className="p-2 text-right">{peer.marketCap}</td>
                  <td className="p-2 text-right font-bold text-white">{peer.pe}x</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
