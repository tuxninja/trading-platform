# Trading Sentiment Analysis SaaS Platform

A comprehensive SaaS paper trading platform that uses sentiment analysis to generate trading recommendations and track portfolio performance. Built for traders, investors, and financial professionals who want to test strategies risk-free.

![Trading Platform](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)
![React](https://img.shields.io/badge/React-18+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)

## 📚 Documentation

### Setup Guides
- **[Development Setup](docs/DEVELOPMENT_SETUP.md)** - Complete guide for local development
- **[Google OAuth Setup](docs/GOOGLE_OAUTH_SETUP.md)** - Configure Google authentication
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment instructions

### Operations
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Deployment Checklist](docs/DEPLOYMENT_CHECKLIST.md)** - Pre/post deployment verification
- **[SaaS Operations](docs/SAAS_OPERATIONS.md)** - Advanced operational procedures

### Technical Reference
- **[API Documentation](backend/docs/api.md)** - Complete API reference
- **[Database Schema](backend/docs/database.md)** - Database structure and models
- **[Configuration Guide](backend/docs/configuration.md)** - Environment variables and settings
- **[Claude AI Reference](CLAUDE.md)** - Context and guidelines for AI assistance

## 🎯 Overview

The Trading Sentiment Analysis Platform is a full-stack application that combines real-time market data, news sentiment analysis, and automated trading strategies to help users make informed investment decisions through paper trading.

### Key Technologies
- **Backend**: FastAPI (Python), SQLAlchemy, PostgreSQL/SQLite
- **Frontend**: React, Tailwind CSS, Recharts
- **Data Sources**: Yahoo Finance API, News APIs, Alternative free sources
- **Sentiment Analysis**: VADER, TextBlob
- **Scheduling**: Python `schedule` library

## ✨ Features

### Trading & Portfolio Management
- 📊 **Paper Trading**: Risk-free trading simulation with real market data
- 💼 **Portfolio Tracking**: Real-time portfolio value and performance metrics
- 📈 **Historical Performance**: Interactive charts showing portfolio evolution
- 🎯 **Position Management**: Track open/closed positions with detailed P&L

### Sentiment Analysis
- 📰 **News Sentiment**: Automated analysis of financial news and articles
- 🔍 **Multi-Source Data**: Yahoo Finance, MarketWatch, Reuters, CNBC
- 🧠 **Smart Recommendations**: AI-powered trade suggestions based on sentiment
- 📊 **Sentiment Scoring**: Comprehensive sentiment metrics per stock

### Market Intelligence
- 🔍 **Market Scanner**: Discover trending stocks from news analysis
- 📋 **Stock Watchlists**: Track multiple securities with real-time updates
- 📈 **Technical Indicators**: Market cap, P/E ratios, dividend yields
- 🚨 **Alert System**: Notifications for significant sentiment changes

### Automation & Scheduling
- ⏰ **Automated Data Collection**: Scheduled market data updates
- 🤖 **Strategy Execution**: Automated trading based on sentiment signals
- 📅 **Flexible Scheduling**: Configurable collection intervals
- 🔄 **Background Processing**: Non-blocking data updates

### Analytics & Reporting
- 📊 **Performance Metrics**: Win rate, Sharpe ratio, max drawdown
- 📈 **Interactive Charts**: Real-time portfolio performance visualization
- 📋 **Trade History**: Detailed records of all trading activity
- 💰 **P&L Analysis**: Comprehensive profit/loss tracking

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend │────│   FastAPI Backend │────│   Database      │
│   (Port 3000)    │    │   (Port 8000)     │    │   (SQLite/PG)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼────────┐ ┌───────▼────────┐
            │  Data Scheduler │ │  External APIs │
            │  (Background)   │ │  (Yahoo, News) │
            └────────────────┘ └────────────────┘
```

### Backend Services
- **Trading Service**: Handles paper trades and portfolio calculations
- **Sentiment Service**: Analyzes news and generates sentiment scores
- **Data Service**: Collects and manages market data
- **Recommendation Service**: Generates AI-powered trading suggestions
- **Market Scanner**: Discovers trending stocks from news
- **Scheduler Service**: Manages automated data collection

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker (optional)
- Git

### Option 1: Complete Setup (Recommended)
For first-time setup with Google OAuth and all features:

👉 **Follow the [Development Setup Guide](docs/DEVELOPMENT_SETUP.md)** for step-by-step instructions.

### Option 2: Basic Demo (Quick Test)
```bash
# Clone the repository
git clone https://github.com/yourusername/trading-platform.git
cd trading-platform

# Start backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py

# Start frontend (new terminal)
cd frontend
npm install
npm start

# Visit http://localhost:3000
```

**Note**: For Google OAuth login to work, you'll need to configure Google Cloud credentials. See [Google OAuth Setup Guide](docs/GOOGLE_OAUTH_SETUP.md).

### Need Help?
- 🐛 **Issues?** Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- 🚀 **Deploying?** See the [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- 💬 **Questions?** Review the [Claude AI Reference](CLAUDE.md) for context

## 📦 Installation

### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv trading_env
source trading_env/bin/activate  # Windows: trading_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"

# Start the API server
python main.py
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your settings

# Start development server
npm start
```

## 🎮 Usage

### Basic Trading Workflow

1. **Start the Application**
   ```bash
   # Terminal 1: Backend
   cd backend && python main.py
   
   # Terminal 2: Frontend  
   cd frontend && npm start
   ```

2. **Access the Dashboard**
   - Open http://localhost:3000
   - View portfolio performance and recent trades
   - Monitor sentiment analysis results

3. **Execute Trades**
   - Navigate to "Trading" section
   - Enter stock symbol, quantity, and trade type
   - Submit paper trade (uses real market prices)

4. **Run Sentiment Analysis**
   ```bash
   # Manual analysis
   curl -X POST http://localhost:8000/api/analyze-sentiment -d '{"symbol": "AAPL"}'
   
   # Bulk analysis
   curl -X POST http://localhost:8000/api/analyze-bulk-sentiment \
     -d '{"symbols": ["AAPL", "MSFT", "GOOGL"]}'
   ```

5. **Automated Data Collection**
   ```bash
   # Run the scheduler for automated updates
   cd backend
   python scheduler.py
   ```

### Advanced Features

#### Market Discovery
```bash
# Scan for trending stocks
curl -X POST http://localhost:8000/api/market-scan

# Auto-discover and analyze
curl -X POST http://localhost:8000/api/auto-discover

# Full discovery pipeline
curl -X POST http://localhost:8000/api/discovery-to-recommendations
```

#### Strategy Execution
```bash
# Run sentiment-based trading strategy
curl -X POST http://localhost:8000/api/run-strategy
```

## 📚 API Documentation

### Core Endpoints

#### Trading
- `GET /api/trades` - List all trades
- `POST /api/trades` - Create new trade
- `POST /api/trades/{id}/close` - Close existing trade
- `DELETE /api/trades/{id}` - Delete trade

#### Portfolio
- `GET /api/performance` - Portfolio metrics and P&L
- `GET /api/portfolio-history` - Historical portfolio values

#### Sentiment
- `GET /api/sentiment` - All sentiment data
- `GET /api/sentiment/{symbol}` - Symbol-specific sentiment
- `POST /api/analyze-sentiment` - Trigger analysis

#### Market Data
- `GET /api/stocks` - Tracked stocks
- `POST /api/stocks` - Add stock to tracking
- `GET /api/market-data/{symbol}` - Historical market data

For complete API documentation, see [Backend API Documentation](backend/docs/api.md).

## ⚙️ Configuration

### Environment Variables

#### Backend Configuration (.env)
```bash
# Database
DATABASE_URL=sqlite:///trading.db

# Trading Settings
INITIAL_BALANCE=100000.0
MAX_POSITION_SIZE=0.05

# Market Hours
MARKET_OPEN_TIME=09:30
MARKET_CLOSE_TIME=16:00

# API Keys (Optional)
NEWS_API_KEY=your_news_api_key
ALPHA_VANTAGE_KEY=your_alpha_vantage_key

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

#### Frontend Configuration (.env.local)
```bash
REACT_APP_API_URL=http://localhost:8000
```

### Scheduler Configuration
The scheduler automatically runs:
- Market data collection at market open
- Hourly data updates during trading hours
- Daily sentiment analysis at 10:00 AM
- Strategy execution at 10:30 AM
- End-of-day collection at market close

## 🛠️ Development

### Backend Development
```bash
cd backend

# Install development dependencies
pip install -r requirements-dev.txt

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest tests/

# Code formatting
black .
isort .
```

### Frontend Development
```bash
cd frontend

# Install development dependencies
npm install

# Start with hot reload
npm start

# Run tests
npm test

# Build for production
npm run build
```

### Database Management
```bash
# Reset database
rm backend/trading.db
python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"

# View database schema
sqlite3 backend/trading.db ".schema"
```

## 🧪 Testing

### Backend Tests
```bash
cd backend

# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=.

# Run specific test files
python test_workflow.py
python test_frontend_apis.py
```

### Frontend Tests
```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

### API Testing
```bash
# Test workflow script
cd backend
python test_workflow.py

# Test frontend APIs
python test_frontend_apis.py
```

## 📁 Project Structure

```
trading-platform/
├── README.md
├── backend/
│   ├── README.md
│   ├── main.py              # FastAPI application
│   ├── scheduler.py         # Background data scheduler
│   ├── config.py           # Configuration management
│   ├── database.py         # Database setup
│   ├── models.py           # SQLAlchemy models
│   ├── schemas.py          # Pydantic schemas
│   ├── exceptions.py       # Custom exceptions
│   ├── services/           # Business logic
│   │   ├── trading_service.py
│   │   ├── sentiment_service.py
│   │   ├── data_service.py
│   │   ├── recommendation_service.py
│   │   └── market_scanner.py
│   ├── docs/               # Backend documentation
│   ├── tests/              # Test files
│   └── requirements.txt
├── frontend/
│   ├── README.md
│   ├── public/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API integration
│   │   └── App.js
│   ├── package.json
│   └── tailwind.config.js
└── docs/                   # Project documentation
```

## 🔐 Authentication

The platform uses Google OAuth for secure user authentication:

1. **Setup Google OAuth:**
   - Create a Google Cloud project
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add your domain to authorized origins

2. **Configure Environment:**
   ```bash
   # Backend (.env)
   GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
   JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
   
   # Frontend (.env.local)
   REACT_APP_GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
   ```

3. **Features:**
   - Secure JWT-based session management
   - Automatic token refresh
   - Protected routes and API endpoints
   - User profile integration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋 Support

- 📚 Documentation: Check the `/docs` folder and service-specific READMEs
- 🐛 Issues: Report technical issues or bugs
- 📧 Contact: For business inquiries and support

## 🔮 Roadmap

- [ ] Real trading integration (Alpaca, Interactive Brokers)
- [ ] Advanced technical indicators
- [ ] Machine learning models for prediction
- [ ] Mobile application
- [x] User authentication with Google OAuth
- [ ] Advanced portfolio analytics
- [ ] Options trading support
- [ ] Real-time WebSocket updates
- [ ] Subscription-based SaaS features

---

**⚠️ Disclaimer**: This is a paper trading platform for educational purposes only. Past performance does not guarantee future results. Always consult with financial professionals before making real investment decisions.