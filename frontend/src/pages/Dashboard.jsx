import React, { useState, useEffect } from 'react';
import {
  Menu, RefreshCw, LayoutDashboard, Terminal, MessageSquare,
  Award, Layers, BarChart3, GitCompare, FileText, Sliders
} from 'lucide-react';
import NavigationDrawer from '../components/NavigationDrawer';
import DashboardOverview from '../components/DashboardOverview';
import SimulationCreator from '../components/SimulationCreator';
import LiveConversationView from '../components/LiveConversationView';
import SessionHistoryTable from '../components/SessionHistoryTable';
import TranscriptModal from '../components/TranscriptModal';
import AgentIntelligencePanel from '../components/AgentIntelligencePanel';
import EvaluationView from '../components/EvaluationView';
import BatchSimulationView from '../components/BatchSimulationView';
import AnalyticsView from '../components/AnalyticsView';
import ReplayCompareView from '../components/ReplayCompareView';
import ReportsView from '../components/ReportsView';
import SettingsDiagnosticsView from '../components/SettingsDiagnosticsView';
import { useSimulation } from '../hooks/useSimulation';
import { api } from '../services/api';

const NAV_GROUPS = [
  {
    title: 'Core Workspace',
    items: [
      { id: 'overview', label: 'Overview', icon: LayoutDashboard },
      { id: 'simulation_manager', label: 'Simulations', icon: Terminal },
      { id: 'live_conversation', label: 'Live Chat', icon: MessageSquare }
    ]
  },
  {
    title: 'Evaluation & Benchmarking',
    items: [
      { id: 'evaluation', label: 'Evaluation Results', icon: Award },
      { id: 'batch_simulations', label: 'Batch Matrix', icon: Layers },
      { id: 'analytics', label: 'Analytics', icon: BarChart3 },
      { id: 'replay_compare', label: 'Replay & Compare', icon: GitCompare }
    ]
  },
  {
    title: 'Reports & System',
    items: [
      { id: 'reports', label: 'Reports & Exports', icon: FileText },
      { id: 'settings', label: 'Diagnostics', icon: Sliders }
    ]
  }
];

const ALL_ITEMS = NAV_GROUPS.flatMap((g) => g.items);

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [backendHealth, setBackendHealth] = useState(null);
  const [transcriptSession, setTranscriptSession] = useState(null);

  const {
    activeSessionId,
    setActiveSessionId,
    session,
    messages,
    stats,
    sessionsList,
    actionLoading,
    createSession,
    startSession,
    stopSession,
    resumeSession,
    refreshOverview,
    refreshActiveSession
  } = useSimulation();

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const data = await api.getHealth();
        setBackendHealth(data);
      } catch (err) {
        setBackendHealth({ status: 'offline', error: err.message });
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleCreateAndStart = async (payload) => {
    try {
      const newSession = await createSession(payload);
      await startSession(newSession.sessionId);
      setActiveTab('live_conversation');
    } catch (err) {
      console.error('Failed to create and start session:', err);
    }
  };

  const handleOpenSessionFromBatch = (sessId) => {
    setActiveSessionId(sessId);
    setActiveTab('live_conversation');
  };

  const currentTabMeta = ALL_ITEMS.find((t) => t.id === activeTab) || ALL_ITEMS[0];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      {/* Compact Single-Row Top Bar (< 12% viewport height) */}
      <header className="h-14 border-b border-slate-200 bg-white/95 backdrop-blur sticky top-0 z-30 shrink-0">
        <div className="max-w-6xl h-full mx-auto px-4 sm:px-6 flex items-center justify-between gap-4">
          {/* Left: Drawer Trigger + Active Section */}
          <div className="flex items-center gap-3 min-w-0">
            <button
              type="button"
              onClick={() => setDrawerOpen(true)}
              aria-label="Open navigation menu"
              aria-controls="main-nav-drawer"
              aria-expanded={drawerOpen}
              className="p-2 -ml-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors flex items-center gap-2"
            >
              <Menu className="w-5 h-5" />
              <span className="hidden sm:inline text-xs font-medium">Menu</span>
            </button>

            <div className="h-4 w-px bg-slate-200 hidden sm:block" />

            <div className="flex items-center gap-2 min-w-0">
              <span className="text-xs font-semibold text-slate-400 hidden md:inline">Honeypot Studio</span>
              <span className="text-slate-300 hidden md:inline">/</span>
              <h1 className="text-sm font-semibold text-slate-900 truncate">{currentTabMeta.label}</h1>
            </div>
          </div>

          {/* Right: Minimal Status & Refresh */}
          <div className="flex items-center gap-2.5 shrink-0">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-50 border border-slate-200 text-[11px] font-medium text-slate-700">
              <span className={`h-2 w-2 rounded-full ${backendHealth?.status === 'healthy' ? 'bg-emerald-500' : 'bg-rose-500'}`} />
              <span>{backendHealth?.status === 'healthy' ? 'Online' : 'Offline'}</span>
            </div>

            <button
              type="button"
              onClick={() => {
                refreshOverview();
                if (activeSessionId) refreshActiveSession();
              }}
              title="Refresh data"
              className="p-1.5 rounded-lg bg-white hover:bg-slate-100 text-slate-500 hover:text-slate-800 border border-slate-200 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Slide-in Sidebar Drawer */}
      <NavigationDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        groups={NAV_GROUPS}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        backendHealth={backendHealth}
      />

      {/* Main Content Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-4 sm:py-5 space-y-4 min-w-0">
        {activeTab === 'overview' && (
          <div className="space-y-4">
            <DashboardOverview stats={stats} />
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
              <div className="lg:col-span-5 min-w-0">
                <SimulationCreator onCreateSession={handleCreateAndStart} actionLoading={actionLoading} />
              </div>
              <div className="lg:col-span-7 min-w-0">
                <SessionHistoryTable
                  sessions={sessionsList}
                  activeSessionId={activeSessionId}
                  onSelectSession={(id) => {
                    setActiveSessionId(id);
                    setActiveTab('live_conversation');
                  }}
                  onResumeSession={resumeSession}
                  onOpenTranscript={setTranscriptSession}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'simulation_manager' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-5 min-w-0">
              <SimulationCreator onCreateSession={handleCreateAndStart} actionLoading={actionLoading} />
            </div>
            <div className="lg:col-span-7 min-w-0">
              <SessionHistoryTable
                sessions={sessionsList}
                activeSessionId={activeSessionId}
                onSelectSession={(id) => {
                  setActiveSessionId(id);
                  setActiveTab('live_conversation');
                }}
                onResumeSession={resumeSession}
                onOpenTranscript={setTranscriptSession}
              />
            </div>
          </div>
        )}

        {activeTab === 'live_conversation' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-5 min-w-0">
              {session ? (
                <AgentIntelligencePanel session={session} />
              ) : (
                <div className="bg-white border border-slate-200 rounded-xl p-6 text-center text-slate-500 text-xs shadow-xs">
                  Select a session or create a simulation to inspect live intelligence state.
                </div>
              )}
            </div>

            <div className="lg:col-span-7 min-w-0">
              <LiveConversationView
                session={session}
                messages={messages}
                actionLoading={actionLoading}
                onStart={startSession}
                onStop={stopSession}
                onResume={resumeSession}
                onOpenTranscript={setTranscriptSession}
              />
            </div>
          </div>
        )}

        {activeTab === 'evaluation' && (
          <EvaluationView activeSessionId={activeSessionId} />
        )}

        {activeTab === 'batch_simulations' && (
          <BatchSimulationView onOpenSession={handleOpenSessionFromBatch} />
        )}

        {activeTab === 'analytics' && <AnalyticsView />}

        {activeTab === 'replay_compare' && (
          <ReplayCompareView activeSessionId={activeSessionId} />
        )}

        {activeTab === 'reports' && <ReportsView />}

        {activeTab === 'settings' && <SettingsDiagnosticsView />}
      </main>

      {/* Transcript Modal */}
      {transcriptSession && (
        <TranscriptModal
          session={transcriptSession}
          onClose={() => setTranscriptSession(null)}
        />
      )}
    </div>
  );
}
