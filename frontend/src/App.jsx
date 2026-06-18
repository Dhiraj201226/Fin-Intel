import React, { useState, useEffect } from 'react';
import { 
  Terminal as TerminalIcon, 
  GitMerge, 
  Database, 
  FileCode, 
  Settings, 
  Activity, 
  ChevronRight, 
  Lock, 
  Unlock,
  ShieldCheck,
  TrendingUp,
  Menu,
  X
} from 'lucide-react';

import ChatConsole from './components/ChatConsole.jsx';
import PipelineStatus from './components/PipelineStatus.jsx';
import ReportViewer from './components/ReportViewer.jsx';
import ChartVault from './components/ChartVault.jsx';
import MemoryVault from './components/MemoryVault.jsx';
import SettingsDrawer from './components/SettingsDrawer.jsx';

import { 
  mockStocks, 
  mockReActLogs, 
  mockReports, 
  mockEpisodicMemory, 
  mockVectorDB 
} from './mockData';

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:7860";

export default function App() {
  // Navigation tab states: 'terminal' | 'memory' | 'charts'
  const [activeTab, setActiveTab] = useState('terminal');
  
  // Mobile sidebar state
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  
  // Settings Drawer state
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settings, setSettings] = useState({
    provider: 'gemini',
    geminiKey: localStorage.getItem('ara1_gemini_key') || '',
    openaiKey: localStorage.getItem('ara1_openai_key') || '',
    groqKey: localStorage.getItem('ara1_groq_key') || '',
    maxSteps: 8,
    vectorStore: 'chromadb',
    temperature: 0.3
  });

  // Save keys to localStorage
  useEffect(() => {
    localStorage.setItem('ara1_gemini_key', settings.geminiKey);
    localStorage.setItem('ara1_openai_key', settings.openaiKey);
    localStorage.setItem('ara1_groq_key', settings.groqKey);
  }, [settings.geminiKey, settings.openaiKey, settings.groqKey]);

  // General App states
  const [sessionId, setSessionId] = useState(`sess_${Math.random().toString(36).substring(2, 9)}`);
  const [selectedStock, setSelectedStock] = useState('AAPL');
  const [query, setQuery] = useState('');
  const [logs, setLogs] = useState([]);
  const [activeTier, setActiveTier] = useState(0); // 0 = Idle, 1 = SEC, 2 = Web, 3 = News, 4 = Media
  const [loading, setLoading] = useState(false);
  const [activeReport, setActiveReport] = useState(null);
  const [rateLimitModalOpen, setRateLimitModalOpen] = useState(false);

  // Database lists populated from live backend
  const [episodicMemory, setEpisodicMemory] = useState([]);
  const [vectorDB, setVectorDB] = useState([]);

  // Fetch live memory data on mount
  useEffect(() => {
    const fetchMemoryData = async () => {
      try {
        const epRes = await fetch(`${API_BASE_URL}/api/episodes`, { headers: { "X-API-Key": "test_key" } });
        if (epRes.ok) {
          const epData = await epRes.json();
          setEpisodicMemory(epData);
        }

        const vecRes = await fetch(`${API_BASE_URL}/api/vectors`, { headers: { "X-API-Key": "test_key" } });
        if (vecRes.ok) {
          const vecData = await vecRes.json();
          setVectorDB(vecData);
        }
      } catch (e) {
        console.error("Failed to fetch memory vault data", e);
      }
    };
    fetchMemoryData();
  }, []);

  // Suggested prompts
  const suggestedQueries = [
    "Should I buy Apple (AAPL) stock right now?",
    "Analyze Tesla (TSLA) automotive gross margins and valuation risks",
    "Evaluate Microsoft (MSFT) OpenAI partnership and cloud growth drivers",
    "Analyze Goldman Sachs (GS) investment banking rebound and capital targets"
  ];

  // Helper to extract ticker from query
  const getTickerFromQuery = (q) => {
    // Look for tickers with .NS or .BO (e.g. RELIANCE.NS)
    const indianMatch = q.match(/\b([A-Z]+(\.NS|\.BO))\b/);
    if (indianMatch) {
      return indianMatch[1];
    }

    // Look for a standard 1-5 letter uppercase ticker symbol in parentheses or standing alone
    // Find all 1-10 letter all-caps words, optionally ending in .NS or .BO
    const matches = q.match(/\b([A-Z]{1,10}(?:\.NS|\.BO)?)\b/g);
    if (matches) {
      const validOneLetterTickers = ["F", "C", "V", "O", "T", "X"];
      const exclusions = ["I", "ME", "MY", "WHAT", "HOW", "WHY", "IS", "THE", "A", "AN", "AND", "OR", "IF", "IT", "ABOUT", "BUY", "SELL", "STOCK", "STOCKS", "ON", "FOR", "IN", "TO", "OF", "TATA", "STEEL", "POWER", "MOTORS", "BANK", "INDIA", "CORP", "LTD", "SHOULD", "NOW", "RIGHT"];
      for (const match of matches) {
        if (!exclusions.includes(match)) {
          if (match.length === 1 && !validOneLetterTickers.includes(match)) continue;
          return match;
        }
      }
    }
    
    // Fallbacks if no explicit ticker is capitalized
    const uppercaseQuery = q.toUpperCase();
    if (uppercaseQuery.includes('APPLE')) return 'AAPL';
    if (uppercaseQuery.includes('TESLA')) return 'TSLA';
    if (uppercaseQuery.includes('MICROSOFT')) return 'MSFT';
    if (uppercaseQuery.includes('GOLDMAN')) return 'GS';
    if (uppercaseQuery.includes('NVIDIA')) return 'NVDA';
    if (uppercaseQuery.includes('META')) return 'META';
    if (uppercaseQuery.includes('AMAZON')) return 'AMZN';
    
    return null; // Let backend figure it out or fail gracefully
  };

  // Execute Agent Query (Tries live API first, falls back to client-side simulation)
  const handleExecute = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setLogs(prev => [...prev, { type: 'user', text: query }]);
    setActiveReport(null);
    setActiveTier(0);

    const ticker = getTickerFromQuery(query);
    setSelectedStock(ticker);

    const providerKey = settings.provider === 'gemini' ? settings.geminiKey : (settings.provider === 'groq' ? settings.groqKey : settings.openaiKey);

    try {
      // 1. Attempt connection to live FastAPI backend
      const response = await fetch(`${API_BASE_URL}/api/research`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-llm-provider": settings.provider,
          "x-llm-api-key": providerKey || "",
          "x-llm-max-steps": settings.maxSteps.toString(),
          "x-llm-temperature": settings.temperature.toString(),
          "x-session-id": sessionId,
          "X-API-Key": "test_key"
        },
        body: JSON.stringify({ query: query, ticker: ticker, session_id: sessionId })
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();
      if (data.logs && data.logs.length > 0) {
        // Stream the real logs returned from backend
        let currentLogIndex = 0;
        const streamNextLog = () => {
          if (currentLogIndex < data.logs.length) {
            const nextLog = data.logs[currentLogIndex];
            setLogs(prev => [...prev, nextLog]);

            if (nextLog.type === 'action') {
              if (nextLog.text.includes('vector_store')) {
                setActiveTier(1);
              } else if (nextLog.text.includes('yfinance_api')) {
                setActiveTier(2);
              }
            } else if (nextLog.type === 'rate_limit_error') {
              setRateLimitModalOpen(true);
            }

            currentLogIndex++;
            const delay = nextLog.type === 'thought' ? 1000 : 1500;
            setTimeout(streamNextLog, delay);
          } else {
            setLoading(false);
            setActiveReport(data.report);
            setActiveTier(0);
            
            // Add to Episodic Memory List
            const wasEarlyStopped = data.logs.some(l => l.text && l.text.toLowerCase().includes("early"));
            
            // Build chat_log so UI can load it later
            const chatLog = [
              { role: "User", text: query },
              { role: "Agent", text: data.report }
            ];
            
            const newEpisode = {
              id: `EP-${Math.floor(1000 + Math.random() * 9000)}`,
              session_id: sessionId,
              timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
              query: query,
              status: wasEarlyStopped ? "EARLY_STOPPED" : "SUCCESS",
              tools_used: ["vector_store", "yfinance_api", "financial_engine"],
              failures: "None",
              recovery: "N/A",
              strategy: `2-Tier hierarchy: ${wasEarlyStopped ? "early stopped at Stage 1" : "completed all stages"} for query.`,
              chat_log: chatLog
            };
            setEpisodicMemory(prev => [newEpisode, ...prev]);
          }
        };
        setTimeout(streamNextLog, 500);
        return;
      } else {
        console.warn("Backend returned empty logs array!");
        setLoading(false);
        setLogs([{
          type: 'error',
          text: `Error: The backend processed the request but returned no logs.`
        }]);
      }
    } catch (err) {
      console.error("Backend API Error:", err.message);
      setLogs([{
        type: 'error',
        text: `Error: Unable to connect to ARA-1 backend. Please ensure the backend is running. Details: ${err.message}`
      }]);
      setLoading(false);
    }
  };

  const handleResetSession = () => {
    setSessionId(`sess_${Math.random().toString(36).substring(2, 9)}`);
    setLogs([]);
    setActiveReport(null);
    setActiveTier(0);
    setQuery('');
  };

  const handleFileUpload = async (file) => {
    if (!file) return;
    setLoading(true);
    setLogs(prev => [...prev, { type: 'user', text: `Uploaded Document: ${file.name}` }]);
    
    const formData = new FormData();
    formData.append("file", file);

    const providerKey = settings.provider === 'gemini' ? settings.geminiKey : (settings.provider === 'groq' ? settings.groqKey : settings.openaiKey);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: "POST",
        headers: {
          "x-llm-provider": settings.provider,
          "x-llm-api-key": providerKey || "",
          "x-session-id": sessionId,
          "X-API-Key": "test_key"
        },
        body: formData
      });

      if (!response.ok) {
        let errorMsg = `Server returned ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) errorMsg = errData.detail;
        } catch(e) {}
        throw new Error(errorMsg);
      }

      const data = await response.json();
      setLogs(prev => [...prev, { type: 'observation', text: `System: ${data.message}` }]);
    } catch (err) {
      setLogs(prev => [...prev, { type: 'error', text: `Upload Error: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  const activeStockData = mockStocks[selectedStock];
  
  // Compute unique sessions for the history sidebar
  const uniqueSessions = [];
  const seenSessions = new Set();
  episodicMemory.forEach(ep => {
    if (ep.session_id && !seenSessions.has(ep.session_id)) {
      seenSessions.add(ep.session_id);
      uniqueSessions.push(ep);
    }
  });

  const loadSession = (targetSessionId) => {
    setSessionId(targetSessionId);
    setActiveTab('terminal');
    
    // Find all episodes for this session to reconstruct logs
    const sessionEps = episodicMemory.filter(ep => ep.session_id === targetSessionId).reverse();
    
    // Construct basic logs from chat history
    let reconstructedLogs = [];
    let lastReport = null;
    
    sessionEps.forEach(ep => {
      if (ep.chat_log && Array.isArray(ep.chat_log)) {
        ep.chat_log.forEach(turn => {
          if (turn.role === 'User') {
            reconstructedLogs.push({ type: 'user', text: turn.text });
          } else if (turn.role === 'Agent') {
            lastReport = turn.text;
          }
        });
      }
    });
    
    setLogs(reconstructedLogs);
    setActiveReport(lastReport);
    setIsSidebarOpen(false); // Close mobile sidebar
  };

  return (
    <div className="h-screen w-full bg-[#0b0f17] flex flex-col font-sans overflow-hidden">
      
      {/* Top Navigation / Terminal Header Bar */}
      <header className="bg-[#121824] border-b border-[#242f49] px-4 py-3 flex items-center justify-between shrink-0 sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <button 
            className="lg:hidden p-1 text-slate-300 hover:text-white" 
            onClick={() => setIsSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>
          <div className="flex items-center justify-center bg-[#10b981]/15 border border-[#10b981]/30 p-1.5 rounded hidden sm:flex">
            <Activity className="h-5 w-5 text-[#10b981] animate-pulse" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-widest uppercase">
              FinIntel AI Agent
            </h1>
            <span className="text-[9px] text-[#10b981] font-mono tracking-wider flex items-center gap-1.5">
              <span className="status-indicator bg-[#10b981] pulse-green"></span>
              SYSTEM STATUS: CALIBRATED & AUDITED
            </span>
          </div>
        </div>

        {/* Global Stats bar */}
        <div className="hidden lg:flex items-center gap-6 font-mono text-[10px] text-slate-500 border-l border-r border-[#242f49] px-6">
          <div>
            CORE LLM: <span className="text-white font-bold">{settings.provider === 'gemini' ? 'Gemini 2.5 Flash' : (settings.provider === 'ollama' ? 'Local Ollama' : 'GPT-4o')}</span>
          </div>
          <div>
            MARKET DATA: <span className="text-[#10b981] font-bold">Yahoo Finance Active</span>
          </div>
        </div>

        {/* Settings and Info */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 bg-[#0b0f17] border border-[#242f49] rounded px-2.5 py-1 text-[10px] font-semibold text-slate-400">
            {settings.provider === 'gemini' || settings.openaiKey || settings.groqKey ? (
              <>
                <Unlock className="h-3 w-3 text-[#10b981]" />
                <span className="text-slate-300">{settings.provider === 'gemini' ? 'Inbuilt Key Active' : 'Keys Activated'}</span>
              </>
            ) : (
              <>
                <Lock className="h-3 w-3 text-slate-500" />
                <span>Demo Sandbox</span>
              </>
            )}
          </div>
          <button 
            onClick={() => setSettingsOpen(true)}
            className="p-1.5 rounded border border-[#242f49] bg-[#1a2234] hover:bg-[#242f49] text-slate-300 hover:text-white transition-all flex items-center gap-1.5 text-xs font-semibold"
          >
            <Settings className="h-4 w-4" />
            <span>Settings</span>
          </button>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="flex-1 flex flex-col lg:flex-row min-h-0">
        
        {/* Mobile Sidebar Overlay */}
        {isSidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/60 z-40 lg:hidden" 
            onClick={() => setIsSidebarOpen(false)} 
          />
        )}

        {/* Navigation Sidebar Panel */}
        <aside className={`fixed lg:static top-0 left-0 h-full lg:h-auto z-50 w-64 lg:w-56 bg-[#121824] border-r border-[#242f49] p-4 flex flex-col justify-between shrink-0 transition-transform duration-300 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
          <div className="space-y-5">
            {/* Mobile Sidebar Header */}
            <div className="flex items-center justify-between lg:hidden mb-4 pb-4 border-b border-[#242f49]">
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-[#10b981]" />
                <span className="text-white font-bold text-sm">FININTEL</span>
              </div>
              <button onClick={() => setIsSidebarOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Nav Title */}
            <div>
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block mb-2">
                Operational Modules
              </span>
              <div className="flex flex-col gap-1">
                <button
                  onClick={() => setActiveTab('terminal')}
                  className={`w-full text-left py-2 px-3 rounded text-xs font-medium flex items-center gap-2.5 transition-all ${
                    activeTab === 'terminal'
                      ? 'bg-[#10b981]/15 text-[#10b981] border-l-2 border-[#10b981]'
                      : 'text-slate-400 hover:bg-[#1a2234] hover:text-white'
                  }`}
                >
                  <TerminalIcon className="h-4 w-4" />
                  <span>Research Terminal</span>
                </button>
                <button
                  onClick={() => setActiveTab('memory')}
                  className={`w-full text-left py-2 px-3 rounded text-xs font-medium flex items-center gap-2.5 transition-all ${
                    activeTab === 'memory'
                      ? 'bg-[#8b5cf6]/15 text-[#8b5cf6] border-l-2 border-[#8b5cf6]'
                      : 'text-slate-400 hover:bg-[#1a2234] hover:text-white'
                  }`}
                >
                  <Database className="h-4 w-4" />
                  <span>Memory Vault</span>
                </button>
                <button
                  onClick={() => setActiveTab('charts')}
                  className={`w-full text-left py-2 px-3 rounded text-xs font-medium flex items-center gap-2.5 transition-all ${
                    activeTab === 'charts'
                      ? 'bg-[#f59e0b]/15 text-[#f59e0b] border-l-2 border-[#f59e0b]'
                      : 'text-slate-400 hover:bg-[#1a2234] hover:text-white'
                  }`}
                >
                  <FileCode className="h-4 w-4" />
                  <span>Chart Vault</span>
                </button>
              </div>
            </div>

            {/* Quick stock selector */}
            <div className="pt-2 border-t border-[#242f49]">
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block mb-2">
                Active Research Ticker
              </span>
              <div className="grid grid-cols-3 gap-1.5 font-mono text-[10px]">
                {Object.keys(mockStocks).map(sym => (
                  <button
                    key={sym}
                    onClick={() => {
                      setSelectedStock(sym);
                      setActiveReport(mockReports[sym]);
                      setLogs(mockReActLogs[sym]);
                    }}
                    className={`py-1.5 rounded border text-center font-bold transition-all ${
                      selectedStock === sym
                        ? 'border-[#10b981] bg-[#10b981]/10 text-white'
                        : 'border-[#242f49] text-slate-500 hover:border-slate-600'
                    }`}
                  >
                    {sym}
                  </button>
                ))}
              </div>
            </div>

            {/* Chat History */}
            <div className="pt-2 border-t border-[#242f49] max-h-48 overflow-y-auto custom-scrollbar">
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest block mb-2">
                Chat History
              </span>
              <div className="flex flex-col gap-1">
                {uniqueSessions.map((session, idx) => (
                  <button
                    key={session.id}
                    onClick={() => loadSession(session.session_id)}
                    className={`w-full text-left py-1.5 px-2 rounded text-[10px] font-medium truncate transition-all ${
                      sessionId === session.session_id
                        ? 'bg-[#10b981]/15 text-[#10b981] border-l-2 border-[#10b981]'
                        : 'text-slate-400 hover:bg-[#1a2234] hover:text-white border-l-2 border-transparent'
                    }`}
                  >
                    {session.query}
                  </button>
                ))}
                {uniqueSessions.length === 0 && (
                  <span className="text-[10px] text-slate-600 italic">No previous chats.</span>
                )}
              </div>
            </div>
          </div>

          {/* Compliance tag */}
          <div className="p-3 bg-[#0b0f17] border border-[#242f49] rounded space-y-1">
            <div className="flex items-center gap-1.5 text-[9px] font-bold text-slate-300">
              <ShieldCheck className="h-3.5 w-3.5 text-[#10b981]" />
              <span>MARKET COMPLIANT</span>
            </div>
            <p className="text-[8px] text-slate-500 leading-normal">
              Market scrapers and RAG pipelines conform to institutional sandbox security filters.
            </p>
          </div>
        </aside>

        {/* Center Panel - Main display based on navigation */}
        <main className="flex-1 p-4 flex flex-col gap-4 min-w-0 overflow-y-auto">
          
          {/* Tab 1: Terminal & RAG Dashboard */}
          {activeTab === 'terminal' && (
            <>
              {/* Dynamic Hierarchy status visual bar */}
              <PipelineStatus activeTier={activeTier} />

              {/* Inner splits: Left Chat Console, Right Report Viewer */}
              <div className="flex-1 flex flex-col lg:flex-row gap-4 min-h-0">
                <div className="w-full lg:w-1/2 flex flex-col min-h-[500px]">
                  <ChatConsole 
                    logs={logs}
                    loading={loading}
                    query={query}
                    setQuery={setQuery}
                    onSubmit={handleExecute}
                    onReset={handleResetSession}
                    suggestedQueries={suggestedQueries}
                    onFileUpload={handleFileUpload}
                  />
                </div>
                
                <div className="w-full lg:w-1/2 flex flex-col min-h-[500px]">
                  <ReportViewer report={activeReport} />
                </div>
              </div>
            </>
          )}

          {/* Tab 3: Memory Vault Databases */}
          {activeTab === 'memory' && (
            <MemoryVault 
              episodicLogs={episodicMemory} 
              vectorLogs={vectorDB} 
            />
          )}

          {/* Tab 4: Chart Vault */}
          {activeTab === 'charts' && (
            <ChartVault />
          )}

        </main>



      </div>

      {/* Settings Drawer Overlay */}
      <SettingsDrawer 
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        settings={settings}
        onSave={setSettings}
      />

      {/* Rate Limit Recovery Modal */}
      {rateLimitModalOpen && (
        <div className="fixed inset-0 bg-black/60 z-[100] flex items-center justify-center p-4">
           <div className="bg-[#121824] border border-[#ef4444]/40 p-6 rounded shadow-xl w-full max-w-sm flex flex-col gap-4">
             <div className="flex items-center gap-2">
               <ShieldCheck className="h-6 w-6 text-[#ef4444]" />
               <h2 className="text-white font-bold text-lg">API Rate Limit Hit</h2>
             </div>
             <p className="text-slate-400 text-xs">
               The Gemini Free-Tier API quota has been exceeded (429 Error). Would you like to automatically switch to a different LLM provider to continue your research?
             </p>
             <div className="flex flex-col gap-2 mt-2">
               <button 
                 onClick={() => { 
                   setSettings(prev => ({...prev, provider: 'groq'})); 
                   setRateLimitModalOpen(false); 
                   setTimeout(handleExecute, 300);
                 }} 
                 className="w-full bg-[#10b981] hover:bg-[#059669] text-white py-2 rounded text-xs font-bold transition-colors"
               >
                 Switch to Groq & Retry
               </button>
               <button 
                 onClick={() => { 
                   setSettings(prev => ({...prev, provider: 'ollama'})); 
                   setRateLimitModalOpen(false); 
                   setTimeout(handleExecute, 300);
                 }} 
                 className="w-full bg-[#8b5cf6] hover:bg-[#7c3aed] text-white py-2 rounded text-xs font-bold transition-colors"
               >
                 Switch to Local Ollama & Retry
               </button>
               <button 
                 onClick={() => setRateLimitModalOpen(false)} 
                 className="w-full bg-transparent border border-slate-600 hover:border-white text-slate-300 hover:text-white py-2 rounded text-xs font-bold transition-colors mt-2"
               >
                 Cancel
               </button>
             </div>
           </div>
        </div>
      )}
    </div>
  );
}
