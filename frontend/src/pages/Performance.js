import React from 'react';
import { useQuery } from 'react-query';
import { 
  ArrowTrendingDownIcon, 
  ChartBarIcon,
  CurrencyDollarIcon,
  ScaleIcon
} from '@heroicons/react/24/outline';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

import { performanceAPI, tradesAPI } from '../services/api';

const Performance = () => {
  const { data: performance, isLoading: performanceLoading } = useQuery('performance', performanceAPI.getMetrics);
  const { data: trades, isLoading: tradesLoading } = useQuery('trades', tradesAPI.getAll);

  const isLoading = performanceLoading || tradesLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  // Prepare chart data for portfolio performance
  const portfolioData = [
    { date: 'Start', value: 100000 },
    { date: 'Current', value: performance?.current_balance || 100000 }
  ];

  // Prepare pie chart data for trade distribution
  const tradeDistribution = [
    { name: 'Winning Trades', value: performance?.winning_trades || 0, color: '#10b981' },
    { name: 'Losing Trades', value: performance?.losing_trades || 0, color: '#ef4444' }
  ];

  // Calculate additional metrics
  const totalTrades = performance?.total_trades || 0;
  const profitFactor = performance?.average_profit && performance?.average_loss 
    ? Math.abs(performance.average_profit / performance.average_loss) 
    : 0;

  const isTradesArray = Array.isArray(trades);
  const recentTrades = isTradesArray ? trades.slice(0, 10) : [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Performance Analytics</h1>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>

      {/* Key Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CurrencyDollarIcon className="h-8 w-8 text-green-500" />
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
              <ChartBarIcon className="h-8 w-8 text-blue-500" />
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

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ScaleIcon className="h-8 w-8 text-purple-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Sharpe Ratio</p>
              <p className="text-2xl font-semibold text-gray-900">
                {performance?.sharpe_ratio?.toFixed(2) || '0'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Portfolio Performance Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Portfolio Value</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={portfolioData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, 'Portfolio Value']} />
              <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Trade Distribution Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Trade Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={tradeDistribution}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {tradeDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Performance Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trading Statistics */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Trading Statistics</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total Trades</span>
              <span className="font-semibold">{totalTrades}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Winning Trades</span>
              <span className="font-semibold text-green-600">{performance?.winning_trades || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Losing Trades</span>
              <span className="font-semibold text-red-600">{performance?.losing_trades || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Average Profit</span>
              <span className="font-semibold text-green-600">
                ${performance?.average_profit?.toFixed(2) || '0'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Average Loss</span>
              <span className="font-semibold text-red-600">
                ${performance?.average_loss?.toFixed(2) || '0'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Profit Factor</span>
              <span className="font-semibold">{profitFactor.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Financial Summary */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Financial Summary</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Initial Balance</span>
              <span className="font-semibold">$100,000</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Current Balance</span>
              <span className="font-semibold">
                ${performance?.current_balance?.toLocaleString() || '100,000'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total P&L</span>
              <span className={`font-semibold ${
                (performance?.total_profit_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                ${performance?.total_profit_loss?.toFixed(2) || '0'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total Return</span>
              <span className={`font-semibold ${
                (performance?.total_return || 0) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {performance?.total_return?.toFixed(2) || '0'}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Max Drawdown</span>
              <span className="font-semibold text-red-600">
                {performance?.max_drawdown?.toFixed(1) || '0'}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Sharpe Ratio</span>
              <span className="font-semibold">{performance?.sharpe_ratio?.toFixed(2) || '0'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Performance */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Trading Activity</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recentTrades.map((trade) => (
                <tr key={trade.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(trade.timestamp).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {trade.symbol}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      trade.trade_type === 'BUY' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {trade.trade_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={trade.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {trade.profit_loss ? `$${trade.profit_loss.toFixed(2)}` : '-'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      trade.status === 'OPEN' 
                        ? 'bg-yellow-100 text-yellow-800'
                        : trade.status === 'CLOSED'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {trade.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Performance; 