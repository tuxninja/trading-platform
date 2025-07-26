import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  CurrencyDollarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  CogIcon,
  BellIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

const TradingControl = () => {
  const queryClient = useQueryClient();
  const [selectedTab, setSelectedTab] = useState('overview');
  const [showSettings, setShowSettings] = useState(false);

  // API calls for trading control data
  const { data: capitalStatus, isLoading: capitalLoading } = useQuery(
    'capital-status',
    () => fetch('/api/trading/capital-status').then(res => res.json()),
    { refetchInterval: 30000 } // Refresh every 30 seconds
  );

  const { data: pendingSignals, isLoading: signalsLoading } = useQuery(
    'pending-signals', 
    () => fetch('/api/trading/signals/pending').then(res => res.json()),
    { refetchInterval: 10000 } // Refresh every 10 seconds
  );

  const { data: riskAssessment, isLoading: riskLoading } = useQuery(
    'risk-assessment',
    () => fetch('/api/trading/risk-assessment').then(res => res.json()),
    { refetchInterval: 60000 } // Refresh every minute
  );

  const { data: notifications, isLoading: notificationsLoading } = useQuery(
    'notifications',
    () => fetch('/api/trading/notifications').then(res => res.json()),
    { refetchInterval: 15000 } // Refresh every 15 seconds
  );

  const { data: tradingSettings } = useQuery(
    'trading-settings',
    () => fetch('/api/trading/settings').then(res => res.json())
  );

  // Mutation for approving/rejecting signals
  const approveSignalMutation = useMutation(
    (approval) => fetch('/api/trading/signals/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(approval)
    }).then(res => res.json()),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('pending-signals');
        queryClient.invalidateQueries('notifications');
      }
    }
  );

  const handleApproveSignal = (signalId, approved, overrides = {}) => {
    approveSignalMutation.mutate({
      signal_id: signalId,
      approved,
      ...overrides
    });
  };

  if (capitalLoading || signalsLoading || riskLoading || notificationsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  const unreadNotifications = notifications?.filter(n => !n.read) || [];
  const highPriorityNotifications = notifications?.filter(n => n.priority === 'HIGH' || n.priority === 'URGENT') || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Trading Control Center</h1>
          <p className="text-gray-600 mt-1">Manage your automated trading with full transparency and control</p>
        </div>
        <div className="flex space-x-4">
          <button
            onClick={() => setShowSettings(true)}
            className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            <CogIcon className="h-5 w-5 mr-2" />
            Settings
          </button>
          <div className="relative">
            <BellIcon className="h-8 w-8 text-gray-600" />
            {unreadNotifications.length > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                {unreadNotifications.length}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* High Priority Alerts */}
      {highPriorityNotifications.length > 0 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                High Priority Alerts ({highPriorityNotifications.length})
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                {highPriorityNotifications.slice(0, 3).map(notification => (
                  <p key={notification.id}>{notification.title}: {notification.message}</p>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: ChartBarIcon },
            { id: 'signals', name: `Pending Signals (${pendingSignals?.length || 0})`, icon: ExclamationTriangleIcon },
            { id: 'capital', name: 'Capital Management', icon: CurrencyDollarIcon },
            { id: 'risk', name: 'Risk Assessment', icon: ExclamationTriangleIcon }
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
          {/* Quick Stats */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Portfolio Status</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Portfolio Value:</span>
                <span className="font-semibold">${capitalStatus?.total_portfolio_value?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Available for Trading:</span>
                <span className="font-semibold text-green-600">${capitalStatus?.cash_available_for_new_trades?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Open Positions:</span>
                <span className="font-semibold">{capitalStatus?.open_positions_count} / {capitalStatus?.max_positions_limit}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Largest Position:</span>
                <span className="font-semibold">{capitalStatus?.largest_position_percent?.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* Trading Mode */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Trading Mode</h3>
            <div className="space-y-3">
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-3 ${
                  tradingSettings?.trading_mode === 'AUTO' ? 'bg-green-400' :
                  tradingSettings?.trading_mode === 'SEMI_AUTO' ? 'bg-yellow-400' : 'bg-gray-400'
                }`}></div>
                <span className="font-medium">
                  {tradingSettings?.trading_mode === 'AUTO' ? 'Fully Automated' :
                   tradingSettings?.trading_mode === 'SEMI_AUTO' ? 'Semi-Automated (Approval Required)' : 'Manual Only'}
                </span>
              </div>
              <p className="text-sm text-gray-600">
                {tradingSettings?.trading_mode === 'AUTO' ? 'Trades execute automatically based on signals' :
                 tradingSettings?.trading_mode === 'SEMI_AUTO' ? 'Trades require your approval before execution' : 'No automated trading'}
              </p>
            </div>
          </div>
        </div>
      )}

      {selectedTab === 'signals' && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Pending Trade Signals</h3>
            <p className="text-sm text-gray-600">Review and approve trade signals before execution</p>
          </div>
          <div className="divide-y divide-gray-200">
            {pendingSignals?.length > 0 ? (
              pendingSignals.map((signal) => (
                <div key={signal.signal_id} className="p-6">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span className="text-lg font-semibold">{signal.symbol}</span>
                        <span className={`ml-3 px-2 py-1 text-xs font-medium rounded-full ${
                          signal.action === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {signal.action}
                        </span>
                        <span className="ml-2 text-sm text-gray-500">
                          Confidence: {(signal.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-gray-600 mb-2">{signal.reasoning}</p>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Quantity:</span> {signal.quantity} shares
                        </div>
                        <div>
                          <span className="text-gray-500">Estimated Price:</span> ${signal.estimated_price.toFixed(2)}
                        </div>
                        <div>
                          <span className="text-gray-500">Total Value:</span> ${signal.estimated_total.toLocaleString()}
                        </div>
                        <div>
                          <span className="text-gray-500">Risk Level:</span> {signal.risk_assessment?.risk_level}
                        </div>
                      </div>
                      
                      {/* Capital Impact */}
                      <div className="mt-3 p-3 bg-gray-50 rounded-md">
                        <h5 className="text-sm font-medium text-gray-700">Capital Impact</h5>
                        <div className="text-xs text-gray-600 mt-1">
                          Available Before: ${signal.capital_impact?.available_before?.toLocaleString()} → 
                          After: ${signal.capital_impact?.available_after?.toLocaleString()}
                        </div>
                      </div>
                    </div>
                    
                    <div className="ml-6 flex space-x-2">
                      <button
                        onClick={() => handleApproveSignal(signal.signal_id, true)}
                        className="flex items-center px-3 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700"
                        disabled={approveSignalMutation.isLoading}
                      >
                        <CheckCircleIcon className="h-4 w-4 mr-1" />
                        Approve
                      </button>
                      <button
                        onClick={() => handleApproveSignal(signal.signal_id, false)}
                        className="flex items-center px-3 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700"
                        disabled={approveSignalMutation.isLoading}
                      >
                        <XCircleIcon className="h-4 w-4 mr-1" />
                        Reject
                      </button>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-6 text-center text-gray-500">
                No pending signals. The system will generate new signals during market hours.
              </div>
            )}
          </div>
        </div>
      )}

      {selectedTab === 'capital' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Capital Allocation */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Capital Allocation</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm">
                  <span>Investment Capacity</span>
                  <span>{((capitalStatus?.current_investment_amount / capitalStatus?.max_total_investment_limit) * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${(capitalStatus?.current_investment_amount / capitalStatus?.max_total_investment_limit) * 100}%` }}
                  ></div>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  ${capitalStatus?.current_investment_amount?.toLocaleString()} / ${capitalStatus?.max_total_investment_limit?.toLocaleString()}
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm">
                  <span>Position Slots Used</span>
                  <span>{capitalStatus?.open_positions_count} / {capitalStatus?.max_positions_limit}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                  <div 
                    className="bg-green-600 h-2 rounded-full" 
                    style={{ width: `${(capitalStatus?.open_positions_count / capitalStatus?.max_positions_limit) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* Sector Allocation */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Sector Allocation</h3>
            <div className="space-y-3">
              {Object.entries(capitalStatus?.sector_allocations || {}).map(([sector, percentage]) => (
                <div key={sector}>
                  <div className="flex justify-between text-sm">
                    <span>{sector}</span>
                    <span>{percentage.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                    <div 
                      className="bg-purple-600 h-2 rounded-full" 
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {selectedTab === 'risk' && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-medium text-gray-900">Risk Assessment</h3>
            <div className="flex items-center">
              <span className="text-sm text-gray-500 mr-2">Risk Score:</span>
              <span className={`text-lg font-bold px-3 py-1 rounded-full ${
                riskAssessment?.overall_risk_score <= 3 ? 'bg-green-100 text-green-800' :
                riskAssessment?.overall_risk_score <= 6 ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {riskAssessment?.overall_risk_score}/10
              </span>
            </div>
          </div>

          {/* Warnings */}
          {riskAssessment?.warnings?.length > 0 && (
            <div className="mb-6">
              <h4 className="text-md font-medium text-red-800 mb-3">⚠️ Risk Warnings</h4>
              <ul className="space-y-2">
                {riskAssessment.warnings.map((warning, index) => (
                  <li key={index} className="text-red-700 bg-red-50 p-3 rounded-md">{warning}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {riskAssessment?.recommendations?.length > 0 && (
            <div>
              <h4 className="text-md font-medium text-blue-800 mb-3">💡 Recommendations</h4>
              <ul className="space-y-2">
                {riskAssessment.recommendations.map((rec, index) => (
                  <li key={index} className="text-blue-700 bg-blue-50 p-3 rounded-md">{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TradingControl;