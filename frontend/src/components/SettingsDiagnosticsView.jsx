import React, { useState, useEffect } from 'react';
import { Sliders, Activity, Server, Zap, RefreshCw, BarChart, Globe, Key, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function SettingsDiagnosticsView() {
  const [health, setHealth] = useState(null);

  // Target Honeypot Config Form
  const [honeypotUrl, setHoneypotUrl] = useState('');
  const [honeypotApiKey, setHoneypotApiKey] = useState('');
  const [hasApiKey, setHasApiKey] = useState(false);
  const [savingEndpoint, setSavingEndpoint] = useState(false);
  const [testingEndpoint, setTestingEndpoint] = useState(false);
  const [saveMessage, setSaveMessage] = useState(null);
  const [saveError, setSaveError] = useState(null);
  const [probeResult, setProbeResult] = useState(null);

  const [numRequests, setNumRequests] = useState(10);
  const [concurrency, setConcurrency] = useState(2);
  const [delayMs, setDelayMs] = useState(200);
  const [stressRunning, setStressRunning] = useState(false);
  const [stressResult, setStressResult] = useState(null);

  const [weights, setWeights] = useState({
    scamDetection: 15,
    conversationContinuity: 15,
    personaConsistency: 10,
    intelligenceExtraction: 15,
    contextRetention: 10,
    responseRelevance: 10,
    hallucinationResistance: 10,
    conversationNaturalness: 5,
    apiReliability: 5,
    completion: 5
  });
  const [weightsSaved, setWeightsSaved] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [hData, hpSettings] = await Promise.all([
          api.getHealth(),
          api.getHoneypotSettings()
        ]);
        setHealth(hData);
        setHoneypotUrl(hpSettings.honeypot_base_url || '');
        setHasApiKey(Boolean(hpSettings.has_api_key));
      } catch (err) {
        console.error('Failed to get status:', err);
      }
    };
    fetchStatus();
  }, []);

  const handleTestConnection = async () => {
    if (!honeypotUrl.trim()) return;
    setTestingEndpoint(true);
    setProbeResult(null);
    setSaveError(null);
    try {
      const res = await api.testHoneypotConnection({
        honeypot_base_url: honeypotUrl.trim(),
        honeypot_api_key: honeypotApiKey.trim() || undefined
      });
      setProbeResult(res);
    } catch (err) {
      setSaveError(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || err.message);
    } finally {
      setTestingEndpoint(false);
    }
  };

  const handleSaveEndpoint = async (e) => {
    e.preventDefault();
    setSavingEndpoint(true);
    setSaveMessage(null);
    setSaveError(null);
    try {
      const updated = await api.updateHoneypotSettings({
        honeypot_base_url: honeypotUrl.trim(),
        honeypot_api_key: honeypotApiKey.trim() || undefined
      });
      setHoneypotUrl(updated.honeypot_base_url);
      setHasApiKey(Boolean(updated.has_api_key));
      setHoneypotApiKey('');
      setSaveMessage('Target Honeypot URL updated & persisted!');
      const hData = await api.getHealth();
      setHealth(hData);
      setTimeout(() => setSaveMessage(null), 3500);
    } catch (err) {
      setSaveError(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || err.message);
    } finally {
      setSavingEndpoint(false);
    }
  };

  const handleRunStressTest = async (e) => {
    e.preventDefault();
    setStressRunning(true);
    setStressResult(null);
    try {
      const res = await api.runStressTest({
        num_requests: parseInt(numRequests, 10),
        concurrency: parseInt(concurrency, 10),
        delay_between_requests_ms: parseInt(delayMs, 10),
        safety_error_threshold: 0.25
      });
      setStressResult(res);
    } catch (err) {
      console.error('Stress test failed:', err);
    } finally {
      setStressRunning(false);
    }
  };

  const totalWeight = Object.values(weights).reduce((a, b) => a + Number(b), 0);

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
          <Sliders className="w-4 h-4" />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-slate-900">Diagnostics & Settings</h2>
          <p className="text-xs text-slate-500">Configure Target Honeypot URL, test connectivity, and run benchmarks</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div className="space-y-6">
          {/* Interactive Target Honeypot Configuration */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <Globe className="w-4 h-4 text-indigo-600" />
                Target Honeypot Endpoint
              </h3>
              <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${
                hasApiKey ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'
              }`}>
                {hasApiKey ? 'Key Configured' : 'No Key'}
              </span>
            </div>

            <form onSubmit={handleSaveEndpoint} className="space-y-3">
              <div>
                <label className="block text-[11px] font-medium text-slate-600 mb-1">
                  Honeypot Base URL
                </label>
                <input
                  type="url"
                  required
                  value={honeypotUrl}
                  onChange={(e) => setHoneypotUrl(e.target.value)}
                  placeholder="https://your-honeypot-api.onrender.com"
                  className="w-full bg-white border border-slate-200 text-xs font-mono text-slate-900 rounded-lg px-3 py-2 outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100"
                />
                <p className="text-[10px] text-slate-400 mt-1">
                  Requests automatically target <code className="text-slate-600">/honeypot</code>
                </p>
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-600 mb-1 flex items-center gap-1">
                  <Key className="w-3 h-3 text-slate-400" />
                  x-api-key Header (Optional)
                </label>
                <input
                  type="password"
                  value={honeypotApiKey}
                  onChange={(e) => setHoneypotApiKey(e.target.value)}
                  placeholder={hasApiKey ? '•••••••• (leave blank to keep current)' : 'Enter API key if required'}
                  autoComplete="off"
                  className="w-full bg-white border border-slate-200 text-xs font-mono text-slate-900 rounded-lg px-3 py-2 outline-none focus:border-indigo-600"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={testingEndpoint || !honeypotUrl.trim()}
                  className="flex-1 py-2 px-3 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-medium flex items-center justify-center gap-1.5 disabled:opacity-50 transition-colors"
                >
                  {testingEndpoint ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Activity className="w-3.5 h-3.5 text-indigo-600" />}
                  Test Link
                </button>
                <button
                  type="submit"
                  disabled={savingEndpoint || !honeypotUrl.trim()}
                  className="flex-1 py-2 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold flex items-center justify-center gap-1.5 disabled:opacity-50 transition-colors"
                >
                  {savingEndpoint ? 'Saving...' : 'Save Endpoint'}
                </button>
              </div>
            </form>

            {saveMessage && (
              <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-[11px] flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                <span>{saveMessage}</span>
              </div>
            )}

            {saveError && (
              <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-[11px] flex items-center gap-2">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span className="break-all">{saveError}</span>
              </div>
            )}

            {probeResult && (
              <div className={`p-3 rounded-lg border text-[11px] space-y-1 ${
                probeResult.reachable
                  ? 'bg-emerald-50/70 border-emerald-200 text-emerald-800'
                  : 'bg-rose-50/70 border-rose-200 text-rose-800'
              }`}>
                <div className="flex items-center justify-between font-semibold">
                  <span>{probeResult.reachable ? 'Connection Verified (HTTP 200)' : `Failed (HTTP ${probeResult.status_code})`}</span>
                  <span className="font-mono">{probeResult.latency_ms} ms</span>
                </div>
                {probeResult.sample_reply_preview && (
                  <p className="text-[10px] text-emerald-700 italic truncate" title={probeResult.sample_reply_preview}>
                    Reply: "{probeResult.sample_reply_preview}"
                  </p>
                )}
                {probeResult.error && (
                  <p className="text-[10px] text-rose-700 break-all">{probeResult.error}</p>
                )}
              </div>
            )}

            <div className="pt-3 border-t border-slate-100 space-y-2 text-xs">
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-slate-500 flex items-center gap-1.5"><Server className="w-3.5 h-3.5 text-slate-400" /> LLM Model</span>
                <span className="font-mono text-indigo-700 font-medium">{health?.llm_model || 'gemini-3.1-flash-lite'}</span>
              </div>
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-slate-500">Database</span>
                <span className="font-mono text-emerald-700 capitalize">{health?.database || 'Connected'}</span>
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <BarChart className="w-4 h-4 text-indigo-600" />
                Metric Weights (%)
              </h3>
              <span className={`text-[11px] font-mono font-bold ${totalWeight === 100 ? 'text-emerald-600' : 'text-rose-600'}`}>
                Total: {totalWeight}%
              </span>
            </div>

            <div className="space-y-1.5 max-h-56 overflow-y-auto overscroll-contain pr-1 text-xs">
              {Object.entries(weights).map(([k, val]) => (
                <div key={k} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200/70">
                  <span className="text-slate-700 capitalize text-[11px]">{k.replace(/([A-Z])/g, ' $1')}</span>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={val}
                    onChange={(e) => setWeights({ ...weights, [k]: Number(e.target.value) })}
                    className="w-14 bg-white border border-slate-200 rounded px-1.5 py-0.5 text-right font-mono text-xs text-indigo-700 font-semibold outline-none focus:border-indigo-600"
                  />
                </div>
              ))}
            </div>

            <button
              onClick={() => {
                setWeightsSaved(true);
                setTimeout(() => setWeightsSaved(false), 2000);
              }}
              className="w-full py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-white transition-colors"
            >
              {weightsSaved ? 'Weights Saved!' : 'Apply Scoring Weights'}
            </button>
          </div>
        </div>

        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Controlled Stress & Reliability Benchmark</h3>
              <p className="text-xs text-slate-500">
                Measures P50, P95, P99 latency percentiles against active target with automatic safety circuit-breaker
              </p>
            </div>
          </div>

          <form onSubmit={handleRunStressTest} className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs text-slate-600 font-medium mb-1">Probe Requests</label>
              <input
                type="number"
                min={2}
                max={50}
                value={numRequests}
                onChange={(e) => setNumRequests(e.target.value)}
                className="w-full bg-white border border-slate-200 text-xs text-slate-900 rounded-lg px-3 py-2 outline-none focus:border-indigo-600"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-600 font-medium mb-1">Concurrency</label>
              <select
                value={concurrency}
                onChange={(e) => setConcurrency(e.target.value)}
                className="w-full bg-white border border-slate-200 text-xs text-slate-900 rounded-lg px-3 py-2 outline-none focus:border-indigo-600"
              >
                <option value={1}>1 Concurrent Worker</option>
                <option value={2}>2 Concurrent Workers</option>
                <option value={4}>4 Concurrent Workers</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-slate-600 font-medium mb-1">Delay (ms)</label>
              <input
                type="number"
                min={0}
                max={2000}
                step={50}
                value={delayMs}
                onChange={(e) => setDelayMs(e.target.value)}
                className="w-full bg-white border border-slate-200 text-xs text-slate-900 rounded-lg px-3 py-2 outline-none focus:border-indigo-600"
              />
            </div>

            <div className="md:col-span-3">
              <button
                type="submit"
                disabled={stressRunning}
                className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold text-xs flex items-center justify-center gap-2 transition-colors"
              >
                {stressRunning ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Executing Probes...
                  </>
                ) : (
                  <>
                    <Zap className="w-3.5 h-3.5 fill-current" />
                    Run Controlled Benchmark
                  </>
                )}
              </button>
            </div>
          </form>

          {stressResult && (
            <div className="space-y-4 pt-4 border-t border-slate-100">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-800 uppercase">Benchmark Results</span>
                <span className={`text-[10px] font-semibold px-2.5 py-0.5 rounded-full uppercase border ${
                  stressResult.status === 'completed'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-rose-50 text-rose-700 border-rose-200'
                }`}>
                  {stressResult.status}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 block font-mono">P50 (Median)</span>
                  <span className="text-lg font-bold font-mono text-emerald-600">
                    {stressResult.summary?.latency_p50_ms || 0} ms
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 block font-mono">P95 Latency</span>
                  <span className="text-lg font-bold font-mono text-indigo-600">
                    {stressResult.summary?.latency_p95_ms || 0} ms
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 block font-mono">P99 Latency</span>
                  <span className="text-lg font-bold font-mono text-slate-900">
                    {stressResult.summary?.latency_p99_ms || 0} ms
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 block font-mono">Circuit Breaker</span>
                  <span className={`text-xs font-bold font-mono ${
                    stressResult.summary?.aborted_by_safety ? 'text-rose-600' : 'text-emerald-600'
                  }`}>
                    {stressResult.summary?.aborted_by_safety ? 'Tripped (Safe)' : 'Normal'}
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                <span className="text-slate-500 font-medium block mb-2">HTTP Status Distribution</span>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(stressResult.summary?.status_code_distribution || {}).map(([code, count]) => (
                    <span
                      key={code}
                      className={`px-2 py-1 rounded font-mono text-[11px] font-medium ${
                        code === '200'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}
                    >
                      HTTP {code}: {count}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
