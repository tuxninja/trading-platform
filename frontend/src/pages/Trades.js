import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-hot-toast';
import { 
  PlusIcon, 
  TrashIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

import { tradesAPI } from '../services/api';

const Trades = () => {
  const [showForm, setShowForm] = useState(false);
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [selectedTrade, setSelectedTrade] = useState(null);
  const [closePrice, setClosePrice] = useState('');
  const [formData, setFormData] = useState({
    symbol: '',
    trade_type: 'BUY',
    quantity: '',
    price: '',
    strategy: 'MANUAL'
  });

  const queryClient = useQueryClient();

  const { data: trades, isLoading } = useQuery('trades', tradesAPI.getAll);

  const createTradeMutation = useMutation(tradesAPI.create, {
    onSuccess: () => {
      queryClient.invalidateQueries('trades');
      queryClient.invalidateQueries('performance');
      toast.success('Trade created successfully!');
      setShowForm(false);
      setFormData({
        symbol: '',
        trade_type: 'BUY',
        quantity: '',
        price: '',
        strategy: 'MANUAL'
      });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to create trade');
    }
  });

  const closeTradeMutation = useMutation(
    ({ tradeId, closePrice }) => tradesAPI.close(tradeId, closePrice),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('trades');
        queryClient.invalidateQueries('performance');
        toast.success('Trade closed successfully!');
        setShowCloseModal(false);
        setSelectedTrade(null);
        setClosePrice('');
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to close trade');
      }
    }
  );

  const deleteTradeMutation = useMutation(tradesAPI.delete, {
    onSuccess: () => {
      queryClient.invalidateQueries('trades');
      queryClient.invalidateQueries('performance');
      toast.success('Trade deleted successfully!');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to delete trade');
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    createTradeMutation.mutate({
      ...formData,
      quantity: parseInt(formData.quantity),
      price: parseFloat(formData.price)
    });
  };

  const handleClose = (trade) => {
    setSelectedTrade(trade);
    setClosePrice(''); // Let backend fetch current price if not specified
    setShowCloseModal(true);
  };

  const handleCloseSubmit = (e) => {
    e.preventDefault();
    closeTradeMutation.mutate({
      tradeId: selectedTrade.id,
      closePrice: closePrice ? parseFloat(closePrice) : null
    });
  };

  const handleDelete = (tradeId) => {
    if (window.confirm('Are you sure you want to delete this trade?')) {
      deleteTradeMutation.mutate(tradeId);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Trades</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          New Trade
        </button>
      </div>

      {/* Create Trade Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Create New Trade</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Symbol</label>
                <input
                  type="text"
                  value={formData.symbol}
                  onChange={(e) => setFormData({...formData, symbol: e.target.value.toUpperCase()})}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  placeholder="AAPL"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Trade Type</label>
                <select
                  value={formData.trade_type}
                  onChange={(e) => setFormData({...formData, trade_type: e.target.value})}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="BUY">BUY</option>
                  <option value="SELL">SELL</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Quantity</label>
                <input
                  type="number"
                  value={formData.quantity}
                  onChange={(e) => setFormData({...formData, quantity: e.target.value})}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  placeholder="100"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Price</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.price}
                  onChange={(e) => setFormData({...formData, price: e.target.value})}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  placeholder="150.00"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Strategy</label>
                <select
                  value={formData.strategy}
                  onChange={(e) => setFormData({...formData, strategy: e.target.value})}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="MANUAL">Manual</option>
                  <option value="SENTIMENT">Sentiment</option>
                  <option value="MOMENTUM">Momentum</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createTradeMutation.isLoading}
                className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
              >
                {createTradeMutation.isLoading ? 'Creating...' : 'Create Trade'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Trades Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Trade History</h2>
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
                  Quantity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Strategy
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {trades && trades.length > 0 ? (
                trades.map((trade) => (
                  <tr key={trade.id}>
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {trade.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${trade.price}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${trade.total_value.toLocaleString()}
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {trade.strategy}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(trade.timestamp).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        {trade.status === 'OPEN' && (
                          <button
                            onClick={() => handleClose(trade)}
                            className="text-green-600 hover:text-green-900"
                            title="Close trade"
                          >
                            <CheckIcon className="h-4 w-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(trade.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete trade"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="9" className="px-6 py-4 text-center text-gray-500">
                    No trades found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Close Trade Modal */}
      {showCloseModal && selectedTrade && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Close Trade: {selectedTrade.symbol}
              </h3>
              <div className="mb-4 text-sm text-gray-600">
                <p>Trade Type: <span className="font-medium">{selectedTrade.trade_type}</span></p>
                <p>Quantity: <span className="font-medium">{selectedTrade.quantity} shares</span></p>
                <p>Entry Price: <span className="font-medium">${selectedTrade.price}</span></p>
              </div>
              <form onSubmit={handleCloseSubmit}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Close Price (optional - leave blank for current market price)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={closePrice}
                    onChange={(e) => setClosePrice(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Current market price"
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCloseModal(false);
                      setSelectedTrade(null);
                      setClosePrice('');
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={closeTradeMutation.isLoading}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    {closeTradeMutation.isLoading ? 'Closing...' : 'Close Trade'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Trades; 