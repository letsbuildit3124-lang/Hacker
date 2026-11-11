import React, { useState, useEffect } from 'react';
import { FileText, Download, Search } from 'lucide-react';
import { api } from '../services/api';

export default function ReportsView() {
  const [sessions, setSessions] = useState([]);
  const [evaluations, setEvaluations] = useState([]);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sessList, evList] = await Promise.all([
          api.listSessions(),
          api.listEvaluations()
        ]);
        setSessions(sessList);
        setEvaluations(evList);
      } catch (err) {
        console.error('Failed to load reports:', err);
      }
    };
    fetchData();
  }, []);

  const evalMap = evaluations.reduce((acc, ev) => {
    acc[ev.sessionId] = ev;
    return acc;
  }, {});

  const filtered = sessions.filter((s) => {
    const term = search.toLowerCase();
    return (
      s.sessionId.toLowerCase().includes(term) ||
      (s.scenario || '').toLowerCase().includes(term) ||
      (s.personaId || '').toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Evaluation Reports & Exports</h2>
            <p className="text-xs text-slate-500">Download audit-grade reports in structured JSON or CSV</p>
          </div>
        </div>

        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search session or scenario..."
            className="bg-white border border-slate-200 text-xs text-slate-900 rounded-lg pl-8 pr-3 py-1.5 outline-none focus:border-indigo-600 w-64"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((s) => {
          const ev = evalMap[s.sessionId];
          return (
            <div
              key={s.sessionId}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between hover:border-slate-300 transition-colors"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold text-indigo-700">{s.sessionId}</span>
                  {ev ? (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold font-mono bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {ev.overallScore ?? ev.overall_score}% ({ev.grade || ev.performance_tier})
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-slate-100 text-slate-500">
                      Not Evaluated
                    </span>
                  )}
                </div>

                <h4 className="text-sm font-semibold text-slate-900 mb-1 truncate">{s.scenario}</h4>
                <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-3">
                  <span className="capitalize">{s.personaId?.replace(/_/g, ' ')}</span>
                  <span>·</span>
                  <span>{s.language}</span>
                  <span>·</span>
                  <span>{s.totalMessages || 0} msgs</span>
                </div>

                {ev && (
                  <div className="space-y-1.5 p-3 rounded-lg bg-slate-50 border border-slate-200/70 text-[11px] mb-4">
                    <div className="flex justify-between text-slate-600">
                      <span>Scam Detection:</span>
                      <span className="font-mono text-slate-900 font-bold">
                        {ev.metric_scores?.scam_detection ?? ev.metrics?.scamDetection?.score ?? 0}%
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Intelligence F1:</span>
                      <span className="font-mono text-indigo-700 font-bold">
                        {((ev.intelligence_metrics?.f1_score || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2 pt-3 border-t border-slate-100">
                <a
                  href={api.getJsonReportUrl(s.sessionId)}
                  target="_blank"
                  rel="noreferrer"
                  className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-xs text-slate-700 font-medium border border-slate-200 transition-colors"
                >
                  <Download className="w-3.5 h-3.5 text-indigo-600" />
                  JSON
                </a>
                <a
                  href={api.getCsvReportUrl(s.sessionId)}
                  target="_blank"
                  rel="noreferrer"
                  className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-xs text-white font-medium transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  CSV
                </a>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
