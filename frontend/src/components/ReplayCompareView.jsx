import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, FastForward, GitCompare, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export default function ReplayCompareView({ activeSessionId }) {
  const [sessions, setSessions] = useState([]);
  const [personas, setPersonas] = useState([]);
  const [activeTab, setActiveTab] = useState('replay');

  const [replaySessionId, setReplaySessionId] = useState(activeSessionId || '');
  const [replayData, setReplayData] = useState(null);
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [replaySpeed, setReplaySpeed] = useState(1);
  const [loadingReplay, setLoadingReplay] = useState(false);

  const [compareSession1, setCompareSession1] = useState('');
  const [compareSession2, setCompareSession2] = useState('');
  const [comparisonResult, setComparisonResult] = useState(null);
  const [loadingCompare, setLoadingCompare] = useState(false);

  const [rerunPersona, setRerunPersona] = useState('urgent_support');
  const [rerunning, setRerunning] = useState(false);

  useEffect(() => {
    const init = async () => {
      try {
        const [sessList, pList] = await Promise.all([
          api.listSessions(),
          api.listPersonas()
        ]);
        setSessions(sessList);
        setPersonas(pList);
        if (sessList.length > 0) {
          const s1 = activeSessionId || sessList[0].sessionId;
          setReplaySessionId(s1);
          setCompareSession1(s1);
          if (sessList.length > 1) {
            setCompareSession2(sessList[1].sessionId);
          }
        }
      } catch (err) {
        console.error('Failed to init replay/compare:', err);
      }
    };
    init();
  }, [activeSessionId]);

  useEffect(() => {
    if (!replaySessionId) return;
    const fetchReplay = async () => {
      setLoadingReplay(true);
      setIsPlaying(false);
      setCurrentStepIdx(0);
      try {
        const data = await api.getReplay(replaySessionId);
        setReplayData(data);
      } catch (err) {
        console.error('Failed to load replay data:', err);
      } finally {
        setLoadingReplay(false);
      }
    };
    fetchReplay();
  }, [replaySessionId]);

  useEffect(() => {
    if (!isPlaying || !replayData?.steps) return;
    if (currentStepIdx >= replayData.steps.length - 1) {
      setIsPlaying(false);
      return;
    }

    const currentStep = replayData.steps[currentStepIdx];
    const delay = Math.max(400, (currentStep?.delay_from_prev_ms || 800) / replaySpeed);

    const timer = setTimeout(() => {
      setCurrentStepIdx((prev) => prev + 1);
    }, delay);

    return () => clearTimeout(timer);
  }, [isPlaying, currentStepIdx, replayData, replaySpeed]);

  const handleCompare = async () => {
    if (!compareSession1 || !compareSession2) return;
    setLoadingCompare(true);
    try {
      const data = await api.compareSessions(compareSession1, compareSession2);
      setComparisonResult(data);
    } catch (err) {
      console.error('Failed to compare sessions:', err);
    } finally {
      setLoadingCompare(false);
    }
  };

  const handleRerun = async () => {
    if (!replaySessionId) return;
    setRerunning(true);
    try {
      const res = await api.rerunSession(replaySessionId, {
        new_persona_id: rerunPersona,
        max_turns: 5,
        run_autonomous: true
      });
      const updatedList = await api.listSessions();
      setSessions(updatedList);
      if (res.new_session_id) {
        setReplaySessionId(res.new_session_id);
      }
    } catch (err) {
      console.error('Rerun failed:', err);
    } finally {
      setRerunning(false);
    }
  };

  const visibleSteps = replayData?.steps ? replayData.steps.slice(0, currentStepIdx + 1) : [];

  return (
    <div className="space-y-5">
      {/* Sub-Tabs & Rerun Controls */}
      <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('replay')}
            className={`px-3.5 py-1.5 rounded-md text-xs font-semibold flex items-center gap-2 transition-colors ${
              activeTab === 'replay'
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Play className="w-3.5 h-3.5" />
            Transcript Replay
          </button>
          <button
            onClick={() => {
              setActiveTab('compare');
              if (!comparisonResult && compareSession1 && compareSession2) handleCompare();
            }}
            className={`px-3.5 py-1.5 rounded-md text-xs font-semibold flex items-center gap-2 transition-colors ${
              activeTab === 'compare'
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <GitCompare className="w-3.5 h-3.5" />
            Side-by-Side Compare
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-500">Re-run with:</span>
          <select
            value={rerunPersona}
            onChange={(e) => setRerunPersona(e.target.value)}
            className="bg-white border border-slate-200 text-xs text-slate-800 rounded-lg px-2.5 py-1.5 outline-none focus:border-indigo-600"
          >
            {personas.map((p) => {
              const id = p.personaId || p.id;
              return (
                <option key={id} value={id}>
                  {p.name || id}
                </option>
              );
            })}
          </select>
          <button
            onClick={handleRerun}
            disabled={rerunning || !replaySessionId}
            className="px-3 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-medium border border-slate-200 flex items-center gap-1.5 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${rerunning ? 'animate-spin' : ''}`} />
            Clone & Rerun
          </button>
        </div>
      </div>

      {activeTab === 'replay' ? (
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <span className="text-xs text-slate-500 font-medium">Session:</span>
              <select
                value={replaySessionId}
                onChange={(e) => setReplaySessionId(e.target.value)}
                className="bg-white border border-slate-200 text-xs text-slate-800 rounded-lg px-3 py-1.5 outline-none focus:border-indigo-600 max-w-xs"
              >
                {sessions.map((s) => (
                  <option key={s.sessionId} value={s.sessionId}>
                    {s.sessionId} — {s.scenario} ({s.personaId})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentStepIdx(0);
                }}
                disabled={currentStepIdx === 0}
                className="p-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 disabled:opacity-40"
                title="Reset"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs flex items-center gap-1.5"
              >
                {isPlaying ? <Pause className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current" />}
                {isPlaying ? 'Pause' : 'Play'}
              </button>

              <button
                onClick={() => {
                  if (replayData?.steps && currentStepIdx < replayData.steps.length - 1) {
                    setCurrentStepIdx((prev) => prev + 1);
                  }
                }}
                disabled={!replayData || currentStepIdx >= (replayData.steps?.length || 0) - 1}
                className="p-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 disabled:opacity-40"
                title="Next step"
              >
                <FastForward className="w-3.5 h-3.5" />
              </button>

              <div className="flex items-center gap-1 border-l border-slate-200 pl-3 ml-1">
                {[0.5, 1, 2].map((spd) => (
                  <button
                    key={spd}
                    onClick={() => setReplaySpeed(spd)}
                    className={`px-2 py-1 rounded text-[11px] font-mono ${
                      replaySpeed === spd ? 'bg-indigo-50 text-indigo-700 font-bold' : 'text-slate-500 hover:bg-slate-100'
                    }`}
                  >
                    {spd}x
                  </button>
                ))}
              </div>
            </div>

            <div className="text-xs font-mono text-slate-500">
              Step {replayData?.steps?.length ? currentStepIdx + 1 : 0} / {replayData?.steps?.length || 0}
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs min-h-[420px] flex flex-col justify-between">
            <div className="space-y-4 max-h-[460px] overflow-y-auto overscroll-contain pr-2">
              {loadingReplay ? (
                <div className="text-center py-12 text-slate-400 text-xs">
                  <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-indigo-600" />
                  Loading replay transcript...
                </div>
              ) : visibleSteps.length === 0 ? (
                <div className="text-center py-12 text-slate-400 text-xs">
                  Press Play or Step Forward to start playback.
                </div>
              ) : (
                visibleSteps.map((step, idx) => {
                  const isAttacker = step.sender === 'scammer';
                  return (
                    <div
                      key={idx}
                      className={`flex flex-col ${isAttacker ? 'items-start' : 'items-end'}`}
                    >
                      <div className="flex items-center gap-2 mb-1 px-1">
                        <span className={`text-[10px] font-mono font-semibold uppercase px-2 py-0.5 rounded-full ${
                          isAttacker ? 'bg-slate-100 text-slate-700' : 'bg-indigo-50 text-indigo-700'
                        }`}>
                          {isAttacker ? 'Attacker' : 'Honeypot'}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">+{step.delay_from_prev_ms}ms</span>
                      </div>
                      <div
                        className={`max-w-xl p-3.5 rounded-2xl text-xs leading-relaxed ${
                          isAttacker
                            ? 'bg-slate-100 border border-slate-200 text-slate-800 rounded-tl-sm'
                            : 'bg-indigo-600 text-white rounded-tr-sm'
                        }`}
                      >
                        {step.text}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {replayData?.steps && (
              <div className="pt-4 border-t border-slate-100 mt-4">
                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-indigo-600 h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${((currentStepIdx + 1) / (replayData.steps.length || 1)) * 100}%`
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs text-slate-500 font-medium">Run A:</span>
              <select
                value={compareSession1}
                onChange={(e) => setCompareSession1(e.target.value)}
                className="bg-white border border-slate-200 text-xs text-slate-800 rounded-lg px-2.5 py-1.5 outline-none focus:border-indigo-600"
              >
                {sessions.map((s) => (
                  <option key={s.sessionId} value={s.sessionId}>
                    {s.sessionId} ({s.personaId})
                  </option>
                ))}
              </select>

              <span className="text-xs text-slate-500 font-medium">Run B:</span>
              <select
                value={compareSession2}
                onChange={(e) => setCompareSession2(e.target.value)}
                className="bg-white border border-slate-200 text-xs text-slate-800 rounded-lg px-2.5 py-1.5 outline-none focus:border-indigo-600"
              >
                {sessions.map((s) => (
                  <option key={s.sessionId} value={s.sessionId}>
                    {s.sessionId} ({s.personaId})
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={handleCompare}
              disabled={loadingCompare || !compareSession1 || !compareSession2}
              className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs flex items-center gap-2"
            >
              <GitCompare className="w-3.5 h-3.5" />
              Compare
            </button>
          </div>

          {comparisonResult && (
            <div className="space-y-4">
              {comparisonResult.score_comparison && (
                <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex items-center justify-around">
                  <div className="text-center">
                    <span className="text-[11px] text-slate-500 block">Run A Score</span>
                    <span className="text-2xl font-bold text-slate-900 font-mono">
                      {comparisonResult.score_comparison.overall_1}%
                    </span>
                  </div>
                  <div className="text-center">
                    <span className="text-[11px] text-slate-500 block">Delta</span>
                    <span className={`text-xl font-bold font-mono ${
                      comparisonResult.score_comparison.overall_diff >= 0 ? 'text-emerald-600' : 'text-rose-600'
                    }`}>
                      {comparisonResult.score_comparison.overall_diff >= 0 ? '+' : ''}
                      {comparisonResult.score_comparison.overall_diff}%
                    </span>
                  </div>
                  <div className="text-center">
                    <span className="text-[11px] text-slate-500 block">Run B Score</span>
                    <span className="text-2xl font-bold text-slate-900 font-mono">
                      {comparisonResult.score_comparison.overall_2}%
                    </span>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs space-y-3">
                  <h4 className="text-xs font-bold text-indigo-700 uppercase tracking-wider">
                    Run A: {comparisonResult.session_1.session_id} ({comparisonResult.session_1.persona_id})
                  </h4>
                  <div className="space-y-2.5 max-h-[460px] overflow-y-auto overscroll-contain pr-1">
                    {comparisonResult.turn_comparison.map((t, i) => (
                      <div key={i} className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 text-xs">
                        <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
                          Turn {t.turn_index} · {t.role}
                        </span>
                        <p className="text-slate-700">{t.session_1?.text || '—'}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs space-y-3">
                  <h4 className="text-xs font-bold text-indigo-700 uppercase tracking-wider">
                    Run B: {comparisonResult.session_2.session_id} ({comparisonResult.session_2.persona_id})
                  </h4>
                  <div className="space-y-2.5 max-h-[460px] overflow-y-auto overscroll-contain pr-1">
                    {comparisonResult.turn_comparison.map((t, i) => (
                      <div key={i} className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 text-xs">
                        <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
                          Turn {t.turn_index} · {t.role}
                        </span>
                        <p className="text-slate-700">{t.session_2?.text || '—'}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
