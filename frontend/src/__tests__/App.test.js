import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

// Mock the GoogleOAuthProvider
jest.mock('@react-oauth/google', () => ({
  GoogleOAuthProvider: ({ children }) => <div>{children}</div>
}));

// Mock the pages
jest.mock('../pages/Dashboard', () => {
  return function MockDashboard() {
    return <div data-testid="dashboard">Dashboard Page</div>;
  };
});

jest.mock('../pages/Login', () => {
  return function MockLogin() {
    return <div data-testid="login">Login Page</div>;
  };
});

jest.mock('../pages/Trades', () => {
  return function MockTrades() {
    return <div data-testid="trades">Trades Page</div>;
  };
});

jest.mock('../components/Navbar', () => {
  return function MockNavbar() {
    return <div data-testid="navbar">Navbar</div>;
  };
});

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});

describe('App', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('shows loading state initially', () => {
    mockLocalStorage.getItem.mockReturnValue(null);

    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('redirects to login when not authenticated', async () => {
    mockLocalStorage.getItem.mockReturnValue(null);

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('login')).toBeInTheDocument();
    });
  });

  test('shows dashboard when authenticated', async () => {
    mockLocalStorage.getItem.mockReturnValue('mock-auth-token');

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('navbar')).toBeInTheDocument();
      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    });
  });

  test('redirects root path to dashboard when authenticated', async () => {
    mockLocalStorage.getItem.mockReturnValue('mock-auth-token');

    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    });
  });

  test('allows access to login page when not authenticated', async () => {
    mockLocalStorage.getItem.mockReturnValue(null);

    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('login')).toBeInTheDocument();
    });
  });

  test('shows protected routes when authenticated', async () => {
    mockLocalStorage.getItem.mockReturnValue('mock-auth-token');

    render(
      <MemoryRouter initialEntries={['/trades']}>
        <App />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('navbar')).toBeInTheDocument();
      expect(screen.getByTestId('trades')).toBeInTheDocument();
    });
  });

  test('handles storage change events', async () => {
    mockLocalStorage.getItem.mockReturnValue(null);

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <App />
      </MemoryRouter>
    );

    // Initially should show login
    await waitFor(() => {
      expect(screen.getByTestId('login')).toBeInTheDocument();
    });

    // Simulate login by setting token and firing storage event
    mockLocalStorage.getItem.mockReturnValue('mock-auth-token');
    
    // Create and dispatch a storage event
    const storageEvent = new StorageEvent('storage', {
      key: 'authToken',
      newValue: 'mock-auth-token'
    });
    window.dispatchEvent(storageEvent);

    await waitFor(() => {
      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    });
  });
});