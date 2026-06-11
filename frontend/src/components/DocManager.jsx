import React, { useState } from 'react';
import { UploadCloud, FileText, Search, Plus, CheckCircle, RefreshCw } from 'lucide-react';

export default function DocManager({ documents, onUpload, onSecFetch, uploadLoading }) {
  const [ticker, setTicker] = useState('');
  const [uploadFile, setUploadFile] = useState(null);

  const handleUploadSubmit = (e) => {
    e.preventDefault();
    if (!uploadFile) return;
    onUpload(uploadFile);
    setUploadFile(null);
  };

  const handleSecSubmit = (e) => {
    e.preventDefault();
    if (!ticker.trim()) return;
    onSecFetch(ticker.trim().toUpperCase());
    setTicker('');
  };

  return (
    <div className="glass-panel p-5 flex flex-col gap-5 min-h-0 overflow-y-auto">
      {/* Section Title */}
      <div>
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-1">
          Data Ingestion & Filings Portal
        </h3>
        <p className="text-[10px] text-slate-500">
          Upload custom materials or pull corporate regulatory reports into the ChromaDB vector database.
        </p>
      </div>



      {/* 1. Drag & Drop File Upload */}
      <form onSubmit={handleUploadSubmit} className="space-y-3 border-b border-[#242f49] pb-4">
        <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
          Upload Verified SEC Filings (PDF)
        </label>
        
        <div className="border border-dashed border-[#242f49] hover:border-[#10b981] rounded p-4 text-center cursor-pointer transition-colors bg-[#0b0f17]/40 relative">
          <input
            type="file"
            accept=".pdf,.txt,.docx"
            onChange={(e) => setUploadFile(e.target.files[0])}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          <UploadCloud className="h-6 w-6 text-slate-500 mx-auto mb-2" />
          <span className="text-[10px] text-slate-400 block font-semibold">
            {uploadFile ? uploadFile.name : "Drag files here or click to browse"}
          </span>
          <span className="text-[9px] text-slate-500 block mt-1">
            Supports PDF, TXT, DOCX (Max 25MB)
          </span>
        </div>

        {uploadFile && (
          <button
            type="submit"
            className="w-full btn-secondary text-xs text-center justify-center border-[#10b981]/50 text-[#10b981] hover:bg-[#10b981]/5"
            disabled={uploadLoading}
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Process & Index File</span>
          </button>
        )}
      </form>

      {/* 2. Ingested Documents List */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex justify-between items-center mb-2">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Ingested Vectors ({documents.length})
          </span>
          {uploadLoading && (
            <span className="flex items-center gap-1 text-[9px] text-[#10b981] font-semibold animate-pulse">
              <RefreshCw className="h-2.5 w-2.5 animate-spin" />
              <span>Indexing...</span>
            </span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
          {documents.map((doc, idx) => (
            <div
              key={idx}
              className="bg-[#121824] border border-[#242f49] rounded p-2 flex items-start gap-2.5"
            >
              <FileText className="h-4 w-4 text-[#10b981] shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0 font-mono text-[10px]">
                <div className="flex items-center justify-between">
                  <span className="text-slate-200 font-bold truncate block">{doc.name}</span>
                  <CheckCircle className="h-3 w-3 text-[#10b981] shrink-0" />
                </div>
                <div className="flex justify-between text-[9px] text-slate-500 mt-1">
                  <span>Size: {doc.size}</span>
                  <span>Chunks: {doc.chunks}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
