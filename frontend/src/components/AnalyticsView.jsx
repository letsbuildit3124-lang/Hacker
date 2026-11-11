import React, { useState, useEffect } from 'react';
import { BarChart3, RefreshCw, Users, FileCode2 } from 'lucide-react';
import { api } from '../services/api';

export default function AnalyticsView() {
  const [overview, setOverview] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [personas, setPersonas] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const [ovData, scData, pData] = await Promise.all([
        api.getAnalyticsOverview(),
        api.getScenarioAnalytics(),
        api.getPersonaAnalytics()
      ]);
      setOverview(ovData);
      setScenarios(scData);
      setPersonas(pData);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <BarChart3 className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Platform Analytics</h2>
            <p className="text-xs text-slate-500">Aggregated red-team scores, scam resistance, and persona effectiveness</p>
          </div>
        </div>
        <button
          onClick={fetchAnalytics}
          disabled={loading}
          className="p-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 transition-colors"
          title="Refresh metrics"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Simulations', val: overview?.total_sessions || 0, sub: 'Total runs' },
          { label: 'Messages', val: overview?.total_messages || 0, sub: 'Turns exchanged' },
          { label: 'Evaluated', val: overview?.total_evaluated || 0, sub: '10-metric scored' },
          { label: 'Avg Score', val: `${overview?.average_score ?? 0}%`, sub: 'Platform mean', highlight: true },
          { label: 'Detection', val: `${overview?.average_scam_detection_score ?? 0}%`, sub: 'Scam resistance' },
          { label: 'Intel F1', val: `${((overview?.average_intelligence_f1 || 0) * 100).toFixed(0)}%`, sub: 'Extraction F1' }
        ].map((kpi, idx) => (
          <div key={idx} className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
            <span className="text-[11px] font-medium text-slate-500 block mb-1">{kpi.label}</span>
            <div className={`text-2xl font-bold font-mono ${kpi.highlight ? 'text-indigo-600' : 'text-slate-900'}`}>
              {kpi.val}
            </div>
            <span className="text-[10px] text-slate-400">{kpi.sub}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
            <FileCode2 className="w-4 h-4 text-indigo-600" />
            Performance by Scenario
          </h3>
          <div className="space-y-2.5">
            {scenarios.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No scenario evaluations yet.</p>
            ) : (
              scenarios.map((sc) => (
                <div key={sc.scenario_id} className="p-3 rounded-lg bg-slate-50 border border-slate-200/80">
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="font-semibold text-slate-900">{sc.scenario_id}</span>
                    <span className="font-mono text-indigo-700 font-semibold">{sc.session_count} runs</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-600">
                    <div className="flex justify-between">
                      <span>Avg Score:</span>
                      <span className="font-mono text-slate-900 font-bold">{sc.average_score}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Detection:</span>
                      <span className="font-mono text-emerald-700 font-bold">{sc.average_detection}%</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Users className="w-4 h-4 text-indigo-600" />
            Persona Effectiveness
          </h3>
          <div className="space-y-2.5">
            {personas.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No persona evaluations yet.</p>
            ) : (
              personas.map((p) => (
                <div key={p.persona_id} className="p-3 rounded-lg bg-slate-50 border border-slate-200/80">
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="font-semibold text-slate-900 capitalize">{p.persona_id.replace(/_/g, ' ')}</span>
                    <span className="font-mono text-indigo-700 font-semibold">{p.session_count} runs</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-600">
                    <div className="flex justify-between">
                      <span>Avg Score:</span>
                      <span className="font-mono text-slate-900 font-bold">{p.average_score}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Continuity:</span>
                      <span className="font-mono text-indigo-700 font-bold">{p.average_continuity}%</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
