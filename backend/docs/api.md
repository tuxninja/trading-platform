# API Documentation

Comprehensive REST API documentation for the Trading Sentiment Analysis Platform.

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL & Headers](#base-url--headers)
- [Error Handling](#error-handling)
- [Trading API](#trading-api)
- [Portfolio API](#portfolio-api)
- [Sentiment Analysis API](#sentiment-analysis-api)
- [Market Data API](#market-data-api)
- [Recommendations API](#recommendations-api)
- [Strategy API](#strategy-api)
- [Market Discovery API](#market-discovery-api)
- [Utility Endpoints](#utility-endpoints)
- [WebSocket Events](#websocket-events)
- [SDK Examples](#sdk-examples)

## 🎯 Overview

The Trading Platform API is a RESTful service built with FastAPI, providing endpoints for paper trading, sentiment analysis, and market data management.

### API Characteristics
- **Format**: JSON
- **Protocol**: HTTP/HTTPS
- **Rate Limiting**: None (development)
- **Pagination**: Limit/offset based
- **Versioning**: None (v1 implied)

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 🔐 Authentication

Currently, the API operates without authentication for development purposes.

### Future Authentication (Planned)
```http
Authorization: Bearer <jwt_token>
```

## 🌐 Base URL & Headers

### Base URL
```
http://localhost:8000  # Development
https://api.trading-platform.com  # Production
```

### Required Headers
```http
Content-Type: application/json
Accept: application/json
```

### Optional Headers
```http
X-Request-ID: unique-request-identifier
User-Agent: TradingApp/1.0
```

## ❌ Error Handling

### Error Response Format
```json
{
  "detail": "Error message description",
  "type": "error_type",
  "code": "ERROR_CODE"
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

### Common Error Examples
```json
// Validation Error (422)
{
  "detail": [
    {
      "loc": ["body", "quantity"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt",
      "ctx": {"limit_value": 0}
    }
  ]
}

// Business Logic Error (400)
{
  "detail": "Insufficient balance: $5000.00 available, $10000.00 required"
}
```

---

## 💰 Trading API

### Get All Trades
Retrieve all paper trades with optional filtering.

```http
GET /api/trades
```

**Query Parameters:**
- `status` (optional): Filter by trade status (`OPEN`, `CLOSED`)
- `symbol` (optional): Filter by stock symbol
- `limit` (optional): Number of trades to return (default: 100)
- `offset` (optional): Number of trades to skip (default: 0)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/trades?status=OPEN&limit=10"
```

**Response (200):**
```json
[
  {
    "id": 1,
    "symbol": "AAPL",
    "trade_type": "BUY",
    "quantity": 15,
    "price": 213.55,
    "total_value": 3203.25,
    "strategy": "SENTIMENT_RECOMMENDATION",
    "timestamp": "2025-07-04T18:47:13.000000",
    "status": "CLOSED",
    "sentiment_score": 0.12,
    "profit_loss": 104.25,
    "close_timestamp": "2025-07-04T19:04:06.909868",
    "close_price": 220.5
  }
]
```

### Create Trade
Execute a new paper trade.

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

**Field Validation:**
- `symbol`: 1-10 characters, alphabetic
- `trade_type`: Must be "BUY" or "SELL"
- `quantity`: Positive integer
- `strategy`: Optional, defaults to "MANUAL"

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/trades" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "MSFT",
    "trade_type": "BUY",
    "quantity": 5,
    "strategy": "SENTIMENT"
  }'
```

**Response (201):**
```json
{
  "id": 15,
  "symbol": "MSFT",
  "trade_type": "BUY", 
  "quantity": 5,
  "price": 374.92,
  "total_value": 1874.60,
  "strategy": "SENTIMENT",
  "timestamp": "2025-07-19T15:30:22.123456",
  "status": "OPEN",
  "sentiment_score": null,
  "profit_loss": null,
  "close_timestamp": null,
  "close_price": null
}
```

### Get Trade by ID
Retrieve a specific trade.

```http
GET /api/trades/{trade_id}
```

**Response (200):**
```json
{
  "id": 15,
  "symbol": "MSFT",
  "trade_type": "BUY",
  "quantity": 5,
  "price": 374.92,
  "total_value": 1874.60,
  "status": "OPEN"
}
```

**Response (404):**
```json
{
  "detail": "Trade with ID 999 not found"
}
```

### Close Trade
Close an open position and calculate profit/loss.

```http
POST /api/trades/{trade_id}/close
```

**Request Body (Optional):**
```json
{
  "close_price": 380.25
}
```

If `close_price` is not provided, current market price is used.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/trades/15/close" \
  -H "Content-Type: application/json" \
  -d '{"close_price": 385.00}'
```

**Response (200):**
```json
{
  "id": 15,
  "symbol": "MSFT",
  "trade_type": "BUY",
  "quantity": 5,
  "price": 374.92,
  "close_price": 385.00,
  "profit_loss": 50.40,
  "status": "CLOSED",
  "close_timestamp": "2025-07-19T16:45:30.789012"
}
```

### Delete Trade
Delete an open trade (cannot delete closed trades).

```http
DELETE /api/trades/{trade_id}
```

**Response (200):**
```json
{
  "message": "Trade 15 deleted successfully"
}
```

**Error (400):**
```json
{
  "detail": "Cannot delete closed trade"
}
```

---

## 📊 Portfolio API

### Get Performance Metrics
Retrieve comprehensive portfolio performance data.

```http
GET /api/performance
```

**Response (200):**
```json
{
  "total_trades": 5,
  "winning_trades": 3,
  "losing_trades": 1,
  "total_profit_loss": 245.75,
  "win_rate": 75.0,
  "average_profit": 81.92,
  "average_loss": -35.50,
  "max_drawdown": 5.2,
  "sharpe_ratio": 1.35,
  "current_balance": 100245.75,
  "total_return": 0.25
}
```

**Metrics Explained:**
- `win_rate`: Percentage of profitable trades
- `max_drawdown`: Maximum portfolio decline from peak (%)
- `sharpe_ratio`: Risk-adjusted return measure
- `total_return`: Overall portfolio return (%)

### Get Portfolio History
Retrieve historical portfolio values for charting.

```http
GET /api/portfolio-history
```

**Query Parameters:**
- `days` (optional): Number of days of history (default: 30)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/portfolio-history?days=7"
```

**Response (200):**
```json
[
  {
    "date": "2025-07-12",
    "value": 100000.00
  },
  {
    "date": "2025-07-13",
    "value": 100000.00
  },
  {
    "date": "2025-07-04",
    "value": 96796.75
  },
  {
    "date": "2025-07-04",
    "value": 100104.25
  },
  {
    "date": "2025-07-19",
    "value": 85976.56
  }
]
```

---

## 📰 Sentiment Analysis API

### Get All Sentiment Data
Retrieve sentiment analysis for all tracked stocks.

```http
GET /api/sentiment
```

**Response (200):**
```json
[
  {
    "id": 1,
    "symbol": "AAPL",
    "overall_sentiment": 0.125,
    "news_sentiment": 0.089,
    "social_sentiment": 0.161,
    "confidence_score": 0.75,
    "sources_count": 12,
    "analysis_date": "2025-07-19",
    "timestamp": "2025-07-19T10:00:00.000000"
  }
]
```

### Get Sentiment for Symbol
Retrieve sentiment analysis for a specific stock.

```http
GET /api/sentiment/{symbol}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/sentiment/AAPL"
```

**Response (200):**
```json
{
  "symbol": "AAPL",
  "overall_sentiment": 0.125,
  "news_sentiment": 0.089,
  "social_sentiment": 0.161,
  "confidence_score": 0.75,
  "sources_count": 12,
  "positive_articles": 8,
  "negative_articles": 2,
  "neutral_articles": 2
}
```

### Trigger Sentiment Analysis
Manually trigger sentiment analysis for a stock.

```http
POST /api/analyze-sentiment
```

**Request Body:**
```json
{
  "symbol": "TSLA"
}
```

**Response (200):**
```json
{
  "symbol": "TSLA",
  "overall_sentiment": -0.043,
  "news_sentiment": -0.12,
  "social_sentiment": 0.034,
  "confidence_score": 0.68,
  "sources_count": 8,
  "message": "Sentiment analysis completed for TSLA"
}
```

### Bulk Sentiment Analysis
Analyze sentiment for multiple stocks.

```http
POST /api/analyze-bulk-sentiment
```

**Request Body:**
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN"],
  "force_refresh": true
}
```

**Response (200):**
```json
{
  "results": [
    {
      "symbol": "AAPL",
      "overall_sentiment": 0.125,
      "status": "success"
    },
    {
      "symbol": "MSFT", 
      "overall_sentiment": 0.089,
      "status": "success"
    }
  ],
  "errors": [
    "Failed to analyze INVALID_SYMBOL: Invalid stock symbol"
  ],
  "total_processed": 4,
  "successful": 3,
  "failed": 1
}
```

### Full Analysis Cycle
Run complete sentiment analysis and generate recommendations.

```http
POST /api/full-analysis-cycle
```

**Request Body (Optional):**
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL"]
}
```

If no symbols provided, analyzes all tracked stocks.

**Response (200):**
```json
{
  "sentiment_analysis": {
    "successful": 15,
    "failed": 1,
    "errors": ["Failed to analyze XYZ: API timeout"]
  },
  "recommendations": {
    "generated": 8,
    "recommendations": [
      {
        "symbol": "AAPL",
        "recommendation_type": "BUY",
        "confidence_score": 0.78,
        "reasoning": "Strong positive sentiment with high confidence"
      }
    ]
  },
  "summary": "Analyzed 15 stocks, generated 8 recommendations"
}
```

---

## 📈 Market Data API

### Get Tracked Stocks
List all stocks being tracked for analysis.

```http
GET /api/stocks
```

**Response (200):**
```json
[
  {
    "symbol": "AAPL",
    "company_name": "Apple Inc.",
    "current_price": 220.50,
    "market_cap": 3400000000000,
    "sector": "Technology"
  },
  {
    "symbol": "MSFT",
    "company_name": "Microsoft Corporation", 
    "current_price": 385.00,
    "market_cap": 2850000000000,
    "sector": "Technology"
  }
]
```

### Add Stock to Tracking
Add a new stock symbol to the tracking list.

```http
POST /api/stocks
```

**Request Body:**
```json
{
  "symbol": "NVDA"
}
```

**Response (201):**
```json
{
  "symbol": "NVDA",
  "company_name": "NVIDIA Corporation",
  "message": "Stock NVDA added to tracking successfully"
}
```

### Get Market Data
Retrieve historical market data for a stock.

```http
GET /api/market-data/{symbol}
```

**Query Parameters:**
- `days` (optional): Number of days of historical data (default: 30)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/market-data/AAPL?days=7"
```

**Response (200):**
```json
{
  "symbol": "AAPL",
  "data": [
    {
      "date": "2025-07-12",
      "open": 215.20,
      "high": 218.90,
      "low": 213.45,
      "close": 217.80,
      "volume": 45623000
    },
    {
      "date": "2025-07-13",
      "open": 218.00,
      "high": 221.50,
      "low": 216.30,
      "close": 220.50,
      "volume": 52341000
    }
  ],
  "current_price": 220.50,
  "market_cap": 3400000000000,
  "pe_ratio": 28.5
}
```

---

## 🤖 Recommendations API

### Get Pending Recommendations
List all pending trade recommendations.

```http
GET /api/recommendations
```

**Response (200):**
```json
{
  "recommendations": [
    {
      "id": 1,
      "symbol": "AAPL",
      "recommendation_type": "BUY",
      "confidence_score": 0.78,
      "target_price": 225.00,
      "reasoning": "Strong positive sentiment with earnings beat expectations",
      "status": "PENDING",
      "created_at": "2025-07-19T10:30:00.000000"
    }
  ],
  "total_pending": 1
}
```

### Generate Recommendations
Create new trade recommendations based on current market conditions.

```http
POST /api/generate-recommendations
```

**Request Body (Optional):**
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL"]
}
```

**Response (200):**
```json
{
  "recommendations": [
    {
      "symbol": "AAPL",
      "recommendation_type": "BUY",
      "confidence_score": 0.78,
      "reasoning": "Positive sentiment score of 0.125 with strong news coverage"
    },
    {
      "symbol": "MSFT",
      "recommendation_type": "HOLD",
      "confidence_score": 0.45,
      "reasoning": "Neutral sentiment with mixed market signals"
    }
  ],
  "total_generated": 2,
  "message": "Generated 2 trade recommendations"
}
```

### Approve Recommendation
Approve and execute a trade recommendation.

```http
POST /api/recommendations/{recommendation_id}/approve
```

**Response (200):**
```json
{
  "recommendation_id": 1,
  "trade_id": 16,
  "message": "Recommendation approved and trade executed",
  "trade_details": {
    "symbol": "AAPL",
    "quantity": 10,
    "price": 221.25,
    "total_value": 2212.50
  }
}
```

### Reject Recommendation
Reject a trade recommendation with optional reason.

```http
POST /api/recommendations/{recommendation_id}/reject
```

**Request Body (Optional):**
```json
{
  "reason": "Market conditions changed, prefer to wait"
}
```

**Response (200):**
```json
{
  "recommendation_id": 1,
  "status": "REJECTED",
  "message": "Recommendation rejected successfully"
}
```

---

## 🎯 Strategy API

### Run Trading Strategy
Execute the automated sentiment-based trading strategy.

```http
POST /api/run-strategy
```

**Response (200):**
```json
{
  "strategy_name": "Sentiment-Based Trading",
  "trades_executed": 3,
  "trades": [
    {
      "symbol": "AAPL",
      "action": "BUY",
      "quantity": 10,
      "price": 221.25,
      "reasoning": "Strong positive sentiment"
    }
  ],
  "total_capital_used": 6635.75,
  "message": "Strategy executed successfully"
}
```

**Error Response (400):**
```json
{
  "detail": "Strategy execution failed: Insufficient balance for recommended trades"
}
```

---

## 🔍 Market Discovery API

### Market Scan
Scan market news for trending stocks.

```http
POST /api/market-scan
```

**Query Parameters:**
- `limit` (optional): Number of trending stocks to return (default: 10)

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/market-scan?limit=5"
```

**Response (200):**
```json
{
  "discoveries": [
    {
      "symbol": "NVDA",
      "trending_score": 0.85,
      "mention_count": 45,
      "sentiment": 0.12,
      "news_sources": ["Reuters", "Bloomberg", "CNBC"],
      "reason": "AI chip demand surge"
    },
    {
      "symbol": "AMD",
      "trending_score": 0.72,
      "mention_count": 28,
      "sentiment": 0.08,
      "news_sources": ["MarketWatch", "Yahoo Finance"],
      "reason": "Quarterly earnings beat"
    }
  ],
  "total_found": 5,
  "message": "Found 5 trending stocks"
}
```

### Auto Discovery
Automatically discover and analyze trending stocks.

```http
POST /api/auto-discover
```

**Query Parameters:**
- `min_trending_score` (optional): Minimum score threshold (default: 0.5)

**Response (200):**
```json
{
  "discovered_stocks": ["NVDA", "AMD", "INTC"],
  "added_stocks": ["NVDA", "AMD"],
  "skipped_stocks": ["INTC"],
  "sentiment_analysis": {
    "completed": 2,
    "failed": 0
  },
  "summary": "Discovered 3 stocks, added 2 new stocks to tracking"
}
```

### Discovery to Recommendations Pipeline
Complete pipeline: discover → analyze → recommend.

```http
POST /api/discovery-to-recommendations
```

**Query Parameters:**
- `min_trending_score` (optional): Minimum trending score (default: 0.5)

**Response (200):**
```json
{
  "discovery": {
    "discovered_stocks": ["NVDA", "AMD"],
    "added_stocks": ["NVDA", "AMD"]
  },
  "recommendations": {
    "generated": 1,
    "recommendations": [
      {
        "symbol": "NVDA",
        "recommendation_type": "BUY",
        "confidence_score": 0.78
      }
    ]
  },
  "summary": "Discovered 2 stocks, generated 1 recommendation"
}
```

---

## 🔧 Utility Endpoints

### Health Check
Check API health status.

```http
GET /
```

**Response (200):**
```json
{
  "message": "Trading Sentiment Analysis API",
  "status": "healthy",
  "timestamp": "2025-07-19T15:30:00.000000"
}
```

### API Status
Get detailed API status information.

```http
GET /api/status
```

**Response (200):**
```json
{
  "api_version": "1.0.0",
  "database_status": "connected",
  "external_apis": {
    "yahoo_finance": "operational",
    "news_api": "operational"
  },
  "scheduler_status": "running",
  "uptime": "2 days, 14 hours"
}
```

---

## 🔌 WebSocket Events

### Portfolio Updates (Planned)
Real-time portfolio value updates via WebSocket.

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/portfolio');

// Receive updates
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Portfolio Update:', data);
};

// Example update
{
  "type": "portfolio_update",
  "current_balance": 100245.75,
  "total_return": 0.25,
  "timestamp": "2025-07-19T15:30:00.000000"
}
```

### Trade Notifications (Planned)
Real-time notifications for trade executions.

```javascript
{
  "type": "trade_executed",
  "trade": {
    "id": 16,
    "symbol": "AAPL",
    "trade_type": "BUY",
    "quantity": 10,
    "price": 221.25
  }
}
```

---

## 📚 SDK Examples

### Python SDK Example
```python
import requests
import json

class TradingAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def create_trade(self, symbol, trade_type, quantity, strategy="MANUAL"):
        response = self.session.post(
            f"{self.base_url}/api/trades",
            json={
                "symbol": symbol,
                "trade_type": trade_type,
                "quantity": quantity,
                "strategy": strategy
            }
        )
        return response.json()
    
    def get_portfolio_performance(self):
        response = self.session.get(f"{self.base_url}/api/performance")
        return response.json()
    
    def analyze_sentiment(self, symbol):
        response = self.session.post(
            f"{self.base_url}/api/analyze-sentiment",
            json={"symbol": symbol}
        )
        return response.json()

# Usage
api = TradingAPI()
trade = api.create_trade("AAPL", "BUY", 10)
performance = api.get_portfolio_performance()
sentiment = api.analyze_sentiment("AAPL")
```

### JavaScript SDK Example
```javascript
class TradingAPI {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async createTrade(symbol, tradeType, quantity, strategy = 'MANUAL') {
    const response = await fetch(`${this.baseUrl}/api/trades`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        symbol,
        trade_type: tradeType,
        quantity,
        strategy,
      }),
    });
    return response.json();
  }

  async getPortfolioHistory(days = 30) {
    const response = await fetch(
      `${this.baseUrl}/api/portfolio-history?days=${days}`
    );
    return response.json();
  }

  async runStrategy() {
    const response = await fetch(`${this.baseUrl}/api/run-strategy`, {
      method: 'POST',
    });
    return response.json();
  }
}

// Usage
const api = new TradingAPI();
const trade = await api.createTrade('MSFT', 'BUY', 5);
const history = await api.getPortfolioHistory(7);
```

### cURL Examples
```bash
# Create a trade
curl -X POST "http://localhost:8000/api/trades" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "trade_type": "BUY", "quantity": 10}'

# Get portfolio performance  
curl -X GET "http://localhost:8000/api/performance"

# Run bulk sentiment analysis
curl -X POST "http://localhost:8000/api/analyze-bulk-sentiment" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT", "GOOGL"]}'

# Market scan
curl -X POST "http://localhost:8000/api/market-scan?limit=5"
```

---

## 🔍 Testing & Validation

### API Testing with Postman
Import the OpenAPI schema from `http://localhost:8000/openapi.json` into Postman for complete API testing.

### Validation Rules
- Stock symbols: 1-10 alphabetic characters
- Quantities: Positive integers
- Prices: Positive numbers with up to 2 decimal places
- Dates: ISO 8601 format

### Performance Testing
```bash
# Load testing with curl
for i in {1..100}; do
  curl -X GET "http://localhost:8000/api/trades" > /dev/null 2>&1 &
done
wait
```

---

For questions about the API or to report issues, please refer to the main project documentation or open an issue on GitHub.