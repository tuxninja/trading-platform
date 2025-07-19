import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import toast from 'react-hot-toast';
import { api } from '../services/api';

const GoogleLoginComponent = ({ onLoginSuccess }) => {
  const [isLoading, setIsLoading] = useState(false);

  const responseGoogle = async (credentialResponse) => {
    console.log('Google OAuth response:', credentialResponse);
    
    if (!credentialResponse.credential) {
      console.error('No credential in Google response');
      toast.error('Google login failed - no credential received');
      return;
    }

    setIsLoading(true);
    try {
      console.log('Sending request to backend with token...');
      const result = await api.post('/api/auth/google', {
        token: credentialResponse.credential
      });

      console.log('Backend response:', result.data);

      // Store token in localStorage
      localStorage.setItem('authToken', result.data.access_token);
      localStorage.setItem('user', JSON.stringify(result.data.user));

      toast.success(`Welcome, ${result.data.user.name}!`);
      
      if (onLoginSuccess) {
        onLoginSuccess(result.data);
      }
    } catch (error) {
      console.error('Full login error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        config: error.config
      });
      
      const errorMessage = error.response?.data?.detail || error.message || 'Authentication failed';
      toast.error(`Login failed: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  const responseGoogleError = () => {
    console.error('Google login error');
    toast.error('Google login failed. Please try again.');
  };

  return (
    <div className="flex flex-col items-center space-y-4">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
        Sign In to Trading Platform
      </h2>
      <p className="text-gray-600 dark:text-gray-300 text-center">
        Access your paper trading portfolio and sentiment analysis
      </p>
      
      <div className="w-full flex justify-center">
        <GoogleLogin
          onSuccess={responseGoogle}
          onError={responseGoogleError}
          disabled={isLoading}
          text={isLoading ? "Signing in..." : "signin_with"}
          shape="rectangular"
          theme="outline"
          size="large"
          width="300"
        />
      </div>
      
      <div className="text-sm text-gray-500 dark:text-gray-400 text-center mt-4">
        <p>By signing in, you agree to our terms of service.</p>
        <p className="mt-1">This is a paper trading platform for educational purposes only.</p>
      </div>
    </div>
  );
};

export default GoogleLoginComponent;