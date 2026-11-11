import React, { useState, useEffect } from 'react';
import { X, Copy, Check, Download, FileJson } from 'lucide-react';

export default function TranscriptModal({ session, onClose }) {
  const [copied, setCopied] = useState(false);
  const [showRawJson, setShowRawJson] = useState(false);

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [onClose]);

  if (!session) return null;

  const transcriptJson = JSON.stringify(session, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(transcriptJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([transcriptJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `simulation_transcript_${session.sessionId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl max-h-[85svh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/60">
          <div>
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <FileJson className="w-4 h-4 text-indigo-600" />
              Transcript: <span className="font-mono text-indigo-700">{session.sessionId}</span>
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {session.scenario} · {session.status} · {session.totalMessages} messages
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close transcript"
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Toolbar */}
        <div className="px-4 py-2 bg-white border-b border-slate-100 flex items-center justify-between text-xs">
          <div className="flex gap-1 bg-slate-100 p-0.5 rounded-lg">
            <button
              onClick={() => setShowRawJson(false)}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                !showRawJson ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Formatted Dialog
            </button>
            <button
              onClick={() => setShowRawJson(true)}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                showRawJson ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Raw JSON
            </button>
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleCopy}
              className="px-2.5 py-1 rounded-md bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 flex items-center gap-1.5 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
            <button
              onClick={handleDownload}
              className="px-2.5 py-1 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-1.5 transition-colors font-medium"
            >
              <Download className="w-3.5 h-3.5" />
              Download
            </button>
          </div>
        </div>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto overscroll-contain p-4 text-xs bg-white">
          {showRawJson ? (
            <pre className="text-slate-700 font-mono text-[11px] bg-slate-50 p-3 rounded-lg border border-slate-200 whitespace-pre-wrap break-all">
              {transcriptJson}
            </pre>
          ) : (
            <div className="space-y-3">
              {!session.conversationHistory?.length ? (
                <div className="text-slate-400 text-center py-8">No messages recorded in this session.</div>
              ) : (
                session.conversationHistory.map((m, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl border text-xs leading-relaxed ${
                      m.sender === 'scammer'
                        ? 'bg-slate-50 border-slate-200 text-slate-800'
                        : 'bg-indigo-50/70 border-indigo-200 text-indigo-950'
                    }`}
                  >
                    <div className="font-mono text-[10px] font-semibold mb-1 flex justify-between text-slate-500">
                      <span className={m.sender === 'scammer' ? 'text-slate-700' : 'text-indigo-700'}>
                        {m.sender === 'scammer' ? 'ATTACKER AGENT' : 'HONEYPOT AGENT'}
                      </span>
                      <span>Turn {m.turnNumber || Math.floor(idx / 2) + 1}</span>
                    </div>
                    <div className="whitespace-pre-wrap break-words">{m.text}</div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
