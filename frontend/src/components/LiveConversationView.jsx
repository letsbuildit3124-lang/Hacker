import React, { useEffect, useRef } from 'react';
import {
  Play,
  Square,
  RotateCcw,
  FileText,
  AlertCircle,
  Radio,
  Cpu,
  Bot
} from 'lucide-react';

export default function LiveConversationView({
  session,
  messages,
  actionLoading,
  onStart,
  onStop,
  onResume,
  onOpenTranscript
}) {
  const scrollContainerRef = useRef(null);

  // Scoped scroll inside the chat container only (prevents outer viewport jumping)
  useEffect(() => {
    const el = scrollContainerRef.current;
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    }
  }, [messages.length, session?.status]);

  if (!session) {
    return (
      <div className="h-[580px] bg-white border border-slate-200 rounded-xl flex flex-col items-center justify-center p-8 text-center shadow-xs">
        <div className="w-12 h-12 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600 mb-3">
          <Bot className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-slate-900">No Simulation Selected</h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Select an existing session or launch a new simulation to observe the autonomous interaction.
        </p>
      </div>
    );
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'running':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-600 animate-pulse" />
            Simulating
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            Completed
          </span>
        );
      case 'stopped':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
            Stopped
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-rose-50 text-rose-700 border border-rose-200">
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200">
            {status}
          </span>
        );
    }
  };

  const formatTimestamp = (ts) => {
    if (!ts) return '';
    try {
      const d = typeof ts === 'number' ? new Date(ts) : new Date(ts);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return String(ts);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl flex flex-col h-[640px] shadow-xs overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 bg-slate-50/60 shrink-0">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-slate-900">
              {session.sessionId}
            </span>
            {getStatusBadge(session.status)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1 flex flex-wrap items-center gap-x-2">
            <span>Scenario: <strong className="font-medium text-slate-700">{session.scenario}</strong></span>
            <span>·</span>
            <span>Channel: <strong className="font-medium text-slate-700">{session.metadata?.channel || 'SMS'}</strong></span>
            <span>·</span>
            <span>Turns: <strong className="font-mono text-indigo-600">{Math.ceil(messages.length / 2)} / {session.maxTurns}</strong></span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 shrink-0">
          {session.status === 'created' && (
            <button
              onClick={() => onStart(session.sessionId)}
              disabled={actionLoading}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              Start
            </button>
          )}

          {session.status === 'running' && (
            <button
              onClick={() => onStop(session.sessionId)}
              disabled={actionLoading}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              Stop
            </button>
          )}

          {(session.status === 'stopped' || session.status === 'failed' || session.status === 'completed') && (
            <button
              onClick={() => onResume(session.sessionId)}
              disabled={actionLoading}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-1.5 transition-colors disabled:opacity-50"
              title={session.status === 'completed' ? 'Extend by 5 more turns and continue conversation' : 'Resume simulation'}
            >
              <RotateCcw className="w-3.5 h-3.5" />
              {session.status === 'completed' ? 'Continue (+5)' : 'Resume'}
            </button>
          )}

          <button
            onClick={() => onOpenTranscript(session)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 flex items-center gap-1.5 transition-colors"
          >
            <FileText className="w-3.5 h-3.5 text-slate-500" />
            Transcript
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {session.errorMessage && (
        <div className="bg-rose-50 border-b border-rose-200 p-3 px-4 flex items-start gap-2.5 text-xs text-rose-800 shrink-0">
          <AlertCircle className="w-4 h-4 text-rose-600 mt-0.5 shrink-0" />
          <div className="min-w-0">
            <div className="font-semibold">Simulation Interrupted / API Error</div>
            <div className="text-[11px] font-mono text-rose-600 mt-0.5 break-all">{session.errorMessage}</div>
          </div>
        </div>
      )}

      {/* Conversation Stream */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto overscroll-contain p-5 space-y-4 bg-white"
      >
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
            <Radio className="w-8 h-8 opacity-40 mb-2" />
            <div className="font-medium text-slate-600">No messages exchanged yet</div>
            <div className="text-[11px] mt-0.5">Click Start to begin autonomous interaction.</div>
          </div>
        ) : (
          messages.map((msg, index) => {
            const isAttacker = msg.sender === 'scammer';
            const turnNum = msg.turnNumber || Math.floor(index / 2) + 1;

            return (
              <div
                key={index}
                className={`flex flex-col ${isAttacker ? 'items-start' : 'items-end'}`}
              >
                {/* Sender Meta */}
                <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400 mb-1 px-1">
                  {isAttacker ? (
                    <>
                      <Cpu className="w-3 h-3 text-slate-500" />
                      <span className="font-semibold text-slate-700">ATTACKER</span>
                      <span>· Turn {turnNum}</span>
                      <span>· {formatTimestamp(msg.timestamp)}</span>
                    </>
                  ) : (
                    <>
                      <span>{formatTimestamp(msg.timestamp)} ·</span>
                      <span>Turn {turnNum} ·</span>
                      <span className="font-semibold text-indigo-600">HONEYPOT</span>
                      <Bot className="w-3 h-3 text-indigo-600" />
                    </>
                  )}
                </div>

                {/* Minimal Message Bubble */}
                <div
                  className={`max-w-[82%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                    isAttacker
                      ? 'bg-slate-100 text-slate-800 border border-slate-200 rounded-tl-sm'
                      : 'bg-indigo-600 text-white rounded-tr-sm shadow-xs'
                  }`}
                >
                  <div className="whitespace-pre-wrap break-words">{msg.text}</div>
                </div>
              </div>
            );
          })
        )}

        {/* Loading indicator */}
        {session.status === 'running' && messages.length % 2 === 1 && (
          <div className="flex flex-col items-end">
            <div className="bg-indigo-50 border border-indigo-200 rounded-2xl rounded-tr-sm px-4 py-2.5 flex items-center gap-2 text-xs text-indigo-700">
              <span className="h-2 w-2 rounded-full bg-indigo-600 animate-pulse" />
              <span>Honeypot responding...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
