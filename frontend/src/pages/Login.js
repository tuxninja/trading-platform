import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import GoogleLoginComponent from '../components/GoogleLogin';

const Login = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('authToken');
    if (token) {
      navigate('/dashboard');
    }
  }, [navigate]);

  const handleLoginSuccess = (authData) => {
    console.log('Login: Authentication successful', authData);
    // Force a page refresh to update authentication state
    window.location.href = '/dashboard';
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            Trading Platform
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            Paper Trading with Sentiment Analysis
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-gray-800 py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <GoogleLoginComponent onLoginSuccess={handleLoginSuccess} />
        </div>
      </div>

      <div className="mt-8 text-center">
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 max-w-2xl mx-auto">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
            ⚠️ Educational Platform Only
          </h3>
          <p className="text-blue-800 dark:text-blue-200 text-sm">
            This is a paper trading platform for educational and testing purposes only. 
            No real money is involved in any trades. All trading is simulated using real market data.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;