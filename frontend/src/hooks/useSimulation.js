import { useState, useEffect, useRef, useCallback } from 'react';
import api from '../services/api';

export function useSimulation(initialSessionId = null) {
  const [activeSessionId, setActiveSessionId] = useState(initialSessionId);
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [stats, setStats] = useState({
    totalSimulations: 0,
    runningSimulations: 0,
    completedSimulations: 0,
    failedSimulations: 0,
    stoppedSimulations: 0,
    totalMessages: 0
  });
  const [sessionsList, setSessionsList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  const pollIntervalRef = useRef(null);

  // Refresh dashboard stats and list
  const refreshOverview = useCallback(async () => {
    try {
      const [statsData, listData] = await Promise.all([
        api.getStats(),
        api.listSessions()
      ]);
      setStats(statsData);
      setSessionsList(listData);
    } catch (err) {
      console.error('Failed to load overview data:', err);
    }
  }, []);

  // Refresh active session data
  const refreshActiveSession = useCallback(async (id = activeSessionId) => {
    if (!id) return;
    try {
      const [sessionData, messagesData] = await Promise.all([
        api.getSession(id),
        api.getMessages(id)
      ]);
      setSession(sessionData);
      setMessages(messagesData);
      setError(sessionData.errorMessage || null);
    } catch (err) {
      console.error(`Failed to refresh session ${id}:`, err);
    }
  }, [activeSessionId]);

  // Initial load
  useEffect(() => {
    refreshOverview();
  }, [refreshOverview]);

  // Session selection change
  useEffect(() => {
    if (activeSessionId) {
      refreshActiveSession(activeSessionId);
    } else {
      setSession(null);
      setMessages([]);
    }
  }, [activeSessionId, refreshActiveSession]);

  // Polling loop for active session when 'running'
  useEffect(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    if (activeSessionId && session?.status === 'running') {
      pollIntervalRef.current = setInterval(async () => {
        try {
          const sessionData = await api.getSession(activeSessionId);
          setSession(sessionData);
          setMessages(sessionData.conversationHistory || []);
          if (sessionData.errorMessage) {
            setError(sessionData.errorMessage);
          }
          // Also update overview stats periodically
          refreshOverview();
          // If state transitioned away from running, interval can stop
          if (sessionData.status !== 'running') {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }, 1500);
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [activeSessionId, session?.status, refreshOverview]);

  // Actions
  const createSession = async (payload) => {
    setActionLoading(true);
    setError(null);
    try {
      const newSession = await api.createSession(payload);
      setActiveSessionId(newSession.sessionId);
      setSession(newSession);
      setMessages([]);
      await refreshOverview();
      return newSession;
    } catch (err) {
      const msg = err.response?.data?.detail || err.message;
      setError(msg);
      throw err;
    } finally {
      setActionLoading(false);
    }
  };

  const startSession = async (id = activeSessionId) => {
    if (!id) return;
    setActionLoading(true);
    setError(null);
    try {
      await api.startSession(id);
      await refreshActiveSession(id);
      await refreshOverview();
    } catch (err) {
      const msg = err.response?.data?.detail || err.message;
      setError(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const stopSession = async (id = activeSessionId) => {
    if (!id) return;
    setActionLoading(true);
    try {
      await api.stopSession(id);
      await refreshActiveSession(id);
      await refreshOverview();
    } catch (err) {
      const msg = err.response?.data?.detail || err.message;
      setError(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const resumeSession = async (id = activeSessionId) => {
    if (!id) return;
    setActionLoading(true);
    setError(null);
    try {
      await api.resumeSession(id);
      await refreshActiveSession(id);
      await refreshOverview();
    } catch (err) {
      const msg = err.response?.data?.detail || err.message;
      setError(msg);
    } finally {
      setActionLoading(false);
    }
  };

  return {
    activeSessionId,
    setActiveSessionId,
    session,
    messages,
    stats,
    sessionsList,
    loading,
    actionLoading,
    error,
    createSession,
    startSession,
    stopSession,
    resumeSession,
    refreshOverview,
    refreshActiveSession
  };
}
