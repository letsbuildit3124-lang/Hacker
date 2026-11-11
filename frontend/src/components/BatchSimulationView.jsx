import React, { useState, useEffect } from 'react';
import { Layers, Play, XCircle, RefreshCw, Zap } from 'lucide-react';
import { api } from '../services/api';

export default function BatchSimulationView({ onOpenSession }) {
  const [scenarios, setScenarios] = useState([]);
  const [personas, setPersonas] = useState([]);
  const [batches, setBatches] = useState([]);
  const [activeBatch, setActiveBatch] = useState(null);
  const [launching, setLaunching] = useState(false);

  const [batchName, setBatchName] = useState('Security Benchmark Run');
  const [selectedScenarios, setSelectedScenarios] = useState(['fictional_bank_verification']);
  const [selectedPersonas, setSelectedPersonas] = useState(['friendly_support', 'urgent_support']);
  const [selectedLanguages] = useState(['English']);
  const [concurrency, setConcurrency] = useState(2);
  const [maxTurns, setMaxTurns] = useState(5);

  const fetchBatches = async () => {
    try {
      const data = await api.listBatches();
      setBatches(data);
      if (data.length > 0 && !activeBatch) {
        setActiveBatch(data[0]);
      } else if (activeBatch) {
        const updated = data.find((b) => b.batchId === activeBatch.batchId);
        if (updated) setActiveBatch(updated);
      }
    } catch (err) {
      console.error('Failed to list batches:', err);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        const [scList, pList] = await Promise.all([
          api.listScenarios(),
          api.listPersonas()
        ]);
        setScenarios(scList);
        setPersonas(pList);
        await fetchBatches();
      } catch (err) {
        console.error('Init batch view failed:', err);
      }
    };
    init();

    const interval = setInterval(fetchBatches, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleScenario = (id) => {
    setSelectedScenarios((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleTogglePersona = (id) => {
    setSelectedPersonas((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleLaunchBatch = async (e) => {
    e.preventDefault();
    if (selectedScenarios.length === 0 || selectedPersonas.length === 0) return;

    setLaunching(true);
    try {
      const payload = {
        batchName,
        scenarioIds: selectedScenarios,
        personaIds: selectedPersonas,
        languages: selectedLanguages,
        concurrency: parseInt(concurrency, 10),
        maxTurns: parseInt(maxTurns, 10)
      };
      const created = await api.createBatch(payload);
      setActiveBatch(created);
      await fetchBatches();
    } catch (err) {
      console.error('Failed to launch batch:', err);
    } finally {
      setLaunching(false);
    }
  };

  const handleCancelBatch = async (batchId) => {
    try {
      await api.cancelBatch(batchId);
      await fetchBatches();
    } catch (err) {
      console.error('Failed to cancel batch:', err);
    }
  };

  const totalCombinations = selectedScenarios.length * selectedPersonas.length * selectedLanguages.length;

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Batch Matrix Simulations</h2>
            <p className="text-xs text-slate-500">Parallel matrix runs across scenarios, personas, and languages</p>
          </div>
        </div>
        <button
          onClick={fetchBatches}
          className="p-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 transition-colors"
          title="Refresh batches"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Matrix Configurator */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Zap className="w-3.5 h-3.5 text-indigo-600" />
            Configure Matrix
          </h3>

          <form onSubmit={handleLaunchBatch} className="space-y-4">
            <div>
              <label className="block text-xs text-slate-600 font-medium mb-1">Batch Name</label>
              <input
                type="text"
                value={batchName}
                onChange={(e) => setBatchName(e.target.value)}
                required
                className="w-full bg-white border border-slate-200 text-xs text-slate-900 rounded-lg px-3 py-2 outline-none focus:border-indigo-600"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-600 mb-1.5 font-medium">
                Scenarios ({selectedScenarios.length} selected)
              </label>
              <div className="space-y-1.5 max-h-36 overflow-y-auto overscroll-contain pr-1">
                {scenarios.map((sc) => {
                  const id = sc.scenarioId || sc.id;
                  return (
                    <label
                      key={id}
                      className="flex items-center gap-2 p-2 rounded-lg bg-slate-50 border border-slate-200 hover:border-slate-300 text-xs text-slate-700 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedScenarios.includes(id)}
                        onChange={() => handleToggleScenario(id)}
                        className="rounded accent-indigo-600"
                      />
                      <span className="truncate">{sc.name || sc.title || id}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            <div>
              <label className="block text-xs text-slate-600 mb-1.5 font-medium">
                Personas ({selectedPersonas.length} selected)
              </label>
              <div className="space-y-1.5 max-h-36 overflow-y-auto overscroll-contain pr-1">
                {personas.map((p) => {
                  const id = p.personaId || p.id;
                  return (
                    <label
                      key={id}
                      className="flex items-center gap-2 p-2 rounded-lg bg-slate-50 border border-slate-200 hover:border-slate-300 text-xs text-slate-700 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedPersonas.includes(id)}
                        onChange={() => handleTogglePersona(id)}
                        className="rounded accent-indigo-600"
                      />
                      <span className="truncate">{p.name || id}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-slate-600 mb-1 font-medium">Concurrency</label>
                <select
                  value={concurrency}
                  onChange={(e) => setConcurrency(e.target.value)}
                  className="w-full bg-white border border-slate-200 text-xs text-slate-800 rounded-lg px-2.5 py-2 outline-none focus:border-indigo-600"
                >
                  <option value={1}>1 Worker</option>
                  <option value={2}>2 Workers</option>
                  <option value={3}>3 Workers</option>
                  <option value={5}>5 Workers</option>
                </select>
              </div>

              <div>
                <label className="block text-xs text-slate-600 mb-1 font-medium">Max Turns</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={maxTurns}
                  onChange={(e) => setMaxTurns(e.target.value)}
                  className="w-full bg-white border border-slate-200 text-xs text-slate-800 rounded-lg px-2.5 py-2 outline-none focus:border-indigo-600"
                />
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-center justify-between">
              <span>Matrix Total:</span>
              <span className="font-bold text-indigo-700">{totalCombinations} simulations</span>
            </div>

            <button
              type="submit"
              disabled={launching || totalCombinations === 0}
              className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold text-xs flex items-center justify-center gap-2 transition-colors"
            >
              {launching ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Starting Batch...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  Launch Batch ({totalCombinations})
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right: Active Batch Status & List */}
        <div className="lg:col-span-2 space-y-4 min-w-0">
          {activeBatch ? (
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-bold text-slate-900">{activeBatch.batchName}</h4>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase border ${
                      activeBatch.status === 'completed'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : activeBatch.status === 'running'
                        ? 'bg-indigo-50 text-indigo-700 border-indigo-200 animate-pulse'
                        : 'bg-rose-50 text-rose-700 border-rose-200'
                    }`}>
                      {activeBatch.status}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">ID: {activeBatch.batchId}</span>
                </div>

                {activeBatch.status === 'running' && (
                  <button
                    onClick={() => handleCancelBatch(activeBatch.batchId)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-semibold border border-rose-200 transition-colors"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    Cancel
                  </button>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5 font-mono">
                  <span>Progress: {activeBatch.completedSessions || 0} / {activeBatch.totalSessions || 0}</span>
                  <span>
                    {activeBatch.totalSessions > 0
                      ? Math.round(((activeBatch.completedSessions || 0) / activeBatch.totalSessions) * 100)
                      : 0}%
                  </span>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-indigo-600 h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${
                        activeBatch.totalSessions > 0
                          ? ((activeBatch.completedSessions || 0) / activeBatch.totalSessions) * 100
                          : 0
                      }%`
                    }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-100">
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/80 text-center">
                  <span className="text-[10px] text-slate-500 block">Total</span>
                  <span className="text-sm font-bold text-slate-900 font-mono">{activeBatch.totalSessions || 0}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-indigo-50/70 border border-indigo-200/70 text-center">
                  <span className="text-[10px] text-indigo-600 block">Running</span>
                  <span className="text-sm font-bold text-indigo-700 font-mono">{activeBatch.runningSessions || 0}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-emerald-50/70 border border-emerald-200/70 text-center">
                  <span className="text-[10px] text-emerald-600 block">Completed</span>
                  <span className="text-sm font-bold text-emerald-700 font-mono">{activeBatch.completedSessions || 0}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-rose-50/70 border border-rose-200/70 text-center">
                  <span className="text-[10px] text-rose-600 block">Failed</span>
                  <span className="text-sm font-bold text-rose-700 font-mono">{activeBatch.failedSessions || 0}</span>
                </div>
              </div>

              <div className="pt-2">
                <h5 className="text-xs font-semibold text-slate-800 mb-2">Simulations in Batch</h5>
                <div className="max-h-64 overflow-y-auto overscroll-contain rounded-lg border border-slate-200">
                  <table className="w-full text-left text-xs text-slate-700">
                    <thead className="bg-slate-50 text-[10px] text-slate-500 uppercase font-semibold sticky top-0 border-b border-slate-200">
                      <tr>
                        <th className="p-2.5">Session ID</th>
                        <th className="p-2.5">Scenario</th>
                        <th className="p-2.5">Persona</th>
                        <th className="p-2.5">Status</th>
                        <th className="p-2.5 text-right">Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white font-mono text-[11px]">
                      {(activeBatch.sessionSummaries || []).map((s) => (
                        <tr
                          key={s.sessionId}
                          onClick={() => onOpenSession && onOpenSession(s.sessionId)}
                          className="hover:bg-slate-50 cursor-pointer transition-colors"
                        >
                          <td className="p-2.5 text-indigo-700 font-semibold">{s.sessionId}</td>
                          <td className="p-2.5 text-slate-600 font-sans">{s.scenarioId}</td>
                          <td className="p-2.5 text-slate-600 font-sans">{s.personaId}</td>
                          <td className="p-2.5">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-sans font-medium ${
                              s.status === 'completed'
                                ? 'bg-emerald-50 text-emerald-700'
                                : s.status === 'running'
                                ? 'bg-indigo-50 text-indigo-700'
                                : 'bg-slate-100 text-slate-600'
                            }`}>
                              {s.status}
                            </span>
                          </td>
                          <td className="p-2.5 text-right font-bold text-slate-900">
                            {s.score !== null && s.score !== undefined ? `${s.score}%` : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center bg-white border border-slate-200 rounded-xl text-slate-500 text-xs">
              No batch runs yet. Configure options on the left and launch a batch.
            </div>
          )}

          {batches.length > 1 && (
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
              <h5 className="text-xs font-semibold text-slate-800 mb-2">Previous Batches</h5>
              <div className="space-y-1.5">
                {batches.map((b) => (
                  <div
                    key={b.batchId}
                    onClick={() => setActiveBatch(b)}
                    className={`p-3 rounded-lg border text-xs flex items-center justify-between cursor-pointer transition-colors ${
                      activeBatch?.batchId === b.batchId
                        ? 'bg-indigo-50/70 border-indigo-300 text-slate-900'
                        : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <div>
                      <span className="font-semibold text-slate-900 mr-2">{b.batchName}</span>
                      <span className="text-[10px] font-mono text-slate-500">{b.batchId}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-[11px] font-mono">{b.completedSessions}/{b.totalSessions} Done</span>
                      <span className={`text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full ${
                        b.status === 'completed' ? 'text-emerald-700 bg-emerald-50' : 'text-indigo-700 bg-indigo-50'
                      }`}>
                        {b.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
