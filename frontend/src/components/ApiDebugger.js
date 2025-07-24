import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

const ApiDebugger = () => {
  const [debugInfo, setDebugInfo] = useState({
    apiBaseUrl: '',
    currentUrl: '',
    networkTests: [],
    backendHealth: null,
    tradesTest: null,
    corsTest: null,
    authToken: null
  });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Get initial debug info
    const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const currentUrl = window.location.origin;
    const authToken = localStorage.getItem('authToken');

    setDebugInfo(prev => ({
      ...prev,
      apiBaseUrl,
      currentUrl,
      authToken: authToken ? `${authToken.substring(0, 20)}...` : 'None'
    }));
  }, []);

  const runNetworkTests = async () => {
    setIsLoading(true);
    const tests = [];
    
    try {
      // Test 1: Backend health check
      console.log('Testing backend health...');
      tests.push({ name: 'Backend Health Check', status: 'running', details: '' });
      setDebugInfo(prev => ({ ...prev, networkTests: [...tests] }));

      try {
        const healthResponse = await fetch(`${debugInfo.apiBaseUrl}/api/health`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        if (healthResponse.ok) {
          const healthData = await healthResponse.json();
          tests[0] = { 
            name: 'Backend Health Check', 
            status: 'success', 
            details: `Status: ${healthData.status}, Response time: ${Date.now() - Date.now()}ms` 
          };
          setDebugInfo(prev => ({ ...prev, backendHealth: healthData }));
        } else {
          tests[0] = { 
            name: 'Backend Health Check', 
            status: 'error', 
            details: `HTTP ${healthResponse.status}: ${healthResponse.statusText}` 
          };
        }
      } catch (error) {
        tests[0] = { 
          name: 'Backend Health Check', 
          status: 'error', 
          details: `Network error: ${error.message}` 
        };
      }

      // Test 2: CORS preflight
      console.log('Testing CORS...');
      tests.push({ name: 'CORS Preflight Test', status: 'running', details: '' });
      setDebugInfo(prev => ({ ...prev, networkTests: [...tests] }));

      try {
        const corsResponse = await fetch(`${debugInfo.apiBaseUrl}/api/health`, {
          method: 'OPTIONS',
        });
        
        tests[1] = { 
          name: 'CORS Preflight Test', 
          status: corsResponse.ok ? 'success' : 'warning',
          details: `Access-Control headers: ${corsResponse.headers.get('Access-Control-Allow-Origin') || 'Missing'}`
        };
      } catch (error) {
        tests[1] = { 
          name: 'CORS Preflight Test', 
          status: 'error', 
          details: `CORS error: ${error.message}` 
        };
      }

      // Test 3: Direct API call
      console.log('Testing trades API...');
      tests.push({ name: 'Trades API Test', status: 'running', details: '' });
      setDebugInfo(prev => ({ ...prev, networkTests: [...tests] }));

      try {
        const tradesResponse = await fetch(`${debugInfo.apiBaseUrl}/api/trades`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...(localStorage.getItem('authToken') && {
              'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            })
          },
        });
        
        if (tradesResponse.ok) {
          const tradesData = await tradesResponse.json();
          tests[2] = { 
            name: 'Trades API Test', 
            status: 'success', 
            details: `Retrieved ${Array.isArray(tradesData) ? tradesData.length : 0} trades` 
          };
          setDebugInfo(prev => ({ ...prev, tradesTest: tradesData }));
        } else {
          tests[2] = { 
            name: 'Trades API Test', 
            status: 'error', 
            details: `HTTP ${tradesResponse.status}: ${tradesResponse.statusText}` 
          };
        }
      } catch (error) {
        tests[2] = { 
          name: 'Trades API Test', 
          status: 'error', 
          details: `Network error: ${error.message}` 
        };
      }

      // Test 4: Using axios service
      console.log('Testing with Axios service...');
      tests.push({ name: 'Axios Service Test', status: 'running', details: '' });
      setDebugInfo(prev => ({ ...prev, networkTests: [...tests] }));

      try {
        const axiosResponse = await api.get('/api/health');
        tests[3] = { 
          name: 'Axios Service Test', 
          status: 'success', 
          details: `Axios interceptors working, status: ${axiosResponse.data.status}` 
        };
      } catch (error) {
        tests[3] = { 
          name: 'Axios Service Test', 
          status: 'error', 
          details: `Axios error: ${error.message}${error.response ? ` (${error.response.status})` : ''}` 
        };
      }

      // Test 5: Alternative URLs
      const alternativeUrls = [
        `${window.location.origin}/api/health`,
        'https://divestifi.com/api/health',
        '/api/health'
      ];

      for (let i = 0; i < alternativeUrls.length; i++) {
        const url = alternativeUrls[i];
        console.log(`Testing alternative URL: ${url}`);
        tests.push({ name: `Alternative URL Test: ${url}`, status: 'running', details: '' });
        setDebugInfo(prev => ({ ...prev, networkTests: [...tests] }));

        try {
          const response = await fetch(url, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
          });
          
          tests[tests.length - 1] = { 
            name: `Alternative URL Test: ${url}`, 
            status: response.ok ? 'success' : 'warning',
            details: `HTTP ${response.status}: ${response.statusText}` 
          };
        } catch (error) {
          tests[tests.length - 1] = { 
            name: `Alternative URL Test: ${url}`, 
            status: 'error', 
            details: `Error: ${error.message}` 
          };
        }
      }

    } catch (error) {
      console.error('Test runner error:', error);
    } finally {
      setDebugInfo(prev => ({ ...prev, networkTests: tests }));
      setIsLoading(false);
    }
  };

  const getCardColor = (status) => {
    switch (status) {
      case 'success': return 'bg-green-50 border-green-200';
      case 'warning': return 'bg-yellow-50 border-yellow-200';
      case 'error': return 'bg-red-50 border-red-200';
      case 'running': return 'bg-blue-50 border-blue-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      case 'running': return '🔄';
      default: return '⏳';
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-2xl font-bold mb-6">API Connectivity Debugger</h1>
        
        {/* Configuration Info */}
        <div className="grid md:grid-cols-2 gap-4 mb-6">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h2 className="font-semibold mb-2">Configuration</h2>
            <div className="space-y-1 text-sm">
              <div><strong>API Base URL:</strong> {debugInfo.apiBaseUrl}</div>
              <div><strong>Current Origin:</strong> {debugInfo.currentUrl}</div>
              <div><strong>Auth Token:</strong> {debugInfo.authToken}</div>
              <div><strong>Environment:</strong> {process.env.NODE_ENV}</div>
            </div>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <h2 className="font-semibold mb-2">Expected vs Actual</h2>
            <div className="space-y-1 text-sm">
              <div><strong>Expected Production URL:</strong> https://divestifi.com/api/trades</div>
              <div><strong>Current Config URL:</strong> {debugInfo.apiBaseUrl}/api/trades</div>
              <div><strong>Issue:</strong> {debugInfo.apiBaseUrl.includes('localhost') ? 'Using localhost in production!' : 'Config looks correct'}</div>
            </div>
          </div>
        </div>

        {/* Test Runner */}
        <div className="mb-6">
          <button
            onClick={runNetworkTests}
            disabled={isLoading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white px-6 py-2 rounded-lg font-medium"
          >
            {isLoading ? 'Running Tests...' : 'Run Network Tests'}
          </button>
        </div>

        {/* Test Results */}
        {debugInfo.networkTests.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Test Results</h2>
            {debugInfo.networkTests.map((test, index) => (
              <div key={index} className={`border rounded-lg p-4 ${getCardColor(test.status)}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span>{getStatusIcon(test.status)}</span>
                    <h3 className="font-medium">{test.name}</h3>
                  </div>
                  <span className="text-sm capitalize text-gray-600">{test.status}</span>
                </div>
                {test.details && (
                  <p className="mt-2 text-sm text-gray-700">{test.details}</p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Detailed Results */}
        {(debugInfo.backendHealth || debugInfo.tradesTest) && (
          <div className="mt-6">
            <h2 className="text-xl font-semibold mb-4">Detailed Results</h2>
            <div className="grid md:grid-cols-2 gap-4">
              {debugInfo.backendHealth && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium mb-2">Backend Health Response</h3>
                  <pre className="text-xs bg-white p-2 rounded border overflow-auto">
                    {JSON.stringify(debugInfo.backendHealth, null, 2)}
                  </pre>
                </div>
              )}
              
              {debugInfo.tradesTest && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium mb-2">Trades API Response</h3>
                  <pre className="text-xs bg-white p-2 rounded border overflow-auto max-h-40">
                    {JSON.stringify(debugInfo.tradesTest, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Debugging Recommendations */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-2">Debugging Recommendations</h2>
          <div className="space-y-2 text-sm">
            <p><strong>1. Check Network Tab:</strong> Open DevTools → Network tab and see what URL is actually being called</p>
            <p><strong>2. Verify Environment:</strong> Make sure REACT_APP_API_URL is set correctly for production</p>
            <p><strong>3. Check CORS:</strong> Ensure the backend is allowing requests from your domain</p>
            <p><strong>4. Test nginx Proxy:</strong> Try accessing https://divestifi.com/api/health directly in a new tab</p>
            <p><strong>5. Check Backend Logs:</strong> Look at the trading-backend container logs for any errors</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApiDebugger;