import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 15000
});

export const api = {
  // System Health & Ready
  async getHealth() {
    const res = await client.get('/api/health');
    return res.data;
  },

  async getReady() {
    const res = await client.get('/api/ready');
    return res.data;
  },

  async getStats() {
    const res = await client.get('/api/sessions/stats');
    return res.data;
  },

  // Personas & Scenarios
  async listPersonas() {
    const res = await client.get('/api/sessions/personas');
    return res.data;
  },

  async listScenarios() {
    const res = await client.get('/api/sessions/scenarios');
    return res.data;
  },

  // Sessions Lifecycle
  async listSessions(status = null) {
    const params = status ? { status } : {};
    const res = await client.get('/api/sessions', { params });
    return res.data;
  },

  async getSession(sessionId) {
    const res = await client.get(`/api/sessions/${sessionId}`);
    return res.data;
  },

  async getMessages(sessionId) {
    const res = await client.get(`/api/sessions/${sessionId}/messages`);
    return res.data;
  },

  async createSession(payload) {
    const res = await client.post('/api/sessions', payload);
    return res.data;
  },

  async startSession(sessionId) {
    const res = await client.post(`/api/sessions/${sessionId}/start`);
    return res.data;
  },

  async stopSession(sessionId) {
    const res = await client.post(`/api/sessions/${sessionId}/stop`);
    return res.data;
  },

  async stepSession(sessionId) {
    const res = await client.post(`/api/sessions/${sessionId}/step`);
    return res.data;
  },

  // Evaluation
  async evaluateSession(sessionId) {
    const res = await client.post(`/api/sessions/${sessionId}/evaluate`);
    return res.data;
  },

  async getSessionEvaluation(sessionId) {
    const res = await client.get(`/api/sessions/${sessionId}/evaluation`);
    return res.data;
  },

  async listEvaluations() {
    const res = await client.get('/api/evaluations');
    return res.data;
  },

  // Batch Simulations
  async createBatch(payload) {
    const res = await client.post('/api/batches', payload);
    return res.data;
  },

  async listBatches() {
    const res = await client.get('/api/batches');
    return res.data;
  },

  async getBatch(batchId) {
    const res = await client.get(`/api/batches/${batchId}`);
    return res.data;
  },

  async cancelBatch(batchId) {
    const res = await client.post(`/api/batches/${batchId}/cancel`);
    return res.data;
  },

  // Replay & Comparison
  async getReplay(sessionId) {
    const res = await client.get(`/api/sessions/${sessionId}/replay`);
    return res.data;
  },

  async rerunSession(sessionId, payload) {
    const res = await client.post(`/api/sessions/${sessionId}/rerun`, payload);
    return res.data;
  },

  async compareSessions(sessionId1, sessionId2) {
    const res = await client.post('/api/compare', {
      session_id_1: sessionId1,
      session_id_2: sessionId2
    });
    return res.data;
  },

  // Analytics
  async getAnalyticsOverview() {
    const res = await client.get('/api/analytics/overview');
    return res.data;
  },

  async getScenarioAnalytics() {
    const res = await client.get('/api/analytics/scenarios');
    return res.data;
  },

  async getPersonaAnalytics() {
    const res = await client.get('/api/analytics/personas');
    return res.data;
  },

  // Reports URLs
  getJsonReportUrl(sessionId) {
    return `${API_BASE_URL}/api/reports/${sessionId}/json`;
  },

  getCsvReportUrl(sessionId) {
    return `${API_BASE_URL}/api/reports/${sessionId}/csv`;
  },

  // Stress Testing
  async runStressTest(payload) {
    const res = await client.post('/api/stress-tests', payload);
    return res.data;
  },

  async getStressTest(testId) {
    const res = await client.get(`/api/stress-tests/${testId}`);
    return res.data;
  },

  // Dynamic Honeypot Endpoint Settings
  async getHoneypotSettings() {
    const res = await client.get('/api/settings/honeypot');
    return res.data;
  },

  async updateHoneypotSettings(payload) {
    const res = await client.put('/api/settings/honeypot', payload);
    return res.data;
  },

  async testHoneypotConnection(payload) {
    const res = await client.post('/api/settings/honeypot/test', payload, { timeout: 25000 });
    return res.data;
  }
};

export default api;
