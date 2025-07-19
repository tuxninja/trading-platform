# Trading Platform Frontend

A modern React-based frontend for the Trading Sentiment Analysis Platform, featuring real-time portfolio tracking, interactive charts, and intuitive trading interfaces.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Components](#components)
- [Pages](#pages)
- [API Integration](#api-integration)
- [Styling](#styling)
- [State Management](#state-management)
- [Development](#development)
- [Building](#building)
- [Testing](#testing)

## 🎯 Overview

The frontend is a single-page application (SPA) built with React that provides an intuitive interface for paper trading, portfolio management, and sentiment analysis visualization.

### Tech Stack
- **Framework**: React 18+
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **HTTP Client**: Axios
- **State Management**: React Query + useState/useEffect
- **Icons**: Heroicons
- **Build Tool**: Create React App

### Key Features
- 📊 **Interactive Dashboard** with real-time portfolio charts
- 💼 **Trading Interface** for executing paper trades
- 📈 **Portfolio Analytics** with performance metrics
- 📰 **Sentiment Analysis** visualization
- 🔍 **Market Discovery** tools
- 📱 **Responsive Design** for all devices

## 🏗️ Architecture

```
src/
├── App.js                 # Main application component
├── index.js              # Application entry point
├── components/           # Reusable components
│   ├── Layout/          # Layout components
│   ├── Trading/         # Trading-specific components
│   ├── Charts/          # Chart components
│   └── Common/          # Shared components
├── pages/               # Page components
│   ├── Dashboard.js     # Main dashboard
│   ├── Trading.js       # Trading interface
│   ├── Portfolio.js     # Portfolio analytics
│   └── Sentiment.js     # Sentiment analysis
├── services/            # API integration
│   └── api.js          # API client functions
├── hooks/               # Custom React hooks
├── utils/               # Utility functions
└── styles/              # Global styles
```

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- npm or yarn

### Installation & Setup
```bash
# Install dependencies
npm install

# Start development server
npm start

# Open browser to http://localhost:3000
```

### Environment Configuration
Create a `.env.local` file:
```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_APP_NAME="Trading Platform"
REACT_APP_VERSION=1.0.0
```

## 🧩 Components

### Layout Components

#### Navigation
**File**: `components/Layout/Navigation.js`
```jsx
// Main navigation bar with responsive menu
<Navigation>
  <NavLink to="/dashboard">Dashboard</NavLink>
  <NavLink to="/trading">Trading</NavLink>
  <NavLink to="/portfolio">Portfolio</NavLink>
</Navigation>
```

#### Layout
**File**: `components/Layout/Layout.js`
```jsx
// Main layout wrapper with navigation and content area
<Layout>
  <Navigation />
  <main className="container mx-auto px-4">
    {children}
  </main>
</Layout>
```

### Trading Components

#### TradeForm
**File**: `components/Trading/TradeForm.js`

Interactive form for creating new trades.

**Props:**
```jsx
<TradeForm 
  onSubmit={handleTradeSubmit}
  loading={isSubmitting}
  initialValues={{}}
/>
```

**Features:**
- Symbol validation and autocomplete
- Quantity input with validation
- Trade type selection (BUY/SELL)
- Real-time price preview
- Form validation and error handling

#### TradeList
**File**: `components/Trading/TradeList.js`

Displays list of trades with actions.

**Features:**
- Sortable columns (symbol, date, P&L)
- Close trade functionality
- Delete trade capability
- Status indicators
- Pagination support

### Chart Components

#### PortfolioChart
**File**: `components/Charts/PortfolioChart.js`

Interactive line chart showing portfolio performance over time.

```jsx
<PortfolioChart 
  data={portfolioHistory}
  height={400}
  showTooltip={true}
  animate={true}
/>
```

**Features:**
- Responsive design
- Hover tooltips
- Zoom and pan capabilities
- Customizable colors and styling
- Real-time data updates

#### SentimentChart
**File**: `components/Charts/SentimentChart.js`

Visualization of sentiment data across different stocks.

### Common Components

#### LoadingSpinner
```jsx
<LoadingSpinner size="lg" />
```

#### Button
```jsx
<Button 
  variant="primary" 
  size="md"
  onClick={handleClick}
  loading={isLoading}
>
  Execute Trade
</Button>
```

#### Modal
```jsx
<Modal 
  isOpen={showModal}
  onClose={handleClose}
  title="Confirm Trade"
>
  <TradeConfirmation />
</Modal>
```

## 📄 Pages

### Dashboard (`pages/Dashboard.js`)

Main dashboard providing overview of trading activity and portfolio performance.

**Key Features:**
- Portfolio value and performance metrics
- Interactive portfolio chart
- Recent trades list
- Top sentiment stocks
- Quick action buttons

**Data Sources:**
- Portfolio performance: `/api/performance`
- Portfolio history: `/api/portfolio-history`
- Recent trades: `/api/trades`
- Sentiment data: `/api/sentiment`

**Code Structure:**
```jsx
const Dashboard = () => {
  const { data: performance } = useQuery('performance', performanceAPI.getMetrics);
  const { data: portfolioHistory } = useQuery('portfolio-history', () => performanceAPI.getHistory(30));
  const { data: trades } = useQuery('trades', tradesAPI.getAll);
  
  return (
    <div className="space-y-6">
      <PerformanceMetrics data={performance} />
      <PortfolioChart data={portfolioHistory} />
      <RecentTrades trades={trades} />
    </div>
  );
};
```

### Trading (`pages/Trading.js`)

Dedicated trading interface for executing and managing trades.

**Features:**
- Trade execution form
- Real-time stock price lookup
- Trade history table
- Open positions management
- Bulk trade operations

### Portfolio (`pages/Portfolio.js`)

Comprehensive portfolio analytics and performance tracking.

**Features:**
- Detailed performance metrics
- Historical portfolio chart
- Asset allocation breakdown
- Trade performance analysis
- Export functionality

### Sentiment (`pages/Sentiment.js`)

Sentiment analysis dashboard with visualization tools.

**Features:**
- Sentiment scores by stock
- News sentiment timeline
- Bulk sentiment analysis
- Sentiment-based recommendations
- Market scanner integration

## 🔌 API Integration

### API Client (`services/api.js`)

Centralized API client with organized endpoints.

```javascript
// Base API configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' }
});

// Trading API
export const tradesAPI = {
  getAll: () => api.get('/api/trades').then(res => res.data),
  create: (trade) => api.post('/api/trades', trade).then(res => res.data),
  close: (id, closePrice) => api.post(`/api/trades/${id}/close`, { close_price: closePrice }),
  delete: (id) => api.delete(`/api/trades/${id}`)
};

// Performance API  
export const performanceAPI = {
  getMetrics: () => api.get('/api/performance').then(res => res.data),
  getHistory: (days = 30) => api.get(`/api/portfolio-history?days=${days}`).then(res => res.data)
};
```

### React Query Integration

Using React Query for efficient data fetching and caching:

```jsx
// Custom hooks for API calls
const usePortfolioData = () => {
  return useQuery('portfolio', performanceAPI.getMetrics, {
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 10000
  });
};

const useTrades = () => {
  return useQuery('trades', tradesAPI.getAll);
};

// Mutations for write operations
const useCreateTrade = () => {
  const queryClient = useQueryClient();
  
  return useMutation(tradesAPI.create, {
    onSuccess: () => {
      queryClient.invalidateQueries('trades');
      queryClient.invalidateQueries('portfolio');
    }
  });
};
```

### Error Handling

```jsx
// Global error boundary
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('App Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    return this.props.children;
  }
}
```

## 🎨 Styling

### Tailwind CSS

The application uses Tailwind CSS for styling with a custom configuration.

**Configuration** (`tailwind.config.js`):
```javascript
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8'
        }
      }
    }
  }
};
```

### Component Styling Patterns

```jsx
// Consistent styling patterns
const Button = ({ variant, size, children, ...props }) => {
  const baseStyles = "font-medium rounded-lg focus:ring-2 focus:ring-offset-2";
  const variants = {
    primary: "bg-primary-600 hover:bg-primary-700 text-white",
    secondary: "bg-gray-100 hover:bg-gray-200 text-gray-900"
  };
  const sizes = {
    sm: "px-3 py-2 text-sm",
    md: "px-4 py-2 text-base",
    lg: "px-6 py-3 text-lg"
  };
  
  return (
    <button 
      className={`${baseStyles} ${variants[variant]} ${sizes[size]}`}
      {...props}
    >
      {children}
    </button>
  );
};
```

### Responsive Design

```jsx
// Mobile-first responsive design
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <MetricCard title="Portfolio Value" />
  <MetricCard title="Total Return" />  
  <MetricCard title="Win Rate" />
</div>
```

## 🔄 State Management

### React Query for Server State

```jsx
// Query configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 3,
      refetchOnWindowFocus: false
    }
  }
});
```

### Local State with useState

```jsx
const TradingPage = () => {
  const [selectedStock, setSelectedStock] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [tradeType, setTradeType] = useState('BUY');
  
  // Component logic...
};
```

### Global State (Context API)

```jsx
// App context for global state
const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [settings, setSettings] = useState({});
  
  return (
    <AppContext.Provider value={{ user, settings, setUser, setSettings }}>
      {children}
    </AppContext.Provider>
  );
};
```

## 🛠️ Development

### Development Scripts
```bash
# Start development server
npm start

# Build for production  
npm run build

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Lint code
npm run lint

# Format code
npm run format
```

### Development Tools

#### Hot Reloading
Automatic browser refresh on file changes with Create React App.

#### Developer Tools
- React Developer Tools browser extension
- Redux DevTools (if using Redux)
- React Query DevTools

```jsx
// Enable React Query DevTools in development
import { ReactQueryDevtools } from 'react-query/devtools';

function App() {
  return (
    <>
      <Router>
        {/* App content */}
      </Router>
      {process.env.NODE_ENV === 'development' && <ReactQueryDevtools />}
    </>
  );
}
```

### Code Organization

#### File Naming Conventions
- Components: PascalCase (`TradeForm.js`)
- Pages: PascalCase (`Dashboard.js`)
- Utilities: camelCase (`formatCurrency.js`)
- Constants: UPPER_SNAKE_CASE (`API_ENDPOINTS.js`)

#### Import Organization
```jsx
// External imports
import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';

// Internal imports
import { tradesAPI } from '../services/api';
import { formatCurrency } from '../utils/formatting';
import Button from '../components/Common/Button';
```

## 🏗️ Building

### Production Build
```bash
# Create production build
npm run build

# Serve build locally for testing
npx serve -s build
```

### Build Optimization

#### Bundle Analysis
```bash
# Analyze bundle size
npm install --save-dev webpack-bundle-analyzer
npm run build
npx webpack-bundle-analyzer build/static/js/*.js
```

#### Performance Optimization
```jsx
// Code splitting with React.lazy
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Trading = React.lazy(() => import('./pages/Trading'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/trading" element={<Trading />} />
      </Routes>
    </Suspense>
  );
}
```

## 🧪 Testing

### Testing Setup
```bash
# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage --collectCoverageFrom=src/**/*.js

# Run tests in watch mode
npm test -- --watch
```

### Testing Patterns

#### Component Testing
```jsx
// TradeForm.test.js
import { render, screen, fireEvent } from '@testing-library/react';
import TradeForm from './TradeForm';

describe('TradeForm', () => {
  test('submits form with correct data', () => {
    const mockSubmit = jest.fn();
    render(<TradeForm onSubmit={mockSubmit} />);
    
    fireEvent.change(screen.getByLabelText('Symbol'), { target: { value: 'AAPL' } });
    fireEvent.change(screen.getByLabelText('Quantity'), { target: { value: '10' } });
    fireEvent.click(screen.getByText('Buy'));
    
    expect(mockSubmit).toHaveBeenCalledWith({
      symbol: 'AAPL',
      quantity: 10,
      trade_type: 'BUY'
    });
  });
});
```

#### API Testing
```jsx
// api.test.js
import { tradesAPI } from './api';

describe('tradesAPI', () => {
  test('creates trade successfully', async () => {
    const mockTrade = { symbol: 'AAPL', quantity: 10, trade_type: 'BUY' };
    const result = await tradesAPI.create(mockTrade);
    
    expect(result.symbol).toBe('AAPL');
    expect(result.status).toBe('OPEN');
  });
});
```

### Test Configuration
```javascript
// setupTests.js
import '@testing-library/jest-dom';

// Mock environment variables
process.env.REACT_APP_API_URL = 'http://localhost:8000';

// Mock React Query
jest.mock('react-query', () => ({
  useQuery: jest.fn(),
  useMutation: jest.fn(),
  useQueryClient: jest.fn()
}));
```

## 📱 Responsive Design

### Breakpoints
```javascript
// Tailwind breakpoints
sm: '640px'   // Small screens
md: '768px'   // Medium screens  
lg: '1024px'  // Large screens
xl: '1280px'  // Extra large screens
```

### Mobile-First Approach
```jsx
// Responsive grid layout
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  {/* Cards */}
</div>

// Responsive text
<h1 className="text-2xl md:text-4xl lg:text-6xl font-bold">
  Portfolio Dashboard
</h1>
```

## 🔧 Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   # Clear npm cache
   npm cache clean --force
   
   # Delete node_modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **CORS Issues**
   ```bash
   # Ensure backend CORS settings include frontend URL
   CORS_ORIGINS=["http://localhost:3000"]
   ```

3. **API Connection Issues**
   ```bash
   # Verify backend is running
   curl http://localhost:8000/api/trades
   
   # Check environment variables
   echo $REACT_APP_API_URL
   ```

4. **Styling Issues**
   ```bash
   # Rebuild Tailwind styles
   npm run build:css
   ```

### Debug Mode
```jsx
// Enable debug logging
const DEBUG = process.env.NODE_ENV === 'development';

const debugLog = (...args) => {
  if (DEBUG) console.log('[DEBUG]', ...args);
};
```

---

## 📚 Additional Resources

- [React Documentation](https://reactjs.org/docs/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [React Query Documentation](https://react-query.tanstack.com/)
- [Recharts Documentation](https://recharts.org/en-US/)
- [Axios Documentation](https://axios-http.com/docs/intro)

---

## 🤝 Contributing

### Development Workflow
1. Create feature branch from `main`
2. Implement changes with tests
3. Ensure all tests pass
4. Submit pull request with description

### Code Style Guidelines
- Use functional components with hooks
- Follow React best practices
- Add PropTypes or TypeScript for type checking
- Write meaningful component and variable names
- Keep components small and focused

### Pull Request Checklist
- [ ] Tests pass (`npm test`)
- [ ] Build succeeds (`npm run build`)
- [ ] Code follows style guidelines
- [ ] Components are responsive
- [ ] Accessibility standards met
- [ ] Documentation updated

---

For additional help, refer to the main project README or open an issue on GitHub.