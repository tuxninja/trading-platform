# Services Documentation

This directory contains detailed documentation for all backend services in the Trading Platform.

## 📋 Service Overview

The Trading Platform backend is organized into modular services, each responsible for specific business logic:

| Service | Purpose | Key Features |
|---------|---------|--------------|
| [TradingService](trading-service.md) | Paper trading operations | Trade execution, P&L calculation, portfolio management |
| [SentimentService](sentiment-service.md) | News sentiment analysis | Multi-source analysis, sentiment scoring, confidence metrics |
| [DataService](data-service.md) | Market data management | Price collection, stock tracking, data validation |
| [RecommendationService](recommendation-service.md) | AI-powered trade recommendations | Signal generation, confidence scoring, execution tracking |
| [MarketScannerService](market-scanner.md) | Market discovery | Trending stock identification, news scanning, popularity scoring |

## 🏗️ Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                      │
├─────────────────────────────────────────────────────────────────┤
│                         Service Layer                          │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
│ Trading     │ Sentiment   │ Data        │ Recommend   │ Scanner │
│ Service     │ Service     │ Service     │ Service     │ Service │
├─────────────┴─────────────┴─────────────┴─────────────┴─────────┤
│                      Database Layer                             │
│                      (SQLAlchemy)                              │
├─────────────────────────────────────────────────────────────────┤
│                     External APIs                              │
│          Yahoo Finance │ News APIs │ Alternative Sources       │
└─────────────────────────────────────────────────────────────────┘
```

## 📚 Service Documentation

### Core Services

- **[TradingService](trading-service.md)** - Complete trading operations documentation
- **[SentimentService](sentiment-service.md)** - Sentiment analysis implementation details  
- **[DataService](data-service.md)** - Market data collection and management
- **[RecommendationService](recommendation-service.md)** - AI recommendation engine
- **[MarketScannerService](market-scanner.md)** - Market discovery and trending analysis

### Service Patterns

All services follow consistent patterns:

- **Dependency Injection** - Services are injected into endpoints
- **Error Handling** - Comprehensive exception handling with custom exceptions
- **Logging** - Structured logging with service-specific loggers
- **Database Sessions** - Proper session management and transactions
- **Configuration** - Environment-based configuration support

### Inter-Service Communication

```python
# Example: TradingService using SentimentService
class TradingService:
    def __init__(self):
        self.sentiment_service = SentimentService()
        self.data_service = DataService()
    
    def run_sentiment_strategy(self, db: Session):
        # Get sentiment data from SentimentService
        sentiment_data = self.sentiment_service.get_all_sentiment(db)
        
        # Get market data from DataService
        market_data = self.data_service.get_tracked_stocks(db)
        
        # Execute trades based on combined data
        return self.execute_strategy_trades(db, sentiment_data, market_data)
```

## 🔄 Service Lifecycle

### Initialization
Services are initialized at application startup with dependency injection:

```python
# main.py
trading_service = TradingService()
sentiment_service = SentimentService() 
data_service = DataService()
recommendation_service = RecommendationService()
market_scanner = MarketScannerService()
```

### Request Handling
Each API endpoint uses appropriate services:

```python
@app.post("/api/trades")
async def create_trade(trade: TradeCreate, db: Session = Depends(get_db)):
    return trading_service.create_trade(db, trade)

@app.post("/api/analyze-sentiment")
async def analyze_sentiment(symbol: str = Body(..., embed=True), db: Session = Depends(get_db)):
    return sentiment_service.analyze_stock_sentiment(db, symbol)
```

### Background Processing
Services are also used by the scheduler for automated tasks:

```python
# scheduler.py
class DataScheduler:
    def __init__(self):
        self.trading_service = TradingService()
        self.sentiment_service = SentimentService()
        self.data_service = DataService()
```

## 🛠️ Development Guidelines

### Adding New Services

1. **Create Service Class**
   ```python
   class NewService:
       def __init__(self):
           self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
   ```

2. **Add Database Operations**
   ```python
   def get_data(self, db: Session) -> List[Model]:
       try:
           return db.query(Model).all()
       except Exception as e:
           self.logger.error(f"Error getting data: {str(e)}")
           raise
       finally:
           # Cleanup if needed
   ```

3. **Implement Error Handling**
   ```python
   from exceptions import CustomException
   
   def process_data(self, data):
       if not data:
           raise CustomException("Data is required")
   ```

4. **Add Logging**
   ```python
   self.logger.info(f"Processing {len(items)} items")
   self.logger.warning(f"Low confidence score: {score}")
   self.logger.error(f"Processing failed: {error}")
   ```

5. **Write Tests**
   ```python
   def test_new_service():
       service = NewService()
       result = service.process_data(test_data)
       assert result is not None
   ```

6. **Update Documentation**
   - Add service to this README
   - Create detailed service documentation
   - Update API documentation if needed

### Service Best Practices

- **Single Responsibility** - Each service has one clear purpose
- **Dependency Injection** - Services receive dependencies, don't create them
- **Error Boundaries** - Handle errors gracefully without crashing the application
- **Logging** - Log important operations and errors
- **Testing** - Write unit tests for all service methods
- **Documentation** - Document public methods and complex logic

### Testing Services

```python
import pytest
from unittest.mock import Mock, patch
from services.trading_service import TradingService

def test_create_trade():
    # Arrange
    service = TradingService()
    mock_db = Mock()
    trade_data = TradeCreate(symbol="AAPL", trade_type="BUY", quantity=10)
    
    # Act
    result = service.create_trade(mock_db, trade_data)
    
    # Assert
    assert result.symbol == "AAPL"
    assert result.status == "OPEN"
```

## 🔍 Debugging Services

### Logging Configuration
```python
# Enable debug logging for specific service
import logging
logging.getLogger('services.trading_service').setLevel(logging.DEBUG)
```

### Service Health Checks
```python
def check_service_health():
    """Check if all services are operational"""
    services = [
        ('TradingService', trading_service),
        ('SentimentService', sentiment_service),
        ('DataService', data_service)
    ]
    
    health_status = {}
    for name, service in services:
        try:
            # Call a simple method to test service
            service.health_check()  # Implement in each service
            health_status[name] = "healthy"
        except Exception as e:
            health_status[name] = f"unhealthy: {str(e)}"
    
    return health_status
```

## 📊 Service Metrics

### Performance Monitoring
Each service can implement performance tracking:

```python
class ServiceMetrics:
    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.avg_response_time = 0.0
    
    def track_request(self, success: bool, response_time: float):
        self.request_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        # Update rolling average
        self.avg_response_time = (self.avg_response_time + response_time) / 2
```

### Usage Analytics
```python
# Track service usage
@app.middleware("http")
async def track_service_usage(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log service usage
    if "/api/" in request.url.path:
        logger.info(f"API call: {request.method} {request.url.path} - {process_time:.3f}s")
    
    return response
```

For detailed information about each service, see the individual service documentation files linked above.