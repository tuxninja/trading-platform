import React, { useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

const AddStockToWatchlist = ({ onSubmit, onCancel, isLoading }) => {
  const [formData, setFormData] = useState({
    symbol: '',
    sentiment_monitoring: true,
    auto_trading: true,
    max_position_size: 1000,
    risk_tolerance: 'medium'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!formData.symbol.trim()) {
      return;
    }

    onSubmit({
      symbol: formData.symbol.toUpperCase().trim(),
      preferences: {
        sentiment_monitoring: formData.sentiment_monitoring,
        auto_trading: formData.auto_trading,
        max_position_size: parseFloat(formData.max_position_size) || 1000,
        risk_tolerance: formData.risk_tolerance
      }
    });
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Add Stock to Watchlist</h3>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600"
            disabled={isLoading}
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="symbol" className="block text-sm font-medium text-gray-700">
              Stock Symbol
            </label>
            <input
              type="text"
              id="symbol"
              name="symbol"
              value={formData.symbol}
              onChange={handleChange}
              placeholder="e.g., AAPL"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              required
              disabled={isLoading}
            />
          </div>

          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-700">Monitoring Preferences</h4>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                id="sentiment_monitoring"
                name="sentiment_monitoring"
                checked={formData.sentiment_monitoring}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={isLoading}
              />
              <label htmlFor="sentiment_monitoring" className="ml-2 block text-sm text-gray-900">
                Enable sentiment monitoring
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="auto_trading"
                name="auto_trading"
                checked={formData.auto_trading}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={isLoading}
              />
              <label htmlFor="auto_trading" className="ml-2 block text-sm text-gray-900">
                Enable auto trading
              </label>
            </div>

            <div>
              <label htmlFor="max_position_size" className="block text-sm font-medium text-gray-700">
                Max Position Size ($)
              </label>
              <input
                type="number"
                id="max_position_size"
                name="max_position_size"
                value={formData.max_position_size}
                onChange={handleChange}
                min="100"
                max="10000"
                step="100"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                disabled={isLoading}
              />
            </div>

            <div>
              <label htmlFor="risk_tolerance" className="block text-sm font-medium text-gray-700">
                Risk Tolerance
              </label>
              <select
                id="risk_tolerance"
                name="risk_tolerance"
                value={formData.risk_tolerance}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                disabled={isLoading}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              disabled={isLoading || !formData.symbol.trim()}
            >
              {isLoading ? 'Adding...' : 'Add to Watchlist'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddStockToWatchlist;