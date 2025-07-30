import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

const StockPreferencesPanel = ({ stock, onUpdate, onClose, isLoading }) => {
  const [preferences, setPreferences] = useState({
    sentiment_monitoring: true,
    auto_trading: true,
    max_position_size: 1000,
    risk_tolerance: 'medium',
    is_active: true
  });

  useEffect(() => {
    if (stock) {
      setPreferences({
        sentiment_monitoring: stock.sentiment_monitoring ?? true,
        auto_trading: stock.auto_trading ?? true,
        max_position_size: stock.max_position_size ?? 1000,
        risk_tolerance: stock.risk_tolerance ?? 'medium',
        is_active: stock.is_active ?? true
      });
    }
  }, [stock]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onUpdate(preferences);
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setPreferences(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  if (!stock) return null;

  return (
    <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-4 z-10">
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-lg font-medium text-gray-900">
          {stock.symbol} Preferences
        </h4>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
          disabled={isLoading}
        >
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-3">
          <div className="flex items-center">
            <input
              type="checkbox"
              id={`active_${stock.id}`}
              name="is_active"
              checked={preferences.is_active}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              disabled={isLoading}
            />
            <label htmlFor={`active_${stock.id}`} className="ml-2 block text-sm text-gray-900">
              Active monitoring
            </label>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id={`sentiment_${stock.id}`}
              name="sentiment_monitoring"
              checked={preferences.sentiment_monitoring}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              disabled={isLoading}
            />
            <label htmlFor={`sentiment_${stock.id}`} className="ml-2 block text-sm text-gray-900">
              Enable sentiment monitoring
            </label>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id={`trading_${stock.id}`}
              name="auto_trading"
              checked={preferences.auto_trading}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              disabled={isLoading}
            />
            <label htmlFor={`trading_${stock.id}`} className="ml-2 block text-sm text-gray-900">
              Enable auto trading
            </label>
          </div>

          <div>
            <label htmlFor={`position_size_${stock.id}`} className="block text-sm font-medium text-gray-700">
              Max Position Size ($)
            </label>
            <input
              type="number"
              id={`position_size_${stock.id}`}
              name="max_position_size"
              value={preferences.max_position_size}
              onChange={handleChange}
              min="100"
              max="10000"
              step="100"
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
              disabled={isLoading}
            />
          </div>

          <div>
            <label htmlFor={`risk_${stock.id}`} className="block text-sm font-medium text-gray-700">
              Risk Tolerance
            </label>
            <select
              id={`risk_${stock.id}`}
              name="risk_tolerance"
              value={preferences.risk_tolerance}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
              disabled={isLoading}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-3 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            disabled={isLoading}
          >
            {isLoading ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default StockPreferencesPanel;