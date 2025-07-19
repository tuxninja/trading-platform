import React, { useState } from 'react';
import PropTypes from 'prop-types';

const AddStockForm = ({ onAdd, isLoading }) => {
  const [symbol, setSymbol] = useState('');
  const [error, setError] = useState('');

  const validateSymbol = (value) => {
    if (!value.trim()) return 'Symbol is required.';
    if (!/^[A-Z0-9.\-]{1,10}$/.test(value.trim().toUpperCase())) return 'Invalid symbol format.';
    return '';
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const validationError = validateSymbol(symbol);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError('');
    onAdd(symbol.trim().toUpperCase());
  };

  return (
    <form onSubmit={handleSubmit} className="flex space-x-2" aria-label="Add Stock Form" autoComplete="off">
      <input
        type="text"
        value={symbol}
        onChange={(e) => setSymbol(e.target.value)}
        placeholder="Enter stock symbol (e.g., AAPL)"
        className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
        aria-label="Stock symbol"
        autoComplete="off"
        disabled={isLoading}
      />
      <button
        type="submit"
        disabled={isLoading || !symbol.trim()}
        className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 disabled:opacity-50 flex items-center"
        aria-label="Add Stock"
      >
        + Add Stock
      </button>
      {error && <span className="text-red-600 text-sm ml-2" role="alert">{error}</span>}
    </form>
  );
};

AddStockForm.propTypes = {
  onAdd: PropTypes.func.isRequired,
  isLoading: PropTypes.bool,
};

export default AddStockForm; 