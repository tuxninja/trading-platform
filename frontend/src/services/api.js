import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Trades API
export const tradesAPI = {
  getAll: () => api.get('/api/trades').then(res => res.data),
  getById: (id) => api.get(`/api/trades/${id}`).then(res => res.data),
  create: (trade) => api.post('/api/trades', trade).then(res => res.data),
  close: (id, closePrice = null) => api.post(`/api/trades/${id}/close`, { close_price: closePrice }).then(res => res.data),
  delete: (id) => api.delete(`/api/trades/${id}`).then(res => res.data),
};

// Sentiment API
export const sentimentAPI = {
  getAll: () => api.get('/api/sentiment').then(res => res.data),
  getBySymbol: (symbol) => api.get(`/api/sentiment/${symbol}`).then(res => res.data),
  analyze: (symbol) => api.post('/api/analyze-sentiment', { symbol }).then(res => res.data),
  analyzeBulk: (symbols) => api.post('/api/analyze-bulk-sentiment', { symbols, force_refresh: true }).then(res => res.data),
  runFullCycle: (symbols) => api.post('/api/full-analysis-cycle', symbols).then(res => res.data),
};

// Recommendations API
export const recommendationsAPI = {
  getAll: () => api.get('/api/recommendations').then(res => res.data),
  generate: (symbols = null) => api.post('/api/generate-recommendations', symbols).then(res => res.data),
  approve: (id) => api.post(`/api/recommendations/${id}/approve`).then(res => res.data),
  reject: (id, reason = '') => api.post(`/api/recommendations/${id}/reject`, reason).then(res => res.data),
};

// Market Discovery API
export const marketAPI = {
  scan: (limit = 10) => api.post(`/api/market-scan?limit=${limit}`).then(res => res.data),
  autoDiscover: (minScore = 0.5) => api.post(`/api/auto-discover?min_trending_score=${minScore}`).then(res => res.data),
  discoveryPipeline: (minScore = 0.5) => api.post(`/api/discovery-to-recommendations?min_trending_score=${minScore}`).then(res => res.data),
};

// Performance API
export const performanceAPI = {
  getMetrics: () => api.get('/api/performance').then(res => res.data),
  getHistory: (days = 30) => api.get(`/api/portfolio-history?days=${days}`).then(res => res.data),
};

// Stocks API
export const stocksAPI = {
  getAll: () => api.get('/api/stocks').then(res => res.data),
  add: (symbol) => api.post('/api/stocks', symbol).then(res => res.data),
  getMarketData: (symbol, days = 30) => api.get(`/api/market-data/${symbol}?days=${days}`).then(res => res.data),
};

// Strategy API
export const strategyAPI = {
  run: () => api.post('/api/run-strategy').then(res => res.data),
};

// Auth API
export const authAPI = {
  googleLogin: (token) => api.post('/api/auth/google', { token }).then(res => res.data),
  getCurrentUser: () => api.get('/api/auth/me').then(res => res.data),
  logout: () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    window.location.href = '/login';
  }
};

// Admin API
export const adminAPI = {
  // Dashboard
  getDashboard: () => api.get('/api/admin/dashboard').then(res => res.data),
  
  // User Management
  getUsers: (params = {}) => api.get('/api/admin/users', { params }).then(res => res.data),
  getUserActivity: (userId, limit = 100) => api.get(`/api/admin/users/${userId}/activity?limit=${limit}`).then(res => res.data),
  updateUserStatus: (userId, isActive) => api.post(`/api/admin/users/${userId}/status`, { is_active: isActive }).then(res => res.data),
  updateUserAdminStatus: (userId, isAdmin) => api.post(`/api/admin/users/${userId}/admin`, { is_admin: isAdmin }).then(res => res.data),
  
  // System Health
  getSystemHealth: () => api.get('/api/admin/health').then(res => res.data),
  getSystemMetrics: (params = {}) => api.get('/api/admin/metrics', { params }).then(res => res.data),
  
  // Analytics
  getUsageAnalytics: (days = 30) => api.get(`/api/admin/analytics/usage?days=${days}`).then(res => res.data),
  getPlatformAnalytics: () => api.get('/api/admin/analytics/platform').then(res => res.data),
  
  // Configuration
  getFeatureFlags: () => api.get('/api/admin/config/features').then(res => res.data),
  updateFeatureFlag: (flagId, isEnabled, rolloutPercentage = 0) => 
    api.put(`/api/admin/config/features/${flagId}`, { is_enabled: isEnabled, rollout_percentage: rolloutPercentage }).then(res => res.data),
  getSystemConfig: (category = null) => api.get('/api/admin/config/system', { params: { category } }).then(res => res.data),
  
  // Data Management
  createDataExport: (exportType, filters = {}) => 
    api.post('/api/admin/data/export', { export_type: exportType, filters }).then(res => res.data),
  getDataExports: () => api.get('/api/admin/data/exports').then(res => res.data),
  
  // Activity Logs
  getAllActivity: (params = {}) => api.get('/api/admin/activity', { params }).then(res => res.data)
};

export { api }; 