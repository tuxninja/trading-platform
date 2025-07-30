import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  AcademicCapIcon,
  ChartBarIcon,
  LightBulbIcon,
  CogIcon,
  ArrowTrendingUpIcon,
  ExclamationTriangleIcon,
  PlayIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const AdaptiveLearning = () => {
  const queryClient = useQueryClient();
  const [selectedTab, setSelectedTab] = useState('overview');

  // API calls for learning data
  const { data: dashboardData, isLoading: dashboardLoading } = useQuery(
    'learning-dashboard',
    () => fetch('/api/learning/dashboard').then(res => res.json()),
    { refetchInterval: 60000 } // Refresh every minute
  );

  const { data: patterns, isLoading: patternsLoading } = useQuery(
    'learning-patterns',
    () => fetch('/api/learning/patterns?min_success_rate=0.6&limit=20').then(res => res.json())
  );

  const { data: insights, isLoading: insightsLoading } = useQuery(
    'learning-insights',
    () => fetch('/api/learning/insights?min_confidence=0.7&limit=10').then(res => res.json())
  );

  const { data: adjustments, isLoading: adjustmentsLoading } = useQuery(
    'learning-adjustments',
    () => fetch('/api/learning/adjustments?days_back=30').then(res => res.json())
  );

  const { data: performanceEvolution, isLoading: evolutionLoading } = useQuery(
    'performance-evolution',
    () => fetch('/api/learning/performance-evolution?days_back=60').then(res => res.json())
  );

  // Mutation for running learning analysis
  const runAnalysisMutation = useMutation(
    () => fetch('/api/learning/analyze', { method: 'POST' }).then(res => res.json()),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('learning-dashboard');
        queryClient.invalidateQueries('learning-patterns');
        queryClient.invalidateQueries('learning-insights');
        queryClient.invalidateQueries('learning-adjustments');
      }
    }
  );

  const isLoading = dashboardLoading || patternsLoading || insightsLoading || adjustmentsLoading || evolutionLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Adaptive Learning System</h1>
          <p className="text-gray-600 mt-1">AI-powered strategy optimization that learns from every trade</p>
        </div>
        <button
          onClick={() => runAnalysisMutation.mutate()}
          disabled={runAnalysisMutation.isLoading}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {runAnalysisMutation.isLoading ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          ) : (
            <PlayIcon className="h-5 w-5 mr-2" />
          )}
          Run Analysis Now
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <AcademicCapIcon className="h-8 w-8 text-blue-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Patterns Discovered</p>
              <p className="text-2xl font-semibold text-gray-900">
                {dashboardData?.patterns_discovered_30d || 0}
              </p>
              <p className="text-xs text-gray-500">
                Last 30 days
                {dashboardData?.total_patterns_ever === 0 && (
                  <span className="text-orange-500 ml-1">• No learning data yet</span>
                )}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CogIcon className="h-8 w-8 text-green-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Parameter Adjustments</p>
              <p className="text-2xl font-semibold text-gray-900">
                {dashboardData?.parameter_adjustments_30d || 0}
              </p>
              <p className="text-xs text-gray-500">
                Strategy optimizations
                {!dashboardData?.learning_system_active && (
                  <span className="text-orange-500 ml-1">• Learning inactive</span>
                )}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <LightBulbIcon className="h-8 w-8 text-yellow-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Insights</p>
              <p className="text-2xl font-semibold text-gray-900">
                {dashboardData?.active_insights || 0}
              </p>
              <p className="text-xs text-gray-500">Market discoveries</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ArrowTrendingUpIcon className="h-8 w-8 text-purple-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Current Win Rate</p>
              <p className="text-2xl font-semibold text-gray-900">
                {((dashboardData?.current_win_rate || 0) * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500">Latest performance</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: ChartBarIcon },
            { id: 'patterns', name: 'Trade Patterns', icon: AcademicCapIcon },
            { id: 'insights', name: 'Market Insights', icon: LightBulbIcon },
            { id: 'adjustments', name: 'Strategy Adjustments', icon: CogIcon }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedTab(tab.id)}
              className={`${
                selectedTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center`}
            >
              <tab.icon className="h-5 w-5 mr-2" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {selectedTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Performance Evolution Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Evolution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceEvolution?.rolling_performance || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip 
                  formatter={(value, name) => [
                    name === 'win_rate' ? `${(value * 100).toFixed(1)}%` : `$${value.toFixed(2)}`,
                    name === 'win_rate' ? 'Win Rate' : 'Avg Profit'
                  ]} 
                />
                <Line type="monotone" dataKey="win_rate" stroke="#3b82f6" strokeWidth={2} />
                <Line type="monotone" dataKey="avg_profit" stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Recent Adjustments */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Strategy Adjustments</h3>
            <div className="space-y-3">
              {dashboardData?.recent_adjustments?.length > 0 ? (
                dashboardData.recent_adjustments.map((adj, index) => (
                  <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-gray-900 capitalize">
                          {adj.parameter.replace('_', ' ')}
                        </p>
                        <p className="text-sm text-gray-600">{adj.reason}</p>
                        <p className="text-xs text-gray-500">
                          {adj.old_value} → {adj.new_value} on {adj.date}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-4">No recent adjustments</p>
              )}
            </div>
          </div>

          {/* Top Insights */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Top Market Insights</h3>
            <div className="space-y-3">
              {dashboardData?.top_insights?.length > 0 ? (
                dashboardData.top_insights.map((insight, index) => (
                  <div key={index} className="p-3 bg-yellow-50 rounded-md">
                    <div className="flex">
                      <LightBulbIcon className="h-5 w-5 text-yellow-400 mr-3 mt-0.5" />
                      <div>
                        <h4 className="text-sm font-medium text-yellow-800">{insight.title}</h4>
                        <p className="text-sm text-yellow-700 mt-1">{insight.description}</p>
                        <div className="mt-2 flex items-center text-xs text-yellow-600">
                          <span className="mr-3">Confidence: {(insight.confidence * 100).toFixed(0)}%</span>
                          <span>Impact: {insight.impact.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-4">No insights discovered yet</p>
              )}
            </div>
          </div>

          {/* Learning Status */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Learning System Status</h3>
            <div className="space-y-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-400 rounded-full mr-3"></div>
                <span className="text-sm">Pattern Recognition: Active</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-400 rounded-full mr-3"></div>
                <span className="text-sm">Parameter Optimization: Active</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-400 rounded-full mr-3"></div>
                <span className="text-sm">Market Analysis: Learning</span>
              </div>
              <div className="flex items-center">
                <ClockIcon className="h-4 w-4 text-gray-400 mr-3" />
                <span className="text-sm text-gray-600">Next Analysis: Daily at 4:30 PM</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedTab === 'patterns' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Discovered Trade Patterns</h3>
            <p className="text-sm text-gray-600">Patterns extracted from successful and unsuccessful trades</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pattern</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Success Rate</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg P&L</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Occurrences</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sector</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {patterns?.length > 0 ? (
                  patterns.map((pattern) => (
                    <tr key={pattern.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          pattern.pattern_type.includes('SUCCESSFUL') ? 
                          'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {pattern.pattern_type.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {pattern.symbol}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {(pattern.success_rate * 100).toFixed(1)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <span className={pattern.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}>
                          ${pattern.profit_loss.toFixed(2)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {pattern.occurrence_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {pattern.sector}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center">
                      <div className="flex flex-col items-center">
                        <AcademicCapIcon className="h-12 w-12 text-gray-400 mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No Trade Patterns Yet</h3>
                        <p className="text-gray-500 max-w-md">
                          The learning system needs more completed trades to identify successful patterns. 
                          Once you have more trading history, patterns will automatically appear here.
                        </p>
                        {dashboardData?.patterns_discovered_30d > 0 && (
                          <p className="text-orange-600 text-sm mt-2 font-medium">
                            Data inconsistency detected: Dashboard shows {dashboardData.patterns_discovered_30d} patterns but none visible here. 
                            Try refreshing the page or check backend logs.
                          </p>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {selectedTab === 'insights' && (
        <div className="space-y-4">
          {insights?.length > 0 ? (
            insights.map((insight) => (
              <div key={insight.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-start justify-between">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <LightBulbIcon className="h-6 w-6 text-yellow-500" />
                    </div>
                    <div className="ml-4">
                      <h3 className="text-lg font-medium text-gray-900">{insight.title}</h3>
                      <p className="text-gray-600 mt-1">{insight.description}</p>
                      <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500">
                        <span>Type: {insight.insight_type.replace('_', ' ')}</span>
                        <span>Confidence: {(insight.confidence_score * 100).toFixed(0)}%</span>
                        <span>Impact: {insight.impact_magnitude.toFixed(2)}</span>
                        <span>Applied: {insight.times_applied} times</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      insight.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {insight.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <LightBulbIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Insights Yet</h3>
              <p className="text-gray-600">The learning system is analyzing trade patterns to discover market insights.</p>
            </div>
          )}
        </div>
      )}

      {selectedTab === 'adjustments' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Strategy Parameter Adjustments</h3>
            <p className="text-sm text-gray-600">Automatic optimizations made by the learning system</p>
          </div>
          <div className="divide-y divide-gray-200">
            {adjustments?.length > 0 ? (
              adjustments.map((adj) => (
                <div key={adj.id} className="p-6">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h4 className="text-lg font-medium text-gray-900 capitalize">
                        {adj.parameter_name.replace('_', ' ')} Adjustment
                      </h4>
                      <p className="text-gray-600 mt-1">{adj.adjustment_reason}</p>
                      <div className="mt-3 grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Previous Value:</span>
                          <span className="ml-2 font-medium">{adj.old_value}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">New Value:</span>
                          <span className="ml-2 font-medium">{adj.new_value}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Confidence:</span>
                          <span className="ml-2 font-medium">{(adj.confidence_level * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                    <div className="ml-6 text-right">
                      <div className="text-sm text-gray-500">
                        {new Date(adj.adjustment_date).toLocaleDateString()}
                      </div>
                      {adj.is_successful !== null && (
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full mt-2 ${
                          adj.is_successful ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {adj.is_successful ? 'Successful' : 'Unsuccessful'}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-6 text-center text-gray-500">
                No parameter adjustments yet. The system is learning from trade performance.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdaptiveLearning;