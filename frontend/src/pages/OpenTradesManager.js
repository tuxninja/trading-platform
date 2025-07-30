import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-hot-toast';
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  ExclamationTriangleIcon,
  XMarkIcon,
  CheckIcon,
  ClockIcon,
  InformationCircleIcon,
  ArrowRightIcon,
  BanknotesIcon
} from '@heroicons/react/24/outline';
import { tradesAPI, performanceAPI } from '../services/api';

const OpenTradesManager = () => {
  const [selectedTrade, setSelectedTrade] = useState(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [actionType, setActionType] = useState(null); // 'close' or 'cancel'
  const [closePrice, setClosePrice] = useState('');
  const queryClient = useQueryClient();

  // Fetch all trades
  const { data: allTrades, isLoading: tradesLoading, isError: tradesError } = useQuery(
    'trades', 
    tradesAPI.getAll,
    { refetchInterval: 30000 } // Refresh every 30 seconds
  );

  // Fetch portfolio metrics for capital allocation info
  const { data: portfolioMetrics } = useQuery(
    'portfolio-metrics',
    performanceAPI.getMetrics,
    { refetchInterval: 60000 } // Refresh every minute
  );

  // Filter open trades
  const openTrades = allTrades?.filter(trade => trade.status === 'OPEN') || [];
  const closedTrades = allTrades?.filter(trade => trade.status === 'CLOSED') || [];
  
  // Calculate capital allocation
  const totalCapitalAllocated = openTrades.reduce((sum, trade) => sum + (trade.total_value || 0), 0);
  const availableCapital = (portfolioMetrics?.current_balance || 0) - totalCapitalAllocated;

  // Close trade mutation
  const closeTradesMutation = useMutation(
    ({ tradeId, closePrice }) => tradesAPI.close(tradeId, closePrice),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('trades');
        queryClient.invalidateQueries('portfolio-metrics');
        toast.success('Trade closed successfully');
        setShowConfirmModal(false);
        setSelectedTrade(null);
        setClosePrice('');
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to close trade');
      }
    }
  );

  // Cancel trade mutation  
  const cancelTradeMutation = useMutation(
    (tradeId) => tradesAPI.delete(tradeId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('trades');
        queryClient.invalidateQueries('portfolio-metrics');
        toast.success('Trade cancelled successfully');
        setShowConfirmModal(false);
        setSelectedTrade(null);
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to cancel trade');
      }
    }
  );

  const handleTradeAction = (trade, action) => {
    setSelectedTrade(trade);
    setActionType(action);
    setClosePrice(trade.price?.toString() || '');
    setShowConfirmModal(true);
  };

  const confirmAction = () => {
    if (actionType === 'close') {
      const price = closePrice ? parseFloat(closePrice) : null;
      closeTradesMutation.mutate({ tradeId: selectedTrade.id, closePrice: price });
    } else if (actionType === 'cancel') {
      cancelTradeMutation.mutate(selectedTrade.id);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'OPEN': return 'text-yellow-600 bg-yellow-100';
      case 'CLOSED': return 'text-green-600 bg-green-100';
      case 'CANCELLED': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getDaysOpen = (timestamp) => {
    const tradeDate = new Date(timestamp);
    const now = new Date();
    const diffTime = Math.abs(now - tradeDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  if (tradesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (tradesError) {
    return (
      <div className="text-center text-red-600">
        <ExclamationTriangleIcon className="h-12 w-12 mx-auto mb-4" />
        Error loading trades data. Please try again.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Open Trades Manager</h1>
        <p className="text-gray-600 mt-1">
          Manage your open positions and monitor capital allocation
        </p>
      </div>

      {/* Capital Allocation Overview */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <BanknotesIcon className="h-5 w-5 mr-2" />
          Capital Allocation Overview
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-sm text-blue-700">Total Portfolio Value</div>
            <div className="text-2xl font-bold text-blue-900">
              {formatCurrency(portfolioMetrics?.current_balance)}
            </div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <div className="text-sm text-yellow-700">Capital Allocated (Open)</div>
            <div className="text-2xl font-bold text-yellow-900">
              {formatCurrency(totalCapitalAllocated)}
            </div>
            <div className="text-sm text-yellow-600">
              {openTrades.length} open position{openTrades.length !== 1 ? 's' : ''}
            </div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-sm text-green-700">Available Capital</div>
            <div className="text-2xl font-bold text-green-900">
              {formatCurrency(availableCapital)}
            </div>
            <div className="text-sm text-green-600">
              {availableCapital < 1000 ? 'Limited availability' : 'Available for new trades'}
            </div>
          </div>
        </div>
      </div>

      {/* Open Trades Warning */}
      {openTrades.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex">
            <InformationCircleIcon className="h-5 w-5 text-yellow-600 mr-2 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800">
                Active Open Positions
              </h3>
              <p className="text-sm text-yellow-700 mt-1">
                You have {openTrades.length} open trades with {formatCurrency(totalCapitalAllocated)} allocated. 
                Consider closing or cancelling trades that have been open for extended periods to free up capital.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Open Trades Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900 flex items-center">
            <ClockIcon className="h-5 w-5 mr-2" />
            Open Trades ({openTrades.length})
          </h2>
        </div>
        
        {openTrades.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <ChartBarIcon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p>No open trades found. All capital is available for new trades.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Value
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Days Open
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Strategy
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {openTrades.map((trade) => (
                  <tr key={trade.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{trade.symbol}</div>
                      <div className="text-sm text-gray-500">ID: {trade.id}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        trade.trade_type === 'BUY' ? 'text-green-800 bg-green-100' : 'text-red-800 bg-red-100'
                      }`}>
                        {trade.trade_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {trade.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(trade.price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                      {formatCurrency(trade.total_value)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <span className={`${getDaysOpen(trade.timestamp) > 7 ? 'text-red-600 font-semibold' : 'text-gray-600'}`}>
                        {getDaysOpen(trade.timestamp)} days
                      </span>
                      {getDaysOpen(trade.timestamp) > 7 && (
                        <ExclamationTriangleIcon className="h-4 w-4 text-red-500 inline ml-1" />
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {trade.strategy || 'Manual'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => handleTradeAction(trade, 'close')}
                        className="text-green-600 hover:text-green-900 bg-green-100 hover:bg-green-200 px-3 py-1 rounded-md"
                      >
                        Close
                      </button>
                      <button
                        onClick={() => handleTradeAction(trade, 'cancel')}
                        className="text-red-600 hover:text-red-900 bg-red-100 hover:bg-red-200 px-3 py-1 rounded-md"
                      >
                        Cancel
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Closed Trades (for reference) */}
      {closedTrades.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900 flex items-center">
              <CheckIcon className="h-5 w-5 mr-2" />
              Recent Closed Trades (Last 10)
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
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
                    Close Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Strategy
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {closedTrades.slice(-10).reverse().map((trade) => (
                  <tr key={trade.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">
                      {trade.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        trade.trade_type === 'BUY' ? 'text-green-800 bg-green-100' : 'text-red-800 bg-red-100'
                      }`}>
                        {trade.trade_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <span className={trade.profit_loss > 0 ? 'text-green-600' : 'text-red-600'}>
                        {formatCurrency(trade.profit_loss)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {trade.close_timestamp ? formatDate(trade.close_timestamp) : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {trade.strategy || 'Manual'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {showConfirmModal && selectedTrade && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                {actionType === 'close' ? 'Close Trade' : 'Cancel Trade'}
              </h3>
              <button
                onClick={() => setShowConfirmModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                {actionType === 'close' 
                  ? `Close ${selectedTrade.trade_type} position for ${selectedTrade.symbol}?`
                  : `Cancel ${selectedTrade.trade_type} order for ${selectedTrade.symbol}?`
                }
              </p>
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm">
                  <div>Symbol: <strong>{selectedTrade.symbol}</strong></div>
                  <div>Quantity: <strong>{selectedTrade.quantity}</strong></div>
                  <div>Original Price: <strong>{formatCurrency(selectedTrade.price)}</strong></div>
                  <div>Total Value: <strong>{formatCurrency(selectedTrade.total_value)}</strong></div>
                  <div>Days Open: <strong>{getDaysOpen(selectedTrade.timestamp)}</strong></div>
                </div>
              </div>
            </div>

            {actionType === 'close' && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Close Price (optional - leave blank for market price)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={closePrice}
                  onChange={(e) => setClosePrice(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Market price"
                />
              </div>
            )}

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowConfirmModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                disabled={closeTradesMutation.isLoading || cancelTradeMutation.isLoading}
              >
                Cancel
              </button>
              <button
                onClick={confirmAction}
                className={`px-4 py-2 text-sm font-medium text-white rounded-md disabled:opacity-50 ${
                  actionType === 'close' 
                    ? 'bg-green-600 hover:bg-green-700' 
                    : 'bg-red-600 hover:bg-red-700'
                }`}
                disabled={closeTradesMutation.isLoading || cancelTradeMutation.isLoading}
              >
                {closeTradesMutation.isLoading || cancelTradeMutation.isLoading
                  ? 'Processing...'
                  : actionType === 'close' ? 'Close Trade' : 'Cancel Trade'
                }
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OpenTradesManager;