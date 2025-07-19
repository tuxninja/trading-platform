import React from 'react';
import { useQuery } from 'react-query';
import { 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon, 
  CurrencyDollarIcon,
  ChartBarIcon 
} from '@heroicons/react/24/outline';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

import { performanceAPI, tradesAPI, sentimentAPI } from '../services/api';

const Dashboard = () => {
  const { data: performance, isLoading: performanceLoading } = useQuery(
    'performance',
    performanceAPI.getMetrics
  );

  const { data: trades, isLoading: tradesLoading } = useQuery(
    'trades',
    tradesAPI.getAll
  );

  const { data: sentiment, isLoading: sentimentLoading } = useQuery(
    'sentiment',
    sentimentAPI.getAll
  );

  const { data: portfolioHistory, isLoading: historyLoading } = useQuery(
    'portfolio-history',
    () => performanceAPI.getHistory(30)
  );

  const isLoading = performanceLoading || tradesLoading || sentimentLoading || historyLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  const isTradesArray = Array.isArray(trades);
  const isSentimentArray = Array.isArray(sentiment);

  const recentTrades = isTradesArray ? trades.slice(0, 5) : [];
  const topSentiment = isSentimentArray ? sentiment.slice(0, 5) : [];

  // Use real portfolio history data, fallback to current balance if no history
  const chartData = Array.isArray(portfolioHistory) && portfolioHistory.length > 0 
    ? portfolioHistory.map(point => ({
        date: point.date,
        value: point.value
      }))
    : [
        { date: new Date(Date.now() - 7*24*60*60*1000).toISOString().split('T')[0], value: performance?.current_balance || 100000 },
        { date: new Date().toISOString().split('T')[0], value: performance?.current_balance || 100000 }
      ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>

      {/* Performance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CurrencyDollarIcon className="h-8 w-8 text-green-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Portfolio Value</p>
              <p className="text-2xl font-semibold text-gray-900">
                ${performance?.current_balance?.toLocaleString() || '0'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ArrowTrendingUpIcon className="h-8 w-8 text-blue-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Return</p>
              <p className={`text-2xl font-semibold ${
                (performance?.total_return || 0) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {performance?.total_return?.toFixed(2) || '0'}%
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="h-8 w-8 text-purple-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Win Rate</p>
              <p className="text-2xl font-semibold text-gray-900">
                {performance?.win_rate?.toFixed(1) || '0'}%
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ArrowTrendingDownIcon className="h-8 w-8 text-orange-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Max Drawdown</p>
              <p className="text-2xl font-semibold text-gray-900">
                {performance?.max_drawdown?.toFixed(1) || '0'}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts and Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Portfolio Performance Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Portfolio Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, 'Portfolio Value']} />
              <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Trades */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Trades</h3>
          <div className="space-y-3">
            {recentTrades.length > 0 ? (
              recentTrades.map((trade) => (
                <div key={trade.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <div>
                    <p className="font-medium text-gray-900">{trade.symbol}</p>
                    <p className="text-sm text-gray-500">
                      {trade.trade_type} {trade.quantity} shares @ ${trade.price}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className={`font-medium ${
                      trade.trade_type === 'BUY' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {trade.trade_type}
                    </p>
                    <p className="text-sm text-gray-500">
                      {new Date(trade.timestamp).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-center py-4">No recent trades</p>
            )}
          </div>
        </div>
      </div>

      {/* Sentiment Overview */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Top Sentiment Scores</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {topSentiment.map((item) => (
            <div key={item.symbol} className="p-4 border rounded-lg">
              <div className="flex justify-between items-center">
                <span className="font-medium text-gray-900">{item.symbol}</span>
                <span className={`text-sm font-medium ${
                  item.overall_sentiment > 0.2 ? 'text-green-600' :
                  item.overall_sentiment < -0.2 ? 'text-red-600' : 'text-yellow-600'
                }`}>
                  {item.overall_sentiment > 0 ? '+' : ''}{item.overall_sentiment.toFixed(3)}
                </span>
              </div>
              <div className="mt-2 text-sm text-gray-500">
                News: {item.news_count} | Social: {item.social_count}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 