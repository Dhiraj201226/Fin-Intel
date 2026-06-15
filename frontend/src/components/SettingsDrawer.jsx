import React from 'react';
import { X, Key, Settings, Cpu, ShieldAlert, Database } from 'lucide-react';

export default function SettingsDrawer({ isOpen, onClose, settings, onSave }) {
  if (!isOpen) return null;

  const handleChange = (key, value) => {
    onSave({ ...settings, [key]: value });
  };

  return (
    <div className="fixed inset-y-0 right-0 w-80 bg-[#121824] border-l border-[#242f49] shadow-2xl z-50 p-6 flex flex-col transition-all duration-300">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-2 text-white font-semibold">
          <Settings className="h-5 w-5 text-[#10b981]" />
          <span>Agent Settings</span>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-white">
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-6 pr-1">
        {/* Model Selection */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            LLM Core Provider
          </label>
            <div className="flex gap-2">
              <button
                onClick={() => handleChange('provider', 'gemini')}
                className={`flex-1 py-2 px-3 rounded-lg border transition-colors text-xs font-medium ${
                  settings.provider === 'gemini' 
                    ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400' 
                    : 'border-slate-700 text-slate-400 hover:border-slate-600'
                }`}
              >
                Gemini
              </button>
              <button
                onClick={() => handleChange('provider', 'groq')}
                className={`flex-1 py-2 px-3 rounded-lg border transition-colors text-xs font-medium ${
                  settings.provider === 'groq' 
                    ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400' 
                    : 'border-slate-700 text-slate-400 hover:border-slate-600'
                }`}
              >
                Groq
              </button>
              <button
                onClick={() => handleChange('provider', 'ollama')}
                className={`flex-1 py-2 px-3 rounded-lg border transition-colors text-xs font-medium ${
                  settings.provider === 'ollama' 
                    ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400' 
                    : 'border-slate-700 text-slate-400 hover:border-slate-600'
                }`}
              >
                Ollama
              </button>
            </div>
        </div>

        {/* API Key Input */}
        {settings.provider !== 'ollama' && (
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              <Key className="h-3.5 w-3.5" />
              <span>{settings.provider === 'gemini' ? 'Gemini API Key' : (settings.provider === 'groq' ? 'Groq API Key' : 'OpenAI API Key')}</span>
            </label>
            <input
              type="password"
              placeholder={settings.provider === 'gemini' ? 'AIzaSy...' : (settings.provider === 'groq' ? 'gsk_...' : 'sk-proj-...')}
              value={settings.provider === 'gemini' ? settings.geminiKey : (settings.provider === 'groq' ? settings.groqKey : settings.openaiKey)}
              onChange={(e) =>
                handleChange(
                  settings.provider === 'gemini' ? 'geminiKey' : (settings.provider === 'groq' ? 'groqKey' : 'openaiKey'),
                  e.target.value
                )
              }
              className="w-full bg-[#0b0f17] border border-[#242f49] rounded p-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-[#10b981]"
            />
            <span className="text-[10px] text-slate-500 block">
              Keys are stored locally in your browser and are never uploaded.
            </span>
          </div>
        )}

        {/* Max Steps */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Max ReAct Thought Steps ({settings.maxSteps})
          </label>
          <input
            type="range"
            min="3"
            max="15"
            value={settings.maxSteps}
            onChange={(e) => handleChange('maxSteps', parseInt(e.target.value))}
            className="w-full accent-[#10b981]"
          />
          <div className="flex justify-between text-[10px] text-slate-500">
            <span>3 Steps (Fast)</span>
            <span>15 Steps (Deep)</span>
          </div>
        </div>

        {/* Vector DB config */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <Database className="h-3.5 w-3.5 text-[#8b5cf6]" />
            <span>Vector Store Backend</span>
          </label>
          <select
            value={settings.vectorStore}
            onChange={(e) => handleChange('vectorStore', e.target.value)}
            className="w-full bg-[#0b0f17] border border-[#242f49] rounded p-2 text-xs text-white focus:outline-none focus:border-[#10b981]"
          >
            <option value="chromadb">ChromaDB (Local Server)</option>
            <option value="faiss">FAISS Index (In-Memory File)</option>
          </select>
        </div>

        {/* Temperature */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Agent Risk Tolerance / Temp ({settings.temperature})
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={settings.temperature}
            onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
            className="w-full accent-[#10b981]"
          />
          <div className="flex justify-between text-[10px] text-slate-500">
            <span>Conservative (0.0)</span>
            <span>Speculative (1.0)</span>
          </div>
        </div>

        {/* Security Warning */}
        <div className="p-3 bg-[#ef4444]/5 border border-[#ef4444]/20 rounded flex gap-2">
          <ShieldAlert className="h-4 w-4 text-[#ef4444] shrink-0 mt-0.5" />
          <div className="text-[10px] text-slate-400">
            <strong className="text-white">Compliance Notice:</strong> Financial advisories generated by this agent are for educational research demonstration purposes only.
          </div>
        </div>
      </div>

      <div className="mt-6 border-t border-[#242f49] pt-4">
        <button
          onClick={onClose}
          className="w-full btn-primary text-center justify-center text-xs"
        >
          Apply Config
        </button>
      </div>
    </div>
  );
}
