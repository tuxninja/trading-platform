# TradingService Documentation

The TradingService is the core service responsible for all paper trading operations, portfolio management, and performance calculations.

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Class Structure](#class-structure)
- [Core Methods](#core-methods)
- [Portfolio Management](#portfolio-management)
- [Performance Calculations](#performance-calculations)
- [Strategy Execution](#strategy-execution)
- [Error Handling](#error-handling)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Testing](#testing)

## 🎯 Overview

The TradingService handles all trading-related operations in the paper trading system. It maintains portfolio state, executes trades, calculates profit/loss, and provides comprehensive performance analytics.

**File Location**: `backend/services/trading_service.py`

### Key Responsibilities
- Execute paper trades (BUY/SELL)
- Manage portfolio balance and positions
- Calculate profit/loss for trades
- Generate performance metrics
- Execute automated trading strategies
- Validate trade requests and balance constraints

## ✨ Key Features

### Trading Operations
- ✅ **Paper Trade Execution** - Simulated trading with real market prices
- ✅ **Balance Management** - Real-time portfolio balance tracking
- ✅ **Position Tracking** - Open position management and P&L calculation
- ✅ **Trade Validation** - Balance and quantity validation before execution

### Portfolio Analytics
- ✅ **Performance Metrics** - Comprehensive portfolio statistics
- ✅ **Historical Tracking** - Portfolio value history for charting
- ✅ **Risk Metrics** - Max drawdown, Sharpe ratio calculations
- ✅ **Win/Loss Analysis** - Trade success rate tracking

### Strategy Integration
- ✅ **Sentiment-Based Trading** - Automated trades based on sentiment analysis
- ✅ **Recommendation Execution** - Execute approved trade recommendations
- ✅ **Risk Management** - Position sizing and balance protection

## 🏗️ Class Structure

```python
class TradingService:
    def __init__(self):
        # Dependencies
        self.sentiment_service = SentimentService()
        self.data_service = DataService()
        
        # Configuration
        self.initial_balance = config.INITIAL_BALANCE
        self.current_balance = self.initial_balance
        self.positions = {}  # Current open positions
        
        # Logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize balance from existing trades (startup fix)
        self._initialize_balance()
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `sentiment_service` | SentimentService | Sentiment analysis service dependency |
| `data_service` | DataService | Market data service dependency |
| `initial_balance` | float | Starting portfolio balance |
| `current_balance` | float | Current available cash balance |
| `positions` | dict | Currently open positions (symbol -> quantity) |
| `logger` | Logger | Service-specific logger instance |

## 🔧 Core Methods

### Trade Execution

#### `create_trade(db: Session, trade: TradeCreate) -> TradeResponse`

Execute a new paper trade with comprehensive validation.

**Parameters:**
- `db`: Database session
- `trade`: Trade creation data (symbol, type, quantity, strategy)

**Returns:** TradeResponse with trade details and execution results

**Validation:**
- Quantity must be positive
- Symbol must be valid (1-10 alphabetic characters)
- Sufficient balance for BUY trades
- Sufficient shares for SELL trades

**Example:**
```python
trade_data = TradeCreate(
    symbol="AAPL",
    trade_type="BUY",
    quantity=10,
    strategy="SENTIMENT"
)

result = trading_service.create_trade(db, trade_data)
print(f"Trade executed: {result.symbol} {result.trade_type} {result.quantity}@{result.price}")
```

**Process Flow:**
1. Validate input parameters
2. Get current market price
3. Calculate total trade value
4. Check balance/position constraints
5. Create database record
6. Update portfolio balance
7. Log trade execution

#### `close_trade(db: Session, trade_id: int, close_price: float = None) -> TradeResponse`

Close an open position and calculate profit/loss.

**Parameters:**
- `db`: Database session
- `trade_id`: ID of the trade to close
- `close_price`: Optional closing price (uses current market price if not provided)

**Returns:** TradeResponse with updated trade including P&L

**Process:**
1. Retrieve open trade from database
2. Get closing price (parameter or current market price)
3. Calculate profit/loss based on trade type
4. Update trade status to "CLOSED"
5. Return capital + profit to available balance
6. Log trade closure

**Profit/Loss Calculation:**
```python
# For BUY trades
profit_loss = (close_price - entry_price) * quantity

# For SELL trades (short selling)  
profit_loss = (entry_price - close_price) * quantity
```

#### `delete_trade(db: Session, trade_id: int) -> Dict`

Delete an open trade and reverse its effects on the portfolio.

**Restrictions:**
- Only open trades can be deleted
- Closed trades cannot be deleted (data integrity)

**Process:**
1. Validate trade exists and is open
2. Reverse balance effects
3. Update position tracking
4. Remove trade from database

### Portfolio Management

#### `recalculate_current_balance(db: Session)`

Recalculate portfolio balance based on all historical trades. This method ensures balance accuracy, especially after service restarts.

**Process:**
1. Start with initial balance
2. Subtract capital tied up in open BUY positions
3. Add proceeds from open SELL positions  
4. Add profits/losses from closed trades
5. Update current_balance attribute

**Balance Formula:**
```
current_balance = initial_balance 
                - sum(open_buy_positions.total_value)
                + sum(open_sell_positions.total_value)
                + sum(closed_trades.profit_loss)
```

#### `get_performance_metrics(db: Session) -> Dict`

Generate comprehensive portfolio performance statistics.

**Returns:**
```python
{
    "total_trades": int,           # Number of closed trades
    "winning_trades": int,         # Number of profitable trades  
    "losing_trades": int,          # Number of losing trades
    "total_profit_loss": float,    # Sum of all P&L
    "win_rate": float,            # Percentage of winning trades
    "average_profit": float,       # Average profit per winning trade
    "average_loss": float,        # Average loss per losing trade
    "max_drawdown": float,        # Maximum portfolio decline (%)
    "sharpe_ratio": float,        # Risk-adjusted return measure
    "current_balance": float,     # Current available balance
    "total_return": float         # Overall return based on realized P&L (%)
}
```

**Key Calculations:**
- **Win Rate**: `winning_trades / total_trades * 100`
- **Total Return**: `total_profit_loss / initial_balance * 100`
- **Max Drawdown**: Maximum decline from portfolio peak
- **Sharpe Ratio**: Average return divided by return volatility

#### `get_portfolio_history(db: Session, days: int = 30) -> List[Dict]`

Generate historical portfolio values for chart visualization.

**Returns:**
```python
[
    {"date": "2025-07-12", "value": 100000.00},
    {"date": "2025-07-04", "value": 96796.75},
    {"date": "2025-07-04", "value": 100104.25},  # After trade close
    {"date": "2025-07-19", "value": 85976.56}
]
```

**Process:**
1. Get all trades in chronological order
2. Calculate portfolio value at each trade timestamp
3. Account for capital allocation and profit/loss
4. Return date-value pairs for charting

### Strategy Execution

#### `run_sentiment_strategy(db: Session) -> Dict`

Execute the automated sentiment-based trading strategy.

**Strategy Logic:**
1. Get sentiment data for all tracked stocks
2. Filter stocks with strong sentiment signals (> threshold)
3. Calculate position sizes based on confidence and risk limits
4. Execute trades for qualifying stocks
5. Return execution summary

**Example Return:**
```python
{
    "strategy_name": "Sentiment-Based Trading",
    "trades_executed": 3,
    "trades": [
        {
            "symbol": "AAPL", 
            "action": "BUY",
            "quantity": 10,
            "price": 221.25,
            "reasoning": "Strong positive sentiment (0.78)"
        }
    ],
    "total_capital_used": 6635.75,
    "message": "Strategy executed successfully"
}
```

**Risk Management:**
- Maximum position size per stock (configurable %)
- Total capital allocation limits
- Sentiment confidence thresholds
- Balance protection (minimum cash reserve)

## 📊 Performance Calculations

### Win Rate Calculation
```python
def calculate_win_rate(closed_trades: List[Trade]) -> float:
    if not closed_trades:
        return 0.0
    
    winning_trades = len([t for t in closed_trades if t.profit_loss > 0])
    return (winning_trades / len(closed_trades)) * 100
```

### Maximum Drawdown
```python
def calculate_max_drawdown(trade_history: List[Trade]) -> float:
    """Calculate maximum portfolio decline from peak"""
    cumulative_returns = []
    running_balance = self.initial_balance
    
    for trade in sorted(trade_history, key=lambda x: x.timestamp):
        running_balance += trade.profit_loss or 0
        return_pct = (running_balance - self.initial_balance) / self.initial_balance
        cumulative_returns.append(return_pct)
    
    max_drawdown = 0
    peak = 0
    for ret in cumulative_returns:
        if ret > peak:
            peak = ret
        drawdown = peak - ret
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    return max_drawdown * 100  # Return as percentage
```

### Sharpe Ratio
```python
def calculate_sharpe_ratio(returns: List[float]) -> float:
    """Risk-adjusted return measure"""
    if len(returns) < 2:
        return 0.0
    
    avg_return = sum(returns) / len(returns)
    variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
    std_dev = variance ** 0.5
    
    return avg_return / std_dev if std_dev > 0 else 0.0
```

### Total Return Calculation
```python
# Updated to use realized profits only (not current_balance)
total_return = (total_profit_loss / initial_balance) * 100
```

**Why This Approach:**
- Uses realized profits/losses from closed trades only
- Doesn't penalize for capital tied up in open positions
- Accurately reflects trading performance vs. cash availability

## 🎯 Strategy Execution Details

### Sentiment-Based Strategy

**Entry Conditions:**
- Sentiment score above threshold (configurable)
- High confidence score (> 0.6)
- Sufficient portfolio balance
- Position size within risk limits

**Position Sizing:**
```python
def calculate_position_size(sentiment_score: float, confidence: float, 
                          stock_price: float) -> int:
    # Base position value
    max_position_value = self.current_balance * config.MAX_POSITION_SIZE
    
    # Adjust based on confidence
    adjusted_value = max_position_value * confidence
    
    # Convert to share quantity
    quantity = int(adjusted_value / stock_price)
    
    return max(1, quantity)  # Minimum 1 share
```

### Risk Management

**Portfolio Protection:**
- Maximum 5% position size per stock (configurable)
- Minimum 10% cash reserve maintained
- Maximum 10 trades per day limit
- Stop-loss at -20% per position (planned feature)

**Balance Constraints:**
```python
def validate_trade_balance(self, total_value: float) -> bool:
    """Ensure sufficient balance for trade"""
    if total_value > self.current_balance:
        raise InsufficientBalanceError(
            f"Insufficient balance: ${self.current_balance:.2f} available, "
            f"${total_value:.2f} required"
        )
    return True
```

## ❌ Error Handling

### Custom Exceptions
```python
class InsufficientBalanceError(TradingAppException):
    """Raised when account balance is insufficient for trade"""
    pass

class InsufficientSharesError(TradingAppException):
    """Raised when trying to sell more shares than owned"""
    pass

class InvalidTradeError(TradingAppException):
    """Raised for invalid trade parameters"""
    pass

class TradeNotFoundError(TradingAppException):
    """Raised when trade ID doesn't exist"""
    pass
```

### Error Handling Patterns
```python
def create_trade(self, db: Session, trade: TradeCreate) -> TradeResponse:
    try:
        # Trade execution logic
        return self.execute_trade(db, trade)
    except (InvalidTradeError, InsufficientBalanceError) as e:
        db.rollback()
        self.logger.warning(f"Trade validation failed: {str(e)}")
        raise  # Re-raise for API to handle
    except Exception as e:
        db.rollback()
        self.logger.error(f"Unexpected error creating trade: {str(e)}")
        raise InvalidTradeError(f"Failed to create trade: {str(e)}")
```

### Logging Strategy
```python
# Trade execution logging
self.logger.info(f"Creating trade: {trade.symbol} {trade.trade_type} {trade.quantity}")
self.logger.info(f"Trade created successfully: ID {result.id}")

# Balance updates
self.logger.info(f"Updated balance after {trade.trade_type}: ${self.current_balance:.2f}")

# Error logging
self.logger.error(f"Trade execution failed: {str(e)}")
self.logger.warning(f"Low balance warning: ${self.current_balance:.2f}")
```

## ⚙️ Configuration

### Environment Variables
```bash
# Trading configuration
INITIAL_BALANCE=100000.0           # Starting portfolio balance
MAX_POSITION_SIZE=0.05             # 5% maximum position size
SENTIMENT_THRESHOLD=0.1            # Minimum sentiment for trades
MAX_TRADES_PER_DAY=10             # Daily trade limit
MIN_RECOMMENDATION_CONFIDENCE=0.6  # Minimum confidence for execution

# Strategy settings
ENABLE_AUTO_TRADING=false          # Enable automated strategy execution
STRATEGY_EXECUTION_TIME=10:30      # Daily strategy run time
```

### Runtime Configuration
```python
class TradingConfig:
    INITIAL_BALANCE: float = 100000.0
    MAX_POSITION_SIZE: float = 0.05
    SENTIMENT_THRESHOLD: float = 0.1
    MIN_CASH_RESERVE: float = 0.1      # Keep 10% cash reserve
    MAX_TRADES_PER_DAY: int = 10
    POSITION_TIMEOUT_DAYS: int = 30     # Auto-close positions after 30 days
```

## 🔧 Usage Examples

### Basic Trade Execution
```python
from services.trading_service import TradingService
from schemas import TradeCreate

# Initialize service
trading_service = TradingService()

# Create a buy trade
trade_data = TradeCreate(
    symbol="AAPL",
    trade_type="BUY",
    quantity=10,
    strategy="MANUAL"
)

# Execute trade
with SessionLocal() as db:
    result = trading_service.create_trade(db, trade_data)
    print(f"Trade executed: {result.id}")
    
    # Get current portfolio performance
    performance = trading_service.get_performance_metrics(db)
    print(f"Current balance: ${performance['current_balance']:,.2f}")
    print(f"Total return: {performance['total_return']:.2f}%")
```

### Close Trade with Profit
```python
# Close the trade after price appreciation
with SessionLocal() as db:
    closed_trade = trading_service.close_trade(db, trade_id=result.id, close_price=225.00)
    print(f"Trade closed with P&L: ${closed_trade.profit_loss:.2f}")
    
    # Check updated performance
    performance = trading_service.get_performance_metrics(db)
    print(f"New balance: ${performance['current_balance']:,.2f}")
```

### Run Automated Strategy
```python
# Execute sentiment-based strategy
with SessionLocal() as db:
    strategy_result = trading_service.run_sentiment_strategy(db)
    
    print(f"Strategy executed {strategy_result['trades_executed']} trades")
    print(f"Total capital used: ${strategy_result['total_capital_used']:,.2f}")
    
    for trade in strategy_result['trades']:
        print(f"  {trade['action']} {trade['quantity']} {trade['symbol']} @ ${trade['price']}")
```

### Portfolio Analytics
```python
# Get comprehensive portfolio analytics
with SessionLocal() as db:
    performance = trading_service.get_performance_metrics(db)
    
    print("=== Portfolio Performance ===")
    print(f"Total Trades: {performance['total_trades']}")
    print(f"Win Rate: {performance['win_rate']:.1f}%")
    print(f"Total P&L: ${performance['total_profit_loss']:,.2f}")
    print(f"Total Return: {performance['total_return']:.2f}%")
    print(f"Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {performance['max_drawdown']:.1f}%")
    
    # Get portfolio history for charting
    history = trading_service.get_portfolio_history(db, days=30)
    print(f"Portfolio history: {len(history)} data points")
```

## 🧪 Testing

### Unit Test Example
```python
import pytest
from unittest.mock import Mock, patch
from services.trading_service import TradingService
from schemas import TradeCreate
from exceptions import InsufficientBalanceError

class TestTradingService:
    def setup_method(self):
        self.service = TradingService()
        self.mock_db = Mock()
    
    def test_create_buy_trade_success(self):
        """Test successful BUY trade creation"""
        # Arrange
        trade_data = TradeCreate(symbol="AAPL", trade_type="BUY", quantity=10)
        
        with patch.object(self.service.data_service, 'get_current_price', return_value=150.0):
            # Act
            result = self.service.create_trade(self.mock_db, trade_data)
            
            # Assert
            assert result.symbol == "AAPL"
            assert result.trade_type == "BUY"
            assert result.quantity == 10
            assert result.total_value == 1500.0
            assert result.status == "OPEN"
    
    def test_insufficient_balance_error(self):
        """Test insufficient balance handling"""
        # Arrange
        self.service.current_balance = 100.0  # Low balance
        trade_data = TradeCreate(symbol="AAPL", trade_type="BUY", quantity=100)
        
        with patch.object(self.service.data_service, 'get_current_price', return_value=150.0):
            # Act & Assert
            with pytest.raises(InsufficientBalanceError):
                self.service.create_trade(self.mock_db, trade_data)
    
    def test_close_trade_profit(self):
        """Test closing trade with profit"""
        # Arrange
        mock_trade = Mock()
        mock_trade.id = 1
        mock_trade.symbol = "AAPL"
        mock_trade.trade_type = "BUY"
        mock_trade.quantity = 10
        mock_trade.price = 150.0
        mock_trade.total_value = 1500.0
        mock_trade.status = "OPEN"
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_trade
        
        # Act
        result = self.service.close_trade(self.mock_db, trade_id=1, close_price=160.0)
        
        # Assert
        assert mock_trade.status == "CLOSED"
        assert mock_trade.close_price == 160.0
        assert mock_trade.profit_loss == 100.0  # (160 - 150) * 10
        
    def test_performance_metrics_empty_portfolio(self):
        """Test performance metrics with no trades"""
        # Arrange
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Act
        metrics = self.service.get_performance_metrics(self.mock_db)
        
        # Assert
        assert metrics['total_trades'] == 0
        assert metrics['win_rate'] == 0.0
        assert metrics['total_profit_loss'] == 0.0
        assert metrics['current_balance'] == self.service.initial_balance
```

### Integration Test Example
```python
def test_full_trade_cycle():
    """Integration test for complete trade lifecycle"""
    from database import SessionLocal
    
    service = TradingService()
    
    with SessionLocal() as db:
        # Create trade
        trade_data = TradeCreate(symbol="TEST", trade_type="BUY", quantity=5)
        trade = service.create_trade(db, trade_data)
        
        # Verify trade created
        assert trade.status == "OPEN"
        initial_balance = service.current_balance
        
        # Close trade with profit
        closed_trade = service.close_trade(db, trade.id, close_price=trade.price + 10)
        
        # Verify profit realized
        assert closed_trade.profit_loss == 50.0  # 5 shares * $10 profit
        assert service.current_balance > initial_balance
        
        # Verify performance metrics
        performance = service.get_performance_metrics(db)
        assert performance['total_trades'] == 1
        assert performance['winning_trades'] == 1
        assert performance['total_return'] > 0
```

### Load Testing
```python
def test_concurrent_trades():
    """Test service performance under load"""
    import threading
    import time
    
    service = TradingService()
    results = []
    
    def create_test_trade(thread_id):
        with SessionLocal() as db:
            trade_data = TradeCreate(
                symbol=f"TEST{thread_id}", 
                trade_type="BUY", 
                quantity=1
            )
            result = service.create_trade(db, trade_data)
            results.append(result)
    
    # Create 10 concurrent trades
    threads = []
    for i in range(10):
        t = threading.Thread(target=create_test_trade, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    # Verify all trades succeeded
    assert len(results) == 10
    assert all(r.status == "OPEN" for r in results)
```

---

## 📚 Additional Resources

- [Database Schema Documentation](../database.md)
- [API Documentation](../api.md)
- [Configuration Guide](../configuration.md)
- [SentimentService Documentation](sentiment-service.md)
- [DataService Documentation](data-service.md)

For questions about the TradingService or to report issues, please refer to the main project documentation.