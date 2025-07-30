import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-hot-toast';
import { 
  PlusIcon, 
  TrashIcon, 
  CogIcon, 
  BellIcon,
  EyeIcon 
} from '@heroicons/react/24/outline';
import StockCard from '../components/StockCard';
import AddStockToWatchlist from '../components/AddStockToWatchlist';
import StockPreferencesPanel from '../components/StockPreferencesPanel';
import { watchlistAPI } from '../services/api';

const Stocks = () => {
  const [selectedStock, setSelectedStock] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showPreferences, setShowPreferences] = useState({});
  const queryClient = useQueryClient();

  // Use watchlist instead of general stocks
  const { data: watchlist, isLoading, isError, error } = useQuery('watchlist', () => watchlistAPI.getAll());
  const { data: alerts } = useQuery('watchlist-alerts', () => watchlistAPI.getAlerts(true)); // Unread only

  const addStockMutation = useMutation(
    (stockData) => watchlistAPI.add(stockData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('watchlist');
        toast.success('Successfully added stock to watchlist');
        setShowAddForm(false);
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to add stock to watchlist');
      }
    }
  );

  const removeStockMutation = useMutation(
    (symbol) => watchlistAPI.remove(symbol),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('watchlist');
        toast.success('Successfully removed stock from watchlist');
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to remove stock');
      }
    }
  );

  const updatePreferencesMutation = useMutation(
    ({ stockId, preferences }) => watchlistAPI.updatePreferences(stockId, preferences),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('watchlist');
        toast.success('Preferences updated');
        setShowPreferences({});
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to update preferences');
      }
    }
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (isError) {
    return <div className="text-center text-red-600">Error loading watchlist: {error?.message || 'Unknown error'}</div>;
  }

  if (!watchlist || !Array.isArray(watchlist) || watchlist.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">My Watchlist</h1>
          <button
            onClick={() => setShowAddForm(true)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Stock
          </button>
        </div>
        
        <div className="text-center py-12">
          <EyeIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Stocks in Watchlist</h3>
          <p className="text-gray-600 mb-4">Add stocks to monitor their sentiment and enable automated trading.</p>
          <button
            onClick={() => setShowAddForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Add Your First Stock
          </button>
        </div>
        
        {showAddForm && (
          <AddStockToWatchlist 
            onSubmit={addStockMutation.mutate}
            onCancel={() => setShowAddForm(false)}
            isLoading={addStockMutation.isLoading}
          />
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Watchlist</h1>
          <p className="text-gray-600 mt-1">
            {watchlist.length} stocks • {alerts?.length || 0} unread alerts
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Add Stock
        </button>
      </div>

      {alerts && alerts.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex items-center">
            <BellIcon className="h-5 w-5 text-yellow-600 mr-2" />
            <span className="text-sm font-medium text-yellow-800">
              {alerts.length} unread alert{alerts.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {watchlist.map((stock) => (
          <div key={stock.symbol} className="relative">
            <StockCard 
              stock={stock}
              onSelect={() => setSelectedStock(stock)}
            />
            <div className="absolute top-2 right-2 flex space-x-1">
              <button
                onClick={() => setShowPreferences(prev => ({ ...prev, [stock.id]: !prev[stock.id] }))}
                className="p-1 bg-white rounded-full shadow-sm hover:bg-gray-50"
                title="Preferences"
              >
                <CogIcon className="h-4 w-4 text-gray-600" />
              </button>
              <button
                onClick={() => removeStockMutation.mutate(stock.symbol)}
                className="p-1 bg-white rounded-full shadow-sm hover:bg-red-50"
                title="Remove from watchlist"
                disabled={removeStockMutation.isLoading}
              >
                <TrashIcon className="h-4 w-4 text-red-600" />
              </button>
            </div>
            
            {showPreferences[stock.id] && (
              <StockPreferencesPanel
                stock={stock}
                onUpdate={(preferences) => updatePreferencesMutation.mutate({ stockId: stock.id, preferences })}
                onClose={() => setShowPreferences(prev => ({ ...prev, [stock.id]: false }))}
                isLoading={updatePreferencesMutation.isLoading}
              />
            )}
          </div>
        ))}
      </div>

      {showAddForm && (
        <AddStockToWatchlist 
          onSubmit={addStockMutation.mutate}
          onCancel={() => setShowAddForm(false)}
          isLoading={addStockMutation.isLoading}
        />
      )}

      {/* Market Summary for Watchlist */}
      {watchlist && watchlist.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Watchlist Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {watchlist.filter(stock => stock.price_change_pct > 0).length}
              </div>
              <div className="text-sm text-green-700">Gaining Stocks</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {watchlist.filter(stock => stock.price_change_pct < 0).length}
              </div>
              <div className="text-sm text-red-700">Declining Stocks</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-600">
                {watchlist.filter(stock => stock.price_change_pct === 0).length}
              </div>
              <div className="text-sm text-gray-700">Unchanged</div>
            </div>
          </div>
        </div>
      )}

      {/* Top Movers in Watchlist */}
      {watchlist && watchlist.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Top Movers in Watchlist</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Top Gainers */}
            <div>
              <h3 className="text-md font-medium text-green-700 mb-3">Top Gainers</h3>
              <div className="space-y-2">
                {watchlist
                  .filter(stock => stock.price_change_pct > 0)
                  .sort((a, b) => b.price_change_pct - a.price_change_pct)
                  .slice(0, 5)
                  .map((stock) => (
                    <div key={stock.symbol} className="flex justify-between items-center p-2 bg-green-50 rounded">
                      <span className="font-medium text-gray-900">{stock.symbol}</span>
                      <span className="text-green-600 font-medium">
                        +{stock.price_change_pct?.toFixed(2) || '0.00'}%
                      </span>
                    </div>
                  ))
                }
                {watchlist.filter(stock => stock.price_change_pct > 0).length === 0 && (
                  <p className="text-sm text-gray-500 italic">No gaining stocks in watchlist</p>
                )}
              </div>
            </div>

            {/* Top Losers */}
            <div>
              <h3 className="text-md font-medium text-red-700 mb-3">Top Losers</h3>
              <div className="space-y-2">
                {watchlist
                  .filter(stock => stock.price_change_pct < 0)
                  .sort((a, b) => a.price_change_pct - b.price_change_pct)
                  .slice(0, 5)
                  .map((stock) => (
                    <div key={stock.symbol} className="flex justify-between items-center p-2 bg-red-50 rounded">
                      <span className="font-medium text-gray-900">{stock.symbol}</span>
                      <span className="text-red-600 font-medium">
                        {stock.price_change_pct?.toFixed(2) || '0.00'}%
                      </span>
                    </div>
                  ))
                }
                {watchlist.filter(stock => stock.price_change_pct < 0).length === 0 && (
                  <p className="text-sm text-gray-500 italic">No declining stocks in watchlist</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Stocks; 