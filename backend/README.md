# Trading Platform Backend

A FastAPI-based backend service providing comprehensive trading, sentiment analysis, and market data APIs.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Services](#services)
- [Database Models](#database-models)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)

## 🎯 Overview

The backend is built with FastAPI and provides REST APIs for:
- Paper trading simulation
- Real-time market data collection
- News sentiment analysis
- Portfolio performance tracking
- Automated trading strategies
- Market discovery and scanning

### Tech Stack
- **Framework**: FastAPI 0.68+
- **Database**: SQLAlchemy with SQLite/PostgreSQL
- **Data Sources**: Yahoo Finance, News APIs
- **Sentiment Analysis**: VADER, TextBlob
- **Async Support**: Native async/await
- **Documentation**: Auto-generated OpenAPI/Swagger

## 🏗️ Architecture

```
┌─────────────────┐
│   FastAPI App   │
│   (main.py)     │
├─────────────────┤
│   Services      │
│  ┌─────────────┐ │
│  │ Trading     │ │  ┌─────────────┐
│  │ Sentiment   │ ├──┤ Database    │
│  │ Data        │ │  │ (SQLAlchemy)│
│  │ Recommender │ │  └─────────────┘
│  │ Scanner     │ │
│  └─────────────┘ │
├─────────────────┤
│   Scheduler     │  ┌─────────────┐
│  (Background)   ├──┤ External    │
│                 │  │ APIs        │
└─────────────────┘  └─────────────┘
```

### Core Components

1. **main.py** - FastAPI application with all endpoints
2. **services/** - Business logic layer
3. **scheduler.py** - Background data collection
4. **models.py** - Database schema definitions
5. **config.py** - Configuration management

## 🚀 API Reference

### Quick Start
```bash
# Start the server
python main.py

# View API documentation
open http://localhost:8000/docs
```

### Authentication
Currently, no authentication is required. All endpoints are public for development.

### Base URL
```
http://localhost:8000
```

---

## 📊 Trading Endpoints

### Get All Trades
```http
GET /api/trades
```
Returns all paper trades with performance data.

**Response:**
```json
[
  {
    "id": 1,
    "symbol": "AAPL",
    "trade_type": "BUY",
    "quantity": 15,
    "price": 213.55,
    "total_value": 3203.25,
    "timestamp": "2025-07-04T18:47:13",
    "status": "CLOSED",
    "profit_loss": 104.25,
    "close_price": 220.50
  }
]
```

### Create Trade
```http
POST /api/trades
```

**Request Body:**
```json
{
  "symbol": "AAPL",
  "trade_type": "BUY",
  "quantity": 10,
  "strategy": "MANUAL"
}
```

### Close Trade
```http
POST /api/trades/{trade_id}/close
```

**Request Body:**
```json
{
  "close_price": 220.50  // Optional, uses current market price if not provided
}
```

---

## 📈 Portfolio Endpoints

### Get Performance Metrics
```http
GET /api/performance
```

**Response:**
```json
{
  "total_trades": 5,
  "winning_trades": 3,
  "losing_trades": 2,
  "total_profit_loss": 245.75,
  "win_rate": 60.0,
  "current_balance": 100245.75,
  "total_return": 0.25
}
```

### Get Portfolio History
```http
GET /api/portfolio-history?days=30
```
Returns historical portfolio values for charting.

---

## 📰 Sentiment Analysis Endpoints

### Get All Sentiment Data
```http
GET /api/sentiment
```

### Get Symbol Sentiment
```http
GET /api/sentiment/{symbol}
```

### Trigger Sentiment Analysis
```http
POST /api/analyze-sentiment
```

**Request Body:**
```json
{
  "symbol": "AAPL"
}
```

### Bulk Sentiment Analysis
```http
POST /api/analyze-bulk-sentiment
```

**Request Body:**
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL"]
}
```

---

## 🤖 Strategy & Recommendations

### Run Trading Strategy
```http
POST /api/run-strategy
```
Executes sentiment-based automated trading.

### Generate Recommendations
```http
POST /api/generate-recommendations
```

### Get Pending Recommendations
```http
GET /api/recommendations
```

### Approve Recommendation
```http
POST /api/recommendations/{id}/approve
```

---

## 🔍 Market Discovery

### Market Scan
```http
POST /api/market-scan?limit=10
```
Scans news for trending stocks.

### Auto Discovery
```http
POST /api/auto-discover?min_trending_score=0.5
```
Discovers and analyzes trending stocks automatically.

### Full Pipeline
```http
POST /api/discovery-to-recommendations
```
Complete pipeline: discover → analyze → recommend.

---

## 📊 Stock Data Endpoints

### Get Tracked Stocks
```http
GET /api/stocks
```

### Add Stock to Tracking
```http
POST /api/stocks
```

**Request Body:**
```json
{
  "symbol": "AAPL"
}
```

### Get Market Data
```http
GET /api/market-data/{symbol}?days=30
```

---

## 🔧 Services

### TradingService
**File:** `services/trading_service.py`

Handles all trading operations and portfolio calculations.

**Key Methods:**
- `create_trade()` - Execute paper trades
- `close_trade()` - Close positions with P&L calculation
- `get_performance_metrics()` - Calculate portfolio statistics
- `run_sentiment_strategy()` - Automated trading based on sentiment

**Example Usage:**
```python
from services.trading_service import TradingService

service = TradingService()
trade = service.create_trade(db, TradeCreate(
    symbol="AAPL",
    trade_type="BUY", 
    quantity=10
))
```

### SentimentService
**File:** `services/sentiment_service.py`

Analyzes news sentiment and generates sentiment scores.

**Key Methods:**
- `analyze_stock_sentiment()` - Analyze single stock
- `get_stock_sentiment()` - Retrieve sentiment data
- `run_daily_sentiment_analysis()` - Bulk analysis

**Features:**
- Multi-source news aggregation
- VADER and TextBlob sentiment analysis
- Sentiment score normalization
- Historical sentiment tracking

### DataService
**File:** `services/data_service.py`

Manages market data collection and storage.

**Key Methods:**
- `get_market_data()` - Fetch stock prices
- `add_stock()` - Add symbol to tracking
- `run_daily_data_collection()` - Bulk data update

**Data Sources:**
- Primary: Yahoo Finance API
- Fallback: Mock data (for development)
- Alternative: Alpha Vantage (with API key)

### RecommendationService
**File:** `services/recommendation_service.py`

Generates AI-powered trading recommendations.

**Key Methods:**
- `generate_recommendations()` - Create trade suggestions
- `approve_recommendation()` - Execute approved trades
- `get_pending_recommendations()` - List pending suggestions

### MarketScannerService
**File:** `services/market_scanner.py`

Discovers trending stocks from news analysis.

**Key Methods:**
- `scan_trending_stocks()` - Find trending symbols
- `auto_discover_and_analyze()` - Full discovery pipeline
- `calculate_trending_score()` - Score symbol popularity

---

## 🗄️ Database Models

### Trade
```python
class Trade(Base):
    id: int
    symbol: str
    trade_type: str  # "BUY" or "SELL"
    quantity: int
    price: float
    total_value: float
    timestamp: datetime
    status: str  # "OPEN" or "CLOSED"
    profit_loss: float
    close_price: float
    strategy: str
```

### SentimentData
```python
class SentimentData(Base):
    id: int
    symbol: str
    overall_sentiment: float  # -1.0 to 1.0
    news_sentiment: float
    social_sentiment: float
    confidence_score: float
    timestamp: datetime
    sources_count: int
```

### StockData
```python
class StockData(Base):
    id: int
    symbol: str
    current_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: int
    market_cap: float
    timestamp: datetime
```

### TradeRecommendation
```python
class TradeRecommendation(Base):
    id: int
    symbol: str
    recommendation_type: str
    confidence_score: float
    reasoning: str
    target_price: float
    status: str
    timestamp: datetime
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=sqlite:///trading.db

# Trading Configuration
INITIAL_BALANCE=100000.0
MAX_POSITION_SIZE=0.05
SENTIMENT_THRESHOLD=0.1

# Market Hours (24-hour format)
MARKET_OPEN_TIME=09:30
MARKET_CLOSE_TIME=16:00
SENTIMENT_ANALYSIS_TIME=10:00
STRATEGY_EXECUTION_TIME=10:30

# API Keys (Optional)
NEWS_API_KEY=your_news_api_key_here
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here

# CORS Settings
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Logging
LOG_LEVEL=INFO
LOG_FILE=trading.log
```

### Configuration Class
```python
# config.py
class Config:
    DATABASE_URL: str
    INITIAL_BALANCE: float = 100000.0
    MAX_POSITION_SIZE: float = 0.05
    MARKET_OPEN_TIME: str = "09:30"
    MARKET_CLOSE_TIME: str = "16:00"
    
    # API Keys (optional)
    NEWS_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_KEY: Optional[str] = None
```

---

## 🛠️ Development

### Setup Development Environment
```bash
# Create virtual environment
python -m venv trading_env
source trading_env/bin/activate  # Windows: trading_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black isort flake8

# Setup database
python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### Running in Development Mode
```bash
# With auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using the main script
python main.py
```

### Code Quality
```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type checking
mypy .
```

### Database Operations
```bash
# View database schema
sqlite3 trading.db ".schema"

# Reset database
rm trading.db
python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"

# Backup database
cp trading.db trading_backup.db
```

---

## 🧪 Testing

### Run Tests
```bash
# All tests
python -m pytest

# With coverage
python -m pytest --cov=.

# Specific test file
python -m pytest tests/test_trading_service.py

# Verbose output
python -m pytest -v
```

### Test Files
- `test_workflow.py` - End-to-end workflow tests
- `test_frontend_apis.py` - API integration tests
- `test_app.py` - Application tests

### Manual Testing Scripts
```bash
# Test complete workflow
python test_workflow.py

# Test all APIs
python test_frontend_apis.py
```

---

## 📦 Background Scheduler

### Running the Scheduler
```bash
# Run scheduler (keeps running)
python scheduler.py
```

### Scheduler Features
- **Market Open**: Data collection at 09:30
- **Hourly Updates**: Throughout trading day
- **Sentiment Analysis**: Daily at 10:00
- **Strategy Execution**: Daily at 10:30
- **Market Close**: Final collection at 16:00

### Schedule Configuration
```python
# Modify schedule in scheduler.py
schedule.every().day.at("09:30").do(collect_data)
schedule.every().hour.do(collect_data)
schedule.every().day.at("10:00").do(analyze_sentiment)
```

---

## 🚀 Deployment

### Production Setup
```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# With environment variables
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Docker Deployment
```dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Environment-Specific Settings
```bash
# Development
export ENVIRONMENT=development

# Production
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:pass@localhost/trading
```

---

## 📝 Logging

### Log Configuration
```python
import logging

# Setup in config.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading.log'),
        logging.StreamHandler()
    ]
)
```

### Log Files
- `trading.log` - Application logs
- Service-specific logging with detailed trade information
- Error tracking with full stack traces

---

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Reset database
   rm trading.db
   python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

2. **API Key Issues**
   ```bash
   # Check environment variables
   python -c "import os; print(os.getenv('NEWS_API_KEY', 'Not set'))"
   ```

3. **Port Already in Use**
   ```bash
   # Kill process on port 8000
   lsof -ti:8000 | xargs kill -9
   ```

4. **Module Import Errors**
   ```bash
   # Ensure you're in the backend directory
   cd backend
   python main.py
   ```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Yahoo Finance API](https://pypi.org/project/yfinance/)
- [VADER Sentiment Analysis](https://github.com/cjhutto/vaderSentiment)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Code Style
- Follow PEP 8
- Use type hints
- Add docstrings to all functions
- Keep functions under 50 lines when possible

---

For questions or issues, please refer to the main project README or open an issue on GitHub.