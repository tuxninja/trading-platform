import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import GoogleLoginComponent from '../GoogleLogin';
import { api } from '../../services/api';
import toast from 'react-hot-toast';

// Mock dependencies
jest.mock('../../services/api');
jest.mock('react-hot-toast');
jest.mock('@react-oauth/google', () => ({
  GoogleOAuthProvider: ({ children }) => <div>{children}</div>,
  GoogleLogin: ({ onSuccess, onError }) => (
    <button 
      onClick={() => onSuccess({ credential: 'mock-credential' })}
      data-testid="google-login-button"
    >
      Sign in with Google
    </button>
  )
}));

const mockOnLoginSuccess = jest.fn();

const TestWrapper = ({ children }) => (
  <GoogleOAuthProvider clientId="test-client-id">
    {children}
  </GoogleOAuthProvider>
);

describe('GoogleLoginComponent', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders login form with title and description', () => {
    render(
      <TestWrapper>
        <GoogleLoginComponent onLoginSuccess={mockOnLoginSuccess} />
      </TestWrapper>
    );

    expect(screen.getByText('Sign In to Trading Platform')).toBeInTheDocument();
    expect(screen.getByText(/Access your paper trading portfolio/)).toBeInTheDocument();
    expect(screen.getByText(/educational purposes only/)).toBeInTheDocument();
  });

  test('handles successful Google OAuth login', async () => {
    const mockResponse = {
      data: {
        access_token: 'mock-jwt-token',
        user: {
          name: 'Test User',
          email: 'test@example.com'
        }
      }
    };

    api.post.mockResolvedValue(mockResponse);

    render(
      <TestWrapper>
        <GoogleLoginComponent onLoginSuccess={mockOnLoginSuccess} />
      </TestWrapper>
    );

    const loginButton = screen.getByTestId('google-login-button');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/api/auth/google', {
        token: 'mock-credential'
      });
    });

    expect(mockOnLoginSuccess).toHaveBeenCalledWith(mockResponse.data);
    expect(toast.success).toHaveBeenCalledWith('Welcome, Test User!');
  });

  test('handles authentication API error', async () => {
    const mockError = {
      response: {
        data: { detail: 'Invalid token' },
        status: 401
      }
    };

    api.post.mockRejectedValue(mockError);

    render(
      <TestWrapper>
        <GoogleLoginComponent onLoginSuccess={mockOnLoginSuccess} />
      </TestWrapper>
    );

    const loginButton = screen.getByTestId('google-login-button');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Login failed: Invalid token');
    });

    expect(mockOnLoginSuccess).not.toHaveBeenCalled();
  });

  test('handles network error', async () => {
    const mockError = new Error('Network Error');
    api.post.mockRejectedValue(mockError);

    render(
      <TestWrapper>
        <GoogleLoginComponent onLoginSuccess={mockOnLoginSuccess} />
      </TestWrapper>
    );

    const loginButton = screen.getByTestId('google-login-button');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Login failed: Network Error');
    });
  });

  test('handles missing credential in Google response', async () => {
    const MockGoogleLogin = ({ onSuccess }) => (
      <button 
        onClick={() => onSuccess({})} // No credential
        data-testid="google-login-button"
      >
        Sign in with Google
      </button>
    );

    // Override the mock for this test
    require('@react-oauth/google').GoogleLogin = MockGoogleLogin;

    render(
      <TestWrapper>
        <GoogleLoginComponent onLoginSuccess={mockOnLoginSuccess} />
      </TestWrapper>
    );

    const loginButton = screen.getByTestId('google-login-button');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Google login failed - no credential received');
    });

    expect(api.post).not.toHaveBeenCalled();
  });
});