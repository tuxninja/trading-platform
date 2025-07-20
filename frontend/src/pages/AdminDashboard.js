import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import {
  UsersIcon,
  ServerIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CpuChipIcon,
  DatabaseIcon
} from '@heroicons/react/24/outline';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

import { adminAPI } from '../services/api';

const AdminDashboard = () => {
  const { data: dashboardData, isLoading, error } = useQuery(
    'admin-dashboard',
    adminAPI.getDashboard,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
      onError: (error) => {
        console.error('Admin dashboard error:', error);
      }
    }
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <h3 className="text-lg font-medium text-red-800">Admin Dashboard Error</h3>
        <p className="text-red-700">Failed to load dashboard data. Please check your admin permissions.</p>
      </div>
    );
  }

  const {
    user_stats = {},
    system_health = {},
    platform_metrics = {},
    recent_activity = []
  } = dashboardData || {};

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>

      {/* System Health Alert */}
      {system_health.alerts?.unresolved_count > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-red-800 font-medium">
              {system_health.alerts.unresolved_count} unresolved system alerts
            </span>
          </div>
        </div>
      )}

      {/* User Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <UsersIcon className="h-8 w-8 text-blue-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Users</p>
              <p className="text-2xl font-semibold text-gray-900">
                {user_stats.total_users?.toLocaleString() || '0'}
              </p>
              <p className="text-xs text-green-600">
                +{user_stats.new_users_30d || 0} this month
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="h-8 w-8 text-green-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Daily Active</p>
              <p className="text-2xl font-semibold text-gray-900">
                {user_stats.daily_active_users || '0'}
              </p>
              <p className="text-xs text-gray-600">
                {user_stats.weekly_active_users || 0} weekly
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CpuChipIcon className="h-8 w-8 text-purple-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">CPU Usage</p>
              <p className="text-2xl font-semibold text-gray-900">
                {system_health.system_resources?.cpu_percent?.toFixed(1) || '0'}%
              </p>
              <p className="text-xs text-gray-600">
                {system_health.system_resources?.memory_percent?.toFixed(1) || '0'}% memory
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <DatabaseIcon className="h-8 w-8 text-orange-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Database</p>
              <p className="text-2xl font-semibold text-gray-900">
                {system_health.database?.status === 'healthy' ? 'Healthy' : 'Error'}
              </p>
              <p className="text-xs text-gray-600">
                {system_health.database?.response_time || 'N/A'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Platform Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Trading Overview</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Total Trades</span>
              <span className="font-semibold">{platform_metrics.trades?.total || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Open Positions</span>
              <span className="font-semibold">{platform_metrics.trades?.open || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Total Portfolio Value</span>
              <span className="font-semibold">
                ${platform_metrics.trades?.total_portfolio_value?.toLocaleString() || '0'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Daily Trades</span>
              <span className="font-semibold">{platform_metrics.trades?.daily || 0}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Top Trading Symbols</h3>
          <div className="space-y-2">
            {platform_metrics.top_symbols?.slice(0, 8).map((symbol, index) => (
              <div key={symbol.symbol} className="flex justify-between items-center">
                <div className="flex items-center">
                  <span className="text-sm text-gray-500 w-6">#{index + 1}</span>
                  <span className="font-medium">{symbol.symbol}</span>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold">{symbol.trade_count} trades</div>
                  <div className="text-xs text-gray-500">
                    ${symbol.total_value?.toLocaleString()}
                  </div>
                </div>
              </div>
            )) || (
              <p className="text-gray-500 text-center">No trading data available</p>
            )}
          </div>
        </div>
      </div>

      {/* System Resources Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">System Resources</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="relative w-20 h-20 mx-auto mb-2">
              <svg className="w-20 h-20 transform -rotate-90">
                <circle
                  cx="40"
                  cy="40"
                  r="36"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="transparent"
                  className="text-gray-200"
                />
                <circle
                  cx="40"
                  cy="40"
                  r="36"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="transparent"
                  strokeDasharray={`${2 * Math.PI * 36}`}
                  strokeDashoffset={`${2 * Math.PI * 36 * (1 - (system_health.system_resources?.cpu_percent || 0) / 100)}`}
                  className="text-blue-500"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-semibold">
                  {system_health.system_resources?.cpu_percent?.toFixed(0) || '0'}%
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600">CPU Usage</p>
          </div>

          <div className="text-center">
            <div className="relative w-20 h-20 mx-auto mb-2">
              <svg className="w-20 h-20 transform -rotate-90">
                <circle
                  cx="40"
                  cy="40"
                  r="36"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="transparent"
                  className="text-gray-200"
                />
                <circle
                  cx="40"
                  cy="40"
                  r="36"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="transparent"
                  strokeDasharray={`${2 * Math.PI * 36}`}
                  strokeDashoffset={`${2 * Math.PI * 36 * (1 - (system_health.system_resources?.memory_percent || 0) / 100)}`}
                  className="text-green-500"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-semibold">
                  {system_health.system_resources?.memory_percent?.toFixed(0) || '0'}%
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600">Memory</p>
            <p className="text-xs text-gray-500">
              {system_health.system_resources?.memory_available || 'N/A'} free
            </p>
          </div>

          <div className="text-center">
            <div className="relative w-20 h-20 mx-auto mb-2">
              <svg className="w-20 h-20 transform -rotate-90">
                <circle
                  cx="40"
                  cy="40"
                  r="36"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="transparent"
                  className="text-gray-200"
                />
                <circle
                  cx="40"
                  cy="40"
                  r="36"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="transparent"
                  strokeDasharray={`${2 * Math.PI * 36}`}
                  strokeDashoffset={`${2 * Math.PI * 36 * (1 - (system_health.system_resources?.disk_percent || 0) / 100)}`}
                  className="text-orange-500"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-semibold">
                  {system_health.system_resources?.disk_percent?.toFixed(0) || '0'}%
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600">Disk</p>
            <p className="text-xs text-gray-500">
              {system_health.system_resources?.disk_free || 'N/A'} free
            </p>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {recent_activity.length > 0 ? (
            recent_activity.map((activity) => (
              <div key={activity.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <div>
                  <p className="font-medium text-gray-900">{activity.action}</p>
                  <p className="text-sm text-gray-500">
                    User ID: {activity.user_id} • {activity.endpoint}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">
                    {new Date(activity.timestamp).toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500">{activity.ip_address}</p>
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-500 text-center py-4">No recent activity</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;