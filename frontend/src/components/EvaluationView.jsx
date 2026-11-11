import React, { useState, useEffect } from 'react';
import { Award, CheckCircle2, AlertTriangle, Download, Cpu, RefreshCw, BarChart2 } from 'lucide-react';
import { api } from '../services/api';

export default function EvaluationView({ activeSessionId }) {
  const [sessions, setSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState(activeSessionId || '');
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const list = await api.listSessions();
        setSessions(list);
        if (!selectedSessionId && list.length > 0) {
          setSelectedSessionId(list[0].sessionId);
        }
      } catch (err) {
        console.error('Failed to load sessions:', err);
      }
    };
    fetchSessions();
  }, []);

  useEffect(() => {
    if (activeSessionId) {
      setSelectedSessionId(activeSessionId);
    }
  }, [activeSessionId]);

  useEffect(() => {
    if (!selectedSessionId) return;
    const fetchEvaluation = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getSessionEvaluation(selectedSessionId);
        setEvaluation(data);
      } catch {
        setEvaluation(null);
      } finally {
        setLoading(false);
      }
    };
    fetchEvaluation();
  }, [selectedSessionId]);

  const handleRunEvaluation = async () => {
    if (!selectedSessionId) return;
    setEvaluating(true);
    setError(null);
    try {
      const data = await api.evaluateSession(selectedSessionId);
      setEvaluation(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Evaluation failed.');
    } finally {
      setEvaluating(false);
    }
  };

  const getGradeColor = (grade) => {
    if (grade?.startsWith('A')) return 'text-emerald-700 border-emerald-200 bg-emerald-50';
    if (grade?.startsWith('B')) return 'text-indigo-700 border-indigo-200 bg-indigo-50';
    if (grade?.startsWith('C')) return 'text-amber-700 border-amber-200 bg-amber-50';
    return 'text-rose-700 border-rose-200 bg-rose-50';
  };

  return (
    <div className="space-y-6">
      {/* Selector Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Award className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Automated Evaluation</h2>
            <p className="text-xs text-slate-500">10-metric quantitative benchmark & LLM judge analysis</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <select
            value={selectedSessionId}
            onChange={(e) => setSelectedSessionId(e.target.value)}
            className="bg-white border border-slate-200 text-xs text-slate-800 rounded-lg px-3 py-2 outline-none focus:border-indigo-600 max-w-xs"
          >
            {sessions.map((s) => (
              <option key={s.sessionId} value={s.sessionId}>
                {s.sessionId} — {s.scenario} ({s.language})
              </option>
            ))}
          </select>

          <button
            onClick={handleRunEvaluation}
            disabled={evaluating || !selectedSessionId}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold text-xs transition-colors"
          >
            {evaluating ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Evaluating...
              </>
            ) : (
              <>
                <BarChart2 className="w-3.5 h-3.5" />
                Evaluate Session
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-slate-500 text-sm bg-white border border-slate-200 rounded-xl">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-600" />
          Loading evaluation report...
        </div>
      ) : !evaluation ? (
        <div className="p-12 text-center bg-white border border-dashed border-slate-300 rounded-xl">
          <Award className="w-9 h-9 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-800">No evaluation found for this session</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-4">
            Run an automated evaluation to compute the 10-metric score, intelligence recall, and judge recommendations.
          </p>
          <button
            onClick={handleRunEvaluation}
            disabled={evaluating || !selectedSessionId}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold"
          >
            Evaluate Now
          </button>
        </div>
      ) : (
        <div className="space-y-5">
          {/* Executive Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex items-center gap-4">
              <div className={`w-14 h-14 rounded-xl border flex items-center justify-center font-bold text-xl shrink-0 ${getGradeColor(evaluation.grade || evaluation.performance_tier)}`}>
                {evaluation.grade || evaluation.performance_tier || 'A'}
              </div>
              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Overall Score</span>
                <div className="text-2xl font-bold text-slate-900 mt-0.5">
                  {evaluation.overall_score ?? evaluation.overallScore ?? 0}
                  <span className="text-xs text-slate-400 font-normal"> / 100</span>
                </div>
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                <span>Scam Detection</span>
                <span className="font-bold text-slate-900">
                  {evaluation.metric_scores?.scam_detection ?? evaluation.metrics?.scamDetection?.score ?? 0}%
                </span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mb-2">
                <div
                  className="bg-indigo-600 h-full rounded-full"
                  style={{ width: `${evaluation.metric_scores?.scam_detection ?? evaluation.metrics?.scamDetection?.score ?? 0}%` }}
                />
              </div>
              <span className="text-[11px] text-slate-400">Resistance & verification</span>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                <span>Intelligence F1</span>
                <span className="font-bold text-slate-900">
                  {((evaluation.intelligence_metrics?.f1_score || 0) * 100).toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mb-2">
                <div
                  className="bg-indigo-600 h-full rounded-full"
                  style={{ width: `${(evaluation.intelligence_metrics?.f1_score || 0) * 100}%` }}
                />
              </div>
              <span className="text-[11px] text-slate-400">
                P: {(evaluation.intelligence_metrics?.precision || 0).toFixed(2)} · R: {(evaluation.intelligence_metrics?.recall || 0).toFixed(2)}
              </span>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between">
              <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Export Report</span>
              <div className="flex items-center gap-2 mt-2">
                <a
                  href={api.getJsonReportUrl(selectedSessionId)}
                  target="_blank"
                  rel="noreferrer"
                  className="flex-1 flex items-center justify-center gap-1.5 px-2.5 py-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-xs text-slate-700 font-medium border border-slate-200 transition-colors"
                >
                  <Download className="w-3.5 h-3.5 text-indigo-600" />
                  JSON
                </a>
                <a
                  href={api.getCsvReportUrl(selectedSessionId)}
                  target="_blank"
                  rel="noreferrer"
                  className="flex-1 flex items-center justify-center gap-1.5 px-2.5 py-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-xs text-slate-700 font-medium border border-slate-200 transition-colors"
                >
                  <Download className="w-3.5 h-3.5 text-indigo-600" />
                  CSV
                </a>
              </div>
            </div>
          </div>

          {/* 10-Metric Grid */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <h3 className="text-sm font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-indigo-600" />
              10-Metric Score Breakdown
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {Object.entries(evaluation.metric_scores || {}).map(([key, score]) => {
                const label = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
                return (
                  <div key={key} className="p-3 rounded-lg bg-slate-50 border border-slate-200/70">
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="text-slate-700 font-medium">{label}</span>
                      <span className="font-mono font-bold text-indigo-700">{score} / 100</span>
                    </div>
                    <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-indigo-600 h-full rounded-full"
                        style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Strengths & Weaknesses */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <h4 className="text-xs font-semibold text-emerald-700 uppercase tracking-wider mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                Strengths
              </h4>
              <ul className="space-y-2">
                {(evaluation.strengths || []).map((s, idx) => (
                  <li key={idx} className="text-xs text-slate-600 flex items-start gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <h4 className="text-xs font-semibold text-rose-700 uppercase tracking-wider mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Weaknesses
              </h4>
              <ul className="space-y-2">
                {(evaluation.weaknesses || []).map((w, idx) => (
                  <li key={idx} className="text-xs text-slate-600 flex items-start gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-rose-500 mt-1.5 shrink-0" />
                    <span>{w}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* LLM Judge Notes */}
          {evaluation.llm_judge_review && (
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <h4 className="text-sm font-semibold text-slate-900 mb-2 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-indigo-600" />
                LLM Judge Review & Recommendations
              </h4>
              <p className="text-xs text-slate-600 italic mb-4">
                "{evaluation.llm_judge_review.reasoning || 'Automated evaluation completed.'}"
              </p>
              <div className="space-y-2">
                {(evaluation.recommendations || evaluation.llm_judge_review.recommendations || []).map((rec, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 flex items-start gap-2.5">
                    <span className="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 font-mono text-[10px] font-bold shrink-0">
                      #{idx + 1}
                    </span>
                    <span>{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
