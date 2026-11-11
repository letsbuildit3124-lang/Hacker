import React, { useState } from 'react';
import { History } from 'lucide-react';

const SCENARIO_LABELS = {
  fictional_bank_verification: 'Bank KYC',
  banking_kyc_verification: 'Bank KYC',
  fictional_upi_payment: 'UPI Payment',
  fictional_customer_support: 'Cust. Support',
  fictional_cashback_notification: 'Cashback',
  fictional_account_security: 'Security Alert',
  fictional_tech_support: 'Tech Support',
  utility_bill_overdue: 'Utility Bill',
  tax_refund_processing: 'Tax Refund'
};

export default function SessionHistoryTable({
  sessions,
  activeSessionId,
  onSelectSession,
  onResumeSession,
  onOpenTranscript
}) {
  const [filter, setFilter] = useState('ALL');

  const filteredSessions = sessions.filter((s) => {
    if (filter === 'ALL') return true;
    return (s.status || '').toUpperCase() === filter;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'running':
        return <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">RUNNING</span>;
      case 'completed':
        return <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">COMPLETED</span>;
      case 'failed':
        return <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">FAILED</span>;
      case 'stopped':
        return <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">STOPPED</span>;
      default:
        return <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 uppercase">{status}</span>;
    }
  };

  const formatShortTime = (isoString) => {
    if (!isoString) return '-';
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoString;
    }
  };

  const formatFullDate = (isoString) => {
    if (!isoString) return '';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xs flex flex-col">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3 pb-2.5 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-indigo-600" />
          <h2 id="session-history-title" className="text-sm font-semibold text-slate-900">
            Session History
          </h2>
          <span className="text-xs text-slate-400 font-mono">({filteredSessions.length})</span>
        </div>

        <div className="flex flex-wrap items-center gap-0.5 bg-slate-100 p-0.5 rounded-lg text-[10px]">
          {['ALL', 'RUNNING', 'COMPLETED', 'FAILED', 'STOPPED'].map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setFilter(tab)}
              className={`px-2 py-1 rounded-md font-medium transition-colors ${
                filter === tab
                  ? 'bg-white text-indigo-700 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Responsive Container Query Table Region */}
      <div
        tabIndex={0}
        role="region"
        aria-labelledby="session-history-title"
        className="session-table-wrap"
      >
        <table className="session-table text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500 font-medium text-[10px] uppercase tracking-wider">
              <th className="py-2 pr-3">Session / Scenario</th>
              <th className="py-2 px-2">Status</th>
              <th className="py-2 px-2 text-center">Msgs</th>
              <th className="py-2 pl-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredSessions.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-10 text-center text-slate-400">
                  No sessions found matching current filter.
                </td>
              </tr>
            ) : (
              filteredSessions.map((s) => {
                const isActive = s.sessionId === activeSessionId;
                const niceScenario = SCENARIO_LABELS[s.scenario] || s.scenario;
                return (
                  <tr
                    key={s.sessionId}
                    className={`transition-colors ${
                      isActive ? 'bg-indigo-50/50' : 'hover:bg-slate-50/80'
                    }`}
                  >
                    <td data-label="Session" className="py-2.5 pr-3">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono font-semibold text-slate-900 text-xs">
                          {s.sessionId}
                        </span>
                        {isActive && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 font-semibold">
                            Active
                          </span>
                        )}
                      </div>
                      <div
                        className="text-[11px] text-slate-500 mt-0.5 truncate max-w-[200px]"
                        title={`${s.scenario} • ${formatFullDate(s.createdAt)}`}
                      >
                        {niceScenario} · {formatShortTime(s.createdAt)}
                      </div>
                    </td>
                    <td data-label="Status" className="py-2.5 px-2 whitespace-nowrap">
                      {getStatusBadge(s.status)}
                    </td>
                    <td data-label="Msgs" className="py-2.5 px-2 font-mono text-slate-700 text-center">
                      {s.totalMessages}
                    </td>
                    <td data-label="Actions" className="py-2.5 pl-2 text-right whitespace-nowrap">
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => onSelectSession(s.sessionId)}
                          className="px-2.5 py-1 rounded-md bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 text-[11px] font-medium transition-colors"
                        >
                          Inspect
                        </button>
                        {(s.status === 'stopped' || s.status === 'failed') && (
                          <button
                            type="button"
                            onClick={() => onResumeSession(s.sessionId)}
                            className="px-2.5 py-1 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white text-[11px] font-medium transition-colors"
                          >
                            Resume
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => onOpenTranscript(s)}
                          className="px-2 py-1 rounded-md bg-white hover:bg-slate-100 text-slate-500 border border-slate-200 text-[11px] transition-colors"
                        >
                          JSON
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
