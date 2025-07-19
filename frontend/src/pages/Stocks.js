import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-hot-toast';
import StockCard from '../components/StockCard';
import AddStockForm from '../components/AddStockForm';

const Stocks = () => {
  const [selectedStock, setSelectedStock] = useState(null);
  const queryClient = useQueryClient();

  const { data: stocks, isLoading, isError, error } = useQuery('stocks', require('../services/api').stocksAPI.getAll);

  const addStockMutation = useMutation(
    (symbol) => require('../services/api').stocksAPI.add(symbol),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('stocks');
        toast.success('Successfully added stock to tracking');
      },
      onError: (error) => {
        toast.error(error.response?.data?.error || 'Failed to add stock');
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
    return <div className="text-center text-red-600">Error loading stocks: {error?.message || 'Unknown error'}</div>;
  }

  if (!stocks || !Array.isArray(stocks) || stocks.length === 0) {
    return (
      <div className="col-span-full text-center text-red-600">
        No stock data available.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Market Watch</h1>
        <AddStockForm
          onAdd={(symbol) => addStockMutation.mutate(symbol)}
          isLoading={addStockMutation.isLoading}
        />
      </div>

      {/* Stock Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {stocks.map((stock) => (
          <StockCard
            key={stock.symbol}
            stock={stock}
            selected={selectedStock === stock.symbol}
            onSelect={(symbol) => setSelectedStock(selectedStock === symbol ? null : symbol)}
          />
        ))}
      </div>

      {/* Market Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Market Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {stocks.filter(stock => stock.price_change_pct > 0).length}
            </div>
            <div className="text-sm text-green-700">Gaining Stocks</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">
              {stocks.filter(stock => stock.price_change_pct < 0).length}
            </div>
            <div className="text-sm text-red-700">Declining Stocks</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-600">
              {stocks.filter(stock => stock.price_change_pct === 0).length}
            </div>
            <div className="text-sm text-gray-700">Unchanged</div>
          </div>
        </div>
      </div>

      {/* Top Movers */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Top Movers</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Top Gainers */}
          <div>
            <h3 className="text-md font-medium text-green-700 mb-3">Top Gainers</h3>
            <div className="space-y-2">
              {stocks
                .filter(stock => stock.price_change_pct > 0)
                .sort((a, b) => b.price_change_pct - a.price_change_pct)
                .slice(0, 5)
                .map((stock) => (
                  <div key={stock.symbol} className="flex justify-between items-center p-2 bg-green-50 rounded">
                    <span className="font-medium text-gray-900">{stock.symbol}</span>
                    <span className="text-green-600 font-medium">
                      +{stock.price_change_pct.toFixed(2)}%
                    </span>
                  </div>
                ))
              }
            </div>
          </div>

          {/* Top Losers */}
          <div>
            <h3 className="text-md font-medium text-red-700 mb-3">Top Losers</h3>
            <div className="space-y-2">
              {stocks
                .filter(stock => stock.price_change_pct < 0)
                .sort((a, b) => a.price_change_pct - b.price_change_pct)
                .slice(0, 5)
                .map((stock) => (
                  <div key={stock.symbol} className="flex justify-between items-center p-2 bg-red-50 rounded">
                    <span className="font-medium text-gray-900">{stock.symbol}</span>
                    <span className="text-red-600 font-medium">
                      {stock.price_change_pct.toFixed(2)}%
                    </span>
                  </div>
                ))
              }
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Stocks; 