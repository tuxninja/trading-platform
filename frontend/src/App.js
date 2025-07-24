import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import { GoogleOAuthProvider } from '@react-oauth/google';

import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Trades from './pages/Trades';
import Sentiment from './pages/Sentiment';
import Performance from './pages/Performance';
import Stocks from './pages/Stocks';
import Login from './pages/Login';
import ApiDebugger from './components/ApiDebugger';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('authToken');
    console.log('App: Checking authentication, token exists:', !!token);
    setIsAuthenticated(!!token);
    setIsLoading(false);
  }, []);

  // Listen for login events to update authentication state
  useEffect(() => {
    const handleStorageChange = () => {
      const token = localStorage.getItem('authToken');
      console.log('App: Storage changed, token exists:', !!token);
      setIsAuthenticated(!!token);
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const ProtectedRoute = ({ children }) => {
    if (isLoading) {
      return <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>;
    }
    
    return isAuthenticated ? children : <Navigate to="/login" />;
  };

  return (
    <GoogleOAuthProvider clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}>
      <QueryClientProvider client={queryClient}>
        <Router>
          <div className="min-h-screen bg-gray-50">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/*" element={
                <ProtectedRoute>
                  <Navbar />
                  <main className="container mx-auto px-4 py-8">
                    <Routes>
                      <Route path="/" element={<Navigate to="/dashboard" />} />
                      <Route path="/dashboard" element={<Dashboard />} />
                      <Route path="/trades" element={<Trades />} />
                      <Route path="/sentiment" element={<Sentiment />} />
                      <Route path="/performance" element={<Performance />} />
                      <Route path="/stocks" element={<Stocks />} />
                      <Route path="/debug" element={<ApiDebugger />} />
                    </Routes>
                  </main>
                </ProtectedRoute>
              } />
            </Routes>
            <Toaster position="top-right" />
          </div>
        </Router>
      </QueryClientProvider>
    </GoogleOAuthProvider>
  );
}

export default App; 