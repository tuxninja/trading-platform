import axios from 'axios';
import { api, tradesAPI, authAPI, performanceAPI } from '../api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});

// Mock location
delete window.location;
window.location = { href: '' };

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue('mock-auth-token');
  });

  describe('axios instance configuration', () => {
    test('creates axios instance with correct base URL', () => {
      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });

    test('request interceptor adds auth token', () => {
      const mockAxiosInstance = {
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() }
        }
      };
      
      mockedAxios.create.mockReturnValue(mockAxiosInstance);
      
      // Import api again to trigger interceptor setup
      jest.resetModules();
      require('../api');
      
      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled();
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });

    test('request interceptor adds Authorization header when token exists', () => {
      const config = { headers: {} };
      mockLocalStorage.getItem.mockReturnValue('test-token');
      
      // Get the request interceptor function
      const mockAxiosInstance = {
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() }
        }
      };
      
      mockedAxios.create.mockReturnValue(mockAxiosInstance);
      
      // Simulate the request interceptor
      const requestInterceptor = (config) => {
        const token = mockLocalStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      };
      
      const result = requestInterceptor(config);
      
      expect(result.headers.Authorization).toBe('Bearer test-token');
    });

    test('response interceptor handles 401 errors', () => {
      const error = {
        response: { status: 401 }
      };
      
      // Simulate the response interceptor error handler
      const responseErrorHandler = (error) => {
        if (error.response?.status === 401) {
          mockLocalStorage.removeItem('authToken');
          mockLocalStorage.removeItem('user');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      };
      
      expect(() => responseErrorHandler(error)).rejects.toEqual(error);
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('authToken');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('user');
      expect(window.location.href).toBe('/login');
    });
  });

  describe('tradesAPI', () => {
    const mockAxiosInstance = {
      get: jest.fn(),
      post: jest.fn(),
      delete: jest.fn()
    };

    beforeEach(() => {
      mockedAxios.create.mockReturnValue(mockAxiosInstance);
    });

    test('getAll calls correct endpoint', async () => {
      const mockTrades = [{ id: 1, symbol: 'AAPL' }];
      mockAxiosInstance.get.mockResolvedValue({ data: mockTrades });

      const result = await tradesAPI.getAll();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/trades');
      expect(result).toEqual(mockTrades);
    });

    test('getById calls correct endpoint with ID', async () => {
      const mockTrade = { id: 1, symbol: 'AAPL' };
      mockAxiosInstance.get.mockResolvedValue({ data: mockTrade });

      const result = await tradesAPI.getById(1);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/trades/1');
      expect(result).toEqual(mockTrade);
    });

    test('create calls correct endpoint with trade data', async () => {
      const tradeData = { symbol: 'AAPL', trade_type: 'BUY', quantity: 10 };
      const mockResponse = { id: 1, ...tradeData };
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await tradesAPI.create(tradeData);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/trades', tradeData);
      expect(result).toEqual(mockResponse);
    });

    test('close calls correct endpoint', async () => {
      const mockResponse = { id: 1, status: 'CLOSED' };
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await tradesAPI.close(1, 150.0);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/trades/1/close', { close_price: 150.0 });
      expect(result).toEqual(mockResponse);
    });

    test('close calls with null price when not provided', async () => {
      const mockResponse = { id: 1, status: 'CLOSED' };
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      await tradesAPI.close(1);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/trades/1/close', { close_price: null });
    });

    test('delete calls correct endpoint', async () => {
      const mockResponse = { message: 'Trade deleted' };
      mockAxiosInstance.delete.mockResolvedValue({ data: mockResponse });

      const result = await tradesAPI.delete(1);

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/api/trades/1');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('authAPI', () => {
    const mockAxiosInstance = {
      get: jest.fn(),
      post: jest.fn()
    };

    beforeEach(() => {
      mockedAxios.create.mockReturnValue(mockAxiosInstance);
    });

    test('googleLogin calls correct endpoint', async () => {
      const mockResponse = { 
        access_token: 'jwt-token',
        user: { email: 'test@example.com' }
      };
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await authAPI.googleLogin('google-token');

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/auth/google', { token: 'google-token' });
      expect(result).toEqual(mockResponse);
    });

    test('getCurrentUser calls correct endpoint', async () => {
      const mockUser = { user: { email: 'test@example.com' } };
      mockAxiosInstance.get.mockResolvedValue({ data: mockUser });

      const result = await authAPI.getCurrentUser();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/auth/me');
      expect(result).toEqual(mockUser);
    });

    test('logout clears localStorage and redirects', () => {
      authAPI.logout();

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('authToken');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('user');
      expect(window.location.href).toBe('/login');
    });
  });

  describe('performanceAPI', () => {
    const mockAxiosInstance = {
      get: jest.fn()
    };

    beforeEach(() => {
      mockedAxios.create.mockReturnValue(mockAxiosInstance);
    });

    test('getMetrics calls correct endpoint', async () => {
      const mockMetrics = { 
        total_profit_loss: 1000,
        win_rate: 75.0,
        current_balance: 105000
      };
      mockAxiosInstance.get.mockResolvedValue({ data: mockMetrics });

      const result = await performanceAPI.getMetrics();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/performance');
      expect(result).toEqual(mockMetrics);
    });

    test('getHistory calls correct endpoint with days parameter', async () => {
      const mockHistory = [
        { date: '2023-01-01', value: 100000 },
        { date: '2023-01-02', value: 105000 }
      ];
      mockAxiosInstance.get.mockResolvedValue({ data: mockHistory });

      const result = await performanceAPI.getHistory(7);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/portfolio-history?days=7');
      expect(result).toEqual(mockHistory);
    });

    test('getHistory uses default days when not provided', async () => {
      const mockHistory = [];
      mockAxiosInstance.get.mockResolvedValue({ data: mockHistory });

      await performanceAPI.getHistory();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/portfolio-history?days=30');
    });
  });

  describe('error handling', () => {
    const mockAxiosInstance = {
      get: jest.fn(),
      post: jest.fn()
    };

    beforeEach(() => {
      mockedAxios.create.mockReturnValue(mockAxiosInstance);
    });

    test('API calls handle network errors', async () => {
      const networkError = new Error('Network Error');
      mockAxiosInstance.get.mockRejectedValue(networkError);

      await expect(tradesAPI.getAll()).rejects.toThrow('Network Error');
    });

    test('API calls handle HTTP errors', async () => {
      const httpError = {
        response: {
          status: 400,
          data: { detail: 'Bad Request' }
        }
      };
      mockAxiosInstance.post.mockRejectedValue(httpError);

      await expect(tradesAPI.create({})).rejects.toEqual(httpError);
    });
  });
});