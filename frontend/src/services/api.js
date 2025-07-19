import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

export default api; 