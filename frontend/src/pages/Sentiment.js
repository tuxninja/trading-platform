import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-hot-toast';
import { 
  ArrowPathIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon
} from '@heroicons/react/24/outline';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

import { sentimentAPI } from '../services/api';

const Sentiment = () => {
  const [selectedStock, setSelectedStock] = useState(null);
  const queryClient = useQueryClient();

  const { data: sentimentData, isLoading, error } = useQuery(
    'sentiment', 
    sentimentAPI.getAll,
    {
      retry: 1,
      onError: (error) => {
        console.error('Sentiment API error:', error);
        toast.error('Failed to load sentiment data');
      }
    }
  );

  const analyzeSentimentMutation = useMutation(
    (symbol) => sentimentAPI.analyze(symbol),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('sentiment');
        toast.success('Sentiment analysis completed!');
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to analyze sentiment');
      }
    }
  );

  const bulkAnalyzeMutation = useMutation(
    (symbols) => {
      // Fallback to individual analysis if bulk not available
      if (sentimentAPI.analyzeBulk) {
        return sentimentAPI.analyzeBulk(symbols);
      } else {
        // Fallback: analyze each symbol individually
        return Promise.all(symbols.map(symbol => sentimentAPI.analyze(symbol)))
          .then(results => ({
            successful: results.length,
            failed: 0,
            results: results
          }));
      }
    },
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries('sentiment');
        const successful = data.successful || data.length || 0;
        const failed = data.failed || 0;
        toast.success(`Analyzed ${successful} stocks successfully!`);
        if (failed > 0) {
          toast.error(`Failed to analyze ${failed} stocks`);
        }
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to run bulk analysis');
      }
    }
  );

  const handleAnalyzeSentiment = (symbol) => {
    analyzeSentimentMutation.mutate(symbol);
  };

  const getSentimentColor = (score) => {
    if (score > 0.2) return 'text-green-600';
    if (score < -0.2) return 'text-red-600';
    return 'text-yellow-600';
  };

  const getSentimentIcon = (score) => {
    if (score > 0.2) return <ArrowTrendingUpIcon className="h-5 w-5 text-green-500" />;
    if (score < -0.2) return <ArrowTrendingDownIcon className="h-5 w-5 text-red-500" />;
    return <MinusIcon className="h-5 w-5 text-yellow-500" />;
  };

  const isSentimentArray = Array.isArray(sentimentData);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-red-600 text-lg font-semibold mb-2">Failed to load sentiment data</div>
          <button 
            onClick={() => window.location.reload()} 
            className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Handle case where sentimentData is not an array or is empty
  if (!Array.isArray(sentimentData)) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Sentiment Analysis</h1>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <div className="text-yellow-800 text-lg font-semibold mb-2">No sentiment data available</div>
          <p className="text-yellow-700 mb-4">
            Add some stocks to your watchlist and run sentiment analysis to get started.
          </p>
          <button 
            onClick={() => window.location.href = '/stocks'} 
            className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700"
          >
            Go to Stocks
          </button>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const chartData = isSentimentArray
    ? sentimentData.map(item => ({
        symbol: item.symbol,
        overall: item.overall_sentiment,
        news: item.news_sentiment,
        social: item.social_sentiment
      }))
    : [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Sentiment Analysis</h1>
        <button
          onClick={() => {
            if (Array.isArray(sentimentData) && sentimentData.length > 0) {
              const symbols = sentimentData.map(item => item.symbol);
              bulkAnalyzeMutation.mutate(symbols);
            }
          }}
          disabled={bulkAnalyzeMutation.isLoading || !Array.isArray(sentimentData) || sentimentData.length === 0}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center"
        >
          <ArrowPathIcon className="h-5 w-5 mr-2" />
          {bulkAnalyzeMutation.isLoading ? 'Analyzing All...' : 'Refresh All'}
        </button>
      </div>

      {/* Sentiment Overview Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Sentiment Overview</h2>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="symbol" />
            <YAxis domain={[-1, 1]} />
            <Tooltip 
              formatter={(value, name) => [
                value.toFixed(3), 
                name === 'overall' ? 'Overall' : name === 'news' ? 'News' : 'Social'
              ]}
            />
            <Bar dataKey="overall" fill="#3b82f6" name="Overall" />
            <Bar dataKey="news" fill="#10b981" name="News" />
            <Bar dataKey="social" fill="#f59e0b" name="Social" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Sentiment Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isSentimentArray
          ? sentimentData.map((item) => (
              <div 
                key={item.symbol} 
                className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => setSelectedStock(selectedStock === item.symbol ? null : item.symbol)}
              >
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-medium text-gray-900">{item.symbol}</h3>
                  {getSentimentIcon(item.overall_sentiment)}
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Overall Sentiment</span>
                    <span className={`text-lg font-semibold ${getSentimentColor(item.overall_sentiment)}`}>
                      {item.overall_sentiment > 0 ? '+' : ''}{item.overall_sentiment.toFixed(3)}
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">News Sentiment</span>
                    <span className={`text-sm font-medium ${getSentimentColor(item.news_sentiment)}`}>
                      {item.news_sentiment > 0 ? '+' : ''}{item.news_sentiment.toFixed(3)}
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Social Sentiment</span>
                    <span className={`text-sm font-medium ${getSentimentColor(item.social_sentiment)}`}>
                      {item.social_sentiment > 0 ? '+' : ''}{item.social_sentiment.toFixed(3)}
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center text-sm text-gray-500">
                    <span>News Articles: {item.news_count}</span>
                    <span>Social Posts: {item.social_count}</span>
                  </div>
                  
                  <div className="pt-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAnalyzeSentiment(item.symbol);
                      }}
                      disabled={analyzeSentimentMutation.isLoading}
                      className="w-full bg-gray-100 text-gray-700 px-3 py-2 rounded-md hover:bg-gray-200 disabled:opacity-50 text-sm"
                    >
                      {analyzeSentimentMutation.isLoading ? 'Analyzing...' : 'Refresh Analysis'}
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {selectedStock === item.symbol && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Analysis Details</h4>
                    <div className="space-y-2 text-sm text-gray-600">
                      <div>
                        <strong>Last Updated:</strong> {new Date(item.timestamp).toLocaleString()}
                      </div>
                      <div>
                        <strong>Source:</strong> {item.source}
                      </div>
                      <div>
                        <strong>Sentiment Breakdown:</strong>
                        <div className="ml-2 mt-1">
                          <div>News: {item.news_count} articles analyzed</div>
                          <div>Social: {item.social_count} posts analyzed</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))
          : (
              <div className="col-span-full text-center">
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-8">
                  <div className="text-gray-600 text-lg mb-4">No sentiment data available</div>
                  <p className="text-gray-500 mb-4">
                    Add stocks to your watchlist and run sentiment analysis to see data here.
                  </p>
                  <button 
                    onClick={() => window.location.href = '/stocks'} 
                    className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
                  >
                    Add Stocks
                  </button>
                </div>
              </div>
            )
        }
      </div>

      {/* Sentiment Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Sentiment Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {isSentimentArray
                ? sentimentData.filter(item => item.overall_sentiment > 0.2).length
                : 0}
            </div>
            <div className="text-sm text-green-700">Positive Sentiment</div>
          </div>
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">
              {isSentimentArray
                ? sentimentData.filter(item => item.overall_sentiment >= -0.2 && item.overall_sentiment <= 0.2).length
                : 0}
            </div>
            <div className="text-sm text-yellow-700">Neutral Sentiment</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">
              {isSentimentArray
                ? sentimentData.filter(item => item.overall_sentiment < -0.2).length
                : 0}
            </div>
            <div className="text-sm text-red-700">Negative Sentiment</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sentiment; 