import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-hot-toast';
import { 
  PlayIcon,
  EyeIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { watchlistAPI } from '../services/api';

const ContinuousMonitoringStatus = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const queryClient = useQueryClient();

  // Fetch monitoring status
  const { data: monitoringStatus, isLoading, error } = useQuery(
    'monitoring-status',
    () => watchlistAPI.getMonitoringStatus(),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
      retry: 1,
      onError: (error) => {
        console.error('Monitoring status error:', error);
      }
    }
  );

  // Run monitoring manually
  const runMonitoringMutation = useMutation(
    () => watchlistAPI.runMonitoring(),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries('monitoring-status');
        queryClient.invalidateQueries('watchlist');
        toast.success(
          `Monitoring complete: ${data.monitored_count} stocks, ${data.sentiment_updates} updates, ${data.price_alerts} alerts`
        );
      },
      onError: (error) => {
        toast.error(error.message || 'Failed to run monitoring');
      }
    }
  );

  const formatTimeAgo = (isoString) => {
    if (!isoString) return 'Never';
    
    const date = new Date(isoString);
    const now = new Date();
    const diffMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const getStatusColor = (ageMinutes) => {
    if (!ageMinutes) return 'text-gray-500';
    if (ageMinutes < 30) return 'text-green-600';
    if (ageMinutes < 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <div className="animate-pulse flex space-x-4">
          <div className="rounded-full bg-gray-200 h-10 w-10"></div>
          <div className="flex-1 space-y-2 py-1">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="text-red-800 text-sm font-medium">
          Failed to load monitoring status
        </div>
        <div className="text-red-600 text-sm mt-1">
          {error.message}
        </div>
      </div>
    );
  }

  const status = monitoringStatus || {};

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <EyeIcon className="h-8 w-8 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                Continuous Monitoring
              </h3>
              <p className="text-sm text-gray-500">
                Automated sentiment analysis and price alerts
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => runMonitoringMutation.mutate()}
              disabled={runMonitoringMutation.isLoading}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {runMonitoringMutation.isLoading ? (
                <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <PlayIcon className="h-4 w-4 mr-2" />
              )}
              {runMonitoringMutation.isLoading ? 'Running...' : 'Run Now'}
            </button>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              {isExpanded ? 'Hide Details' : 'Show Details'}
            </button>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {status.total_active_stocks || 0}
            </div>
            <div className="text-sm text-gray-500">Active Stocks</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {status.sentiment_monitoring_enabled || 0}
            </div>
            <div className="text-sm text-gray-500">Sentiment Monitoring</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {status.auto_trading_enabled || 0}
            </div>
            <div className="text-sm text-gray-500">Auto Trading</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-500 flex items-center justify-center">
              <ClockIcon className="h-4 w-4 mr-1" />
              Last Run
            </div>
            <div className="text-sm font-medium text-gray-900">
              {formatTimeAgo(status.last_monitoring_cycle)}
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Stock Status */}
      {isExpanded && (
        <div className="border-t border-gray-200">
          <div className="p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">
              Stock Monitoring Status
            </h4>
            
            {status.stocks && status.stocks.length > 0 ? (
              <div className="space-y-3">
                {status.stocks.map((stock) => (
                  <div
                    key={stock.symbol}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <div>
                        <div className="font-medium text-sm text-gray-900">
                          {stock.symbol}
                        </div>
                        <div className="text-xs text-gray-500">
                          {stock.company_name}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4 text-xs">
                      {/* Sentiment Status */}
                      <div className="text-center">
                        <div className="flex items-center justify-center">
                          {stock.sentiment_monitoring ? (
                            <CheckCircleIcon className="h-4 w-4 text-green-500" />
                          ) : (
                            <XCircleIcon className="h-4 w-4 text-gray-400" />
                          )}
                        </div>
                        <div className="text-gray-500 mt-1">Sentiment</div>
                      </div>
                      
                      {/* Auto Trading Status */}
                      <div className="text-center">
                        <div className="flex items-center justify-center">
                          {stock.auto_trading ? (
                            <CheckCircleIcon className="h-4 w-4 text-blue-500" />
                          ) : (
                            <XCircleIcon className="h-4 w-4 text-gray-400" />
                          )}
                        </div>
                        <div className="text-gray-500 mt-1">Trading</div>
                      </div>
                      
                      {/* Latest Sentiment */}
                      {stock.latest_sentiment !== null && (
                        <div className="text-center">
                          <div className={`font-medium ${
                            stock.latest_sentiment > 0.2 ? 'text-green-600' :
                            stock.latest_sentiment < -0.2 ? 'text-red-600' :
                            'text-yellow-600'
                          }`}>
                            {stock.latest_sentiment > 0 ? '+' : ''}{stock.latest_sentiment.toFixed(3)}
                          </div>
                          <div className="text-gray-500 mt-1">Sentiment</div>
                        </div>
                      )}
                      
                      {/* Last Monitored */}
                      <div className="text-center">
                        <div className={`font-medium ${getStatusColor(stock.sentiment_age_minutes)}`}>
                          {stock.sentiment_age_minutes ? `${stock.sentiment_age_minutes}m` : 'Never'}
                        </div>
                        <div className="text-gray-500 mt-1">Age</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 text-gray-500">
                <EyeIcon className="mx-auto h-12 w-12 text-gray-400" />
                <div className="mt-2 text-sm">
                  No stocks are being monitored
                </div>
                <div className="text-xs mt-1">
                  Add stocks to your watchlist to enable monitoring
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ContinuousMonitoringStatus;