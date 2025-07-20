import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import Dashboard from '../Dashboard';
import { performanceAPI, tradesAPI, sentimentAPI } from '../../services/api';

// Mock the API services
jest.mock('../../services/api');

// Mock recharts components
jest.mock('recharts', () => ({
  LineChart: ({ children }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }) => <div data-testid="responsive-container">{children}</div>
}));

const createTestQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  });
};

const TestWrapper = ({ children }) => {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('Dashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders loading state initially', () => {
    // Mock APIs to return pending promises
    performanceAPI.getMetrics.mockReturnValue(new Promise(() => {}));
    tradesAPI.getAll.mockReturnValue(new Promise(() => {}));
    sentimentAPI.getAll.mockReturnValue(new Promise(() => {}));
    performanceAPI.getHistory.mockReturnValue(new Promise(() => {}));

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  test('renders dashboard with successful data load', async () => {
    const mockPerformance = {
      current_balance: 105000,
      total_return: 5.0,
      win_rate: 75.0,
      max_drawdown: 2.5,
      total_trades: 10,
      winning_trades: 8,
      losing_trades: 2
    };

    const mockTrades = [
      {
        id: 1,
        symbol: 'AAPL',
        trade_type: 'BUY',
        quantity: 10,
        price: 150.0,
        timestamp: '2023-01-01T10:00:00Z'
      },
      {
        id: 2,
        symbol: 'GOOGL',
        trade_type: 'SELL',
        quantity: 5,
        price: 2500.0,
        timestamp: '2023-01-02T11:00:00Z'
      }
    ];

    const mockSentiment = [
      {
        symbol: 'AAPL',
        overall_sentiment: 0.6,
        news_count: 15,
        social_count: 25
      },
      {
        symbol: 'GOOGL',
        overall_sentiment: -0.3,
        news_count: 8,
        social_count: 12
      }
    ];

    const mockHistory = [
      { date: '2023-01-01', value: 100000 },
      { date: '2023-01-02', value: 105000 }
    ];

    performanceAPI.getMetrics.mockResolvedValue(mockPerformance);
    tradesAPI.getAll.mockResolvedValue(mockTrades);
    sentimentAPI.getAll.mockResolvedValue(mockSentiment);
    performanceAPI.getHistory.mockResolvedValue(mockHistory);

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    // Check performance cards
    expect(screen.getByText('$105,000')).toBeInTheDocument();
    expect(screen.getByText('5.00%')).toBeInTheDocument();
    expect(screen.getByText('75.0%')).toBeInTheDocument();
    expect(screen.getByText('2.5%')).toBeInTheDocument();

    // Check recent trades section
    expect(screen.getByText('Recent Trades')).toBeInTheDocument();
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('GOOGL')).toBeInTheDocument();

    // Check sentiment section
    expect(screen.getByText('Top Sentiment Scores')).toBeInTheDocument();
    expect(screen.getByText('+0.600')).toBeInTheDocument();
    expect(screen.getByText('-0.300')).toBeInTheDocument();

    // Check chart is rendered
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  test('renders error state when API calls fail', async () => {
    const mockError = new Error('API Error');
    
    performanceAPI.getMetrics.mockRejectedValue(mockError);
    tradesAPI.getAll.mockRejectedValue(mockError);
    sentimentAPI.getAll.mockRejectedValue(mockError);
    performanceAPI.getHistory.mockRejectedValue(mockError);

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Dashboard Loading Error')).toBeInTheDocument();
    });

    expect(screen.getByText(/Performance API: API Error/)).toBeInTheDocument();
    expect(screen.getByText(/Trades API: API Error/)).toBeInTheDocument();
    expect(screen.getByText(/Sentiment API: API Error/)).toBeInTheDocument();
    expect(screen.getByText(/Portfolio History API: API Error/)).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  test('handles empty data gracefully', async () => {
    const mockPerformance = {
      current_balance: 100000,
      total_return: 0,
      win_rate: 0,
      max_drawdown: 0
    };

    performanceAPI.getMetrics.mockResolvedValue(mockPerformance);
    tradesAPI.getAll.mockResolvedValue([]);
    sentimentAPI.getAll.mockResolvedValue([]);
    performanceAPI.getHistory.mockResolvedValue([]);

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    expect(screen.getByText('No recent trades')).toBeInTheDocument();
    expect(screen.getByText('$100,000')).toBeInTheDocument();
  });

  test('formats numbers correctly in performance cards', async () => {
    const mockPerformance = {
      current_balance: 1234567.89,
      total_return: 12.3456,
      win_rate: 66.666,
      max_drawdown: 5.4321
    };

    performanceAPI.getMetrics.mockResolvedValue(mockPerformance);
    tradesAPI.getAll.mockResolvedValue([]);
    sentimentAPI.getAll.mockResolvedValue([]);
    performanceAPI.getHistory.mockResolvedValue([]);

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('$1,234,568')).toBeInTheDocument(); // Rounded and formatted
      expect(screen.getByText('12.35%')).toBeInTheDocument(); // Rounded to 2 decimals
      expect(screen.getByText('66.7%')).toBeInTheDocument(); // Rounded to 1 decimal
      expect(screen.getByText('5.4%')).toBeInTheDocument(); // Rounded to 1 decimal
    });
  });

  test('displays correct sentiment colors', async () => {
    const mockSentiment = [
      {
        symbol: 'POSITIVE',
        overall_sentiment: 0.8,
        news_count: 10,
        social_count: 15
      },
      {
        symbol: 'NEGATIVE',
        overall_sentiment: -0.8,
        news_count: 5,
        social_count: 8
      },
      {
        symbol: 'NEUTRAL',
        overall_sentiment: 0.1,
        news_count: 3,
        social_count: 5
      }
    ];

    performanceAPI.getMetrics.mockResolvedValue({});
    tradesAPI.getAll.mockResolvedValue([]);
    sentimentAPI.getAll.mockResolvedValue(mockSentiment);
    performanceAPI.getHistory.mockResolvedValue([]);

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('POSITIVE')).toBeInTheDocument();
    });

    // Check that sentiment values are displayed with correct signs
    expect(screen.getByText('+0.800')).toBeInTheDocument();
    expect(screen.getByText('-0.800')).toBeInTheDocument();
    expect(screen.getByText('+0.100')).toBeInTheDocument();
  });
});