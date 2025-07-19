import React from 'react';
import PropTypes from 'prop-types';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon, MinusIcon } from '@heroicons/react/24/outline';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const getPriceChangeColor = (change) => {
  if (change > 0) return 'text-green-600';
  if (change < 0) return 'text-red-600';
  return 'text-gray-600';
};

const getPriceChangeIcon = (change) => {
  if (change > 0) return <ArrowTrendingUpIcon className="h-4 w-4 text-green-500" aria-label="Trending Up" />;
  if (change < 0) return <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" aria-label="Trending Down" />;
  return <MinusIcon className="h-4 w-4 text-gray-500" aria-label="No Change" />;
};

const StockCard = ({ stock, selected, onSelect }) => (
  <div
    role="button"
    tabIndex={0}
    aria-pressed={selected}
    aria-label={`View details for ${stock.symbol}`}
    key={stock.symbol}
    className={`bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow cursor-pointer outline-none ${selected ? 'ring-2 ring-primary-500' : ''}`}
    onClick={() => onSelect(stock.symbol)}
    onKeyPress={e => { if (e.key === 'Enter') onSelect(stock.symbol); }}
  >
    <div className="flex justify-between items-start mb-4">
      <div>
        <h3 className="text-lg font-medium text-gray-900">{stock.symbol}</h3>
        <p className="text-sm text-gray-500">{stock.company_name}</p>
      </div>
      {getPriceChangeIcon(stock.price_change_pct)}
    </div>
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-500">Current Price</span>
        <span className="text-lg font-semibold text-gray-900">
          ${stock.current_price}
        </span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-500">Change</span>
        <span className={`font-medium ${getPriceChangeColor(stock.price_change_pct)}`}> 
          {stock.price_change > 0 ? '+' : ''}{stock.price_change.toFixed(2)}
          ({stock.price_change_pct > 0 ? '+' : ''}{stock.price_change_pct.toFixed(2)}%)
        </span>
      </div>
      <div className="flex justify-between items-center text-sm text-gray-500">
        <span>Market Cap</span>
        <span>
          {stock.market_cap ? `$${(stock.market_cap / 1e9).toFixed(1)}B` : 'N/A'}
        </span>
      </div>
      <div className="flex justify-between items-center text-sm text-gray-500">
        <span>P/E Ratio</span>
        <span>{stock.pe_ratio ? stock.pe_ratio.toFixed(2) : 'N/A'}</span>
      </div>
      <div className="flex justify-between items-center text-sm text-gray-500">
        <span>Dividend Yield</span>
        <span>
          {stock.dividend_yield ? `${(stock.dividend_yield * 100).toFixed(2)}%` : 'N/A'}
        </span>
      </div>
    </div>
    {selected && (
      <div className="mt-4 pt-4 border-t border-gray-200">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Company Details</h4>
        <div className="space-y-2 text-sm text-gray-600">
          <div>
            <strong>Sector:</strong> {stock.sector}
          </div>
          <div>
            <strong>Industry:</strong> {stock.industry}
          </div>
        </div>
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Price History</h4>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={stock.historical_data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" hide />
              <YAxis hide />
              <Tooltip 
                formatter={(value) => [`$${value}`, 'Price']}
                labelFormatter={(label) => `Date: ${label}`}
              />
              <Line 
                type="monotone" 
                dataKey="close" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    )}
  </div>
);

StockCard.propTypes = {
  stock: PropTypes.shape({
    symbol: PropTypes.string.isRequired,
    company_name: PropTypes.string,
    current_price: PropTypes.number.isRequired,
    price_change: PropTypes.number.isRequired,
    price_change_pct: PropTypes.number.isRequired,
    market_cap: PropTypes.number,
    pe_ratio: PropTypes.number,
    dividend_yield: PropTypes.number,
    historical_data: PropTypes.array,
    sector: PropTypes.string,
    industry: PropTypes.string,
  }).isRequired,
  selected: PropTypes.bool,
  onSelect: PropTypes.func.isRequired,
};

export default StockCard; 