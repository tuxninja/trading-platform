from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from enum import Enum

class PositionStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARTIALLY_CLOSED = "PARTIALLY_CLOSED"
    EXPIRED = "EXPIRED"

class StrategyType(Enum):
    SENTIMENT = "SENTIMENT"
    MOMENTUM = "MOMENTUM"
    MEAN_REVERSION = "MEAN_REVERSION"
    BREAKOUT = "BREAKOUT"
    HYBRID = "HYBRID"
    CUSTOM = "CUSTOM"

class ExitConditionType(Enum):
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TIME_BASED = "TIME_BASED"
    SENTIMENT_CHANGE = "SENTIMENT_CHANGE"
    TRAILING_STOP = "TRAILING_STOP"

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    trade_type = Column(String)  # "BUY" or "SELL"
    quantity = Column(Integer)
    price = Column(Float)
    total_value = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="OPEN")  # "OPEN", "CLOSED", "CANCELLED"
    strategy = Column(String)  # "MANUAL", "SENTIMENT", "MOMENTUM"
    sentiment_score = Column(Float, nullable=True)
    profit_loss = Column(Float, nullable=True)
    close_timestamp = Column(DateTime(timezone=True), nullable=True)
    close_price = Column(Float, nullable=True)
    # Position ID - nullable for backward compatibility with existing trades
    position_id = Column(Integer, nullable=True)

class SentimentData(Base):
    __tablename__ = "sentiment_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    news_sentiment = Column(Float)
    social_sentiment = Column(Float)
    overall_sentiment = Column(Float)
    news_count = Column(Integer)
    social_count = Column(Integer)
    source = Column(String)  # "NEWS", "SOCIAL", "COMBINED"

class StockData(Base):
    __tablename__ = "stock_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    market_cap = Column(Float, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)

class PerformanceMetrics(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    total_profit_loss = Column(Float)
    win_rate = Column(Float)
    average_profit = Column(Float)
    average_loss = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float, nullable=True)

class TradeRecommendation(Base):
    __tablename__ = "trade_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    action = Column(String)  # "BUY", "SELL", "HOLD"
    confidence = Column(Float)
    sentiment_score = Column(Float)
    current_price = Column(Float)
    recommended_quantity = Column(Integer)
    recommended_value = Column(Float)
    reasoning = Column(Text)
    risk_level = Column(String)
    news_summary = Column(Text)
    status = Column(String, default="PENDING")  # "PENDING", "APPROVED", "REJECTED", "EXPIRED"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True)  # If approved and executed

class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    strategy_type = Column(String)  # StrategyType enum
    description = Column(Text)
    parameters = Column(JSON)  # Strategy-specific parameters
    is_active = Column(Boolean, default=True)
    allocation_percentage = Column(Float, default=10.0)  # % of total portfolio
    max_positions = Column(Integer, default=5)
    risk_level = Column(String, default="MEDIUM")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    positions = relationship("Position", back_populates="strategy")
    performance_records = relationship("StrategyPerformance", back_populates="strategy")

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    symbol = Column(String, index=True)
    entry_price = Column(Float)
    quantity = Column(Integer)
    position_size = Column(Float)  # Total value
    status = Column(String, default="OPEN")  # PositionStatus enum
    entry_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    exit_timestamp = Column(DateTime(timezone=True), nullable=True)
    exit_price = Column(Float, nullable=True)
    realized_pnl = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=True)
    
    # Exit conditions
    stop_loss_price = Column(Float, nullable=True)
    take_profit_price = Column(Float, nullable=True)
    max_hold_time = Column(Integer, nullable=True)  # Hours
    trailing_stop_percentage = Column(Float, nullable=True)
    
    # Strategy context
    entry_signal = Column(JSON)  # Signal that triggered entry
    sentiment_at_entry = Column(Float, nullable=True)
    market_conditions = Column(JSON, nullable=True)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="positions")
    exit_events = relationship("PositionExitEvent", back_populates="position")

class PositionExitEvent(Base):
    __tablename__ = "position_exit_events"
    
    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"))
    exit_type = Column(String)  # ExitConditionType enum
    trigger_price = Column(Float)
    quantity_closed = Column(Integer)
    exit_price = Column(Float)
    realized_pnl = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    reason = Column(Text)
    
    # Relationships
    position = relationship("Position", back_populates="exit_events")

class StrategyPerformance(Base):
    __tablename__ = "strategy_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Performance metrics
    total_positions = Column(Integer, default=0)
    open_positions = Column(Integer, default=0)
    closed_positions = Column(Integer, default=0)
    winning_positions = Column(Integer, default=0)
    losing_positions = Column(Integer, default=0)
    
    # Financial metrics
    total_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    average_win = Column(Float, default=0.0)
    average_loss = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)
    
    # Portfolio allocation
    allocated_capital = Column(Float, default=0.0)
    utilized_capital = Column(Float, default=0.0)
    available_capital = Column(Float, default=0.0)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="performance_records")

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String)  # "STRATEGY_RUN", "POSITION_CHECK", "MARKET_SCAN"
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True)
    schedule_expression = Column(String)  # Cron-like expression
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True), nullable=True)
    next_run = Column(DateTime(timezone=True), nullable=True)
    run_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

# ADAPTIVE LEARNING MODELS

class TradePattern(Base):
    """Stores patterns and features extracted from successful/unsuccessful trades"""
    __tablename__ = "trade_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_type = Column(String)  # "SUCCESSFUL_ENTRY", "FAILED_ENTRY", "SUCCESSFUL_EXIT", "FAILED_EXIT"
    
    # Market context when pattern occurred
    symbol = Column(String, index=True)
    sector = Column(String)
    market_cap_range = Column(String)  # SMALL, MID, LARGE
    volatility_level = Column(String)  # LOW, MEDIUM, HIGH
    
    # Sentiment features
    sentiment_score = Column(Float)
    sentiment_strength = Column(Float)  # abs(sentiment_score)
    news_count = Column(Integer, default=0)
    social_count = Column(Integer, default=0)
    
    # Technical features
    price_trend = Column(String)  # UP, DOWN, SIDEWAYS
    volume_trend = Column(String)  # HIGH, NORMAL, LOW
    price_change_1d = Column(Float)
    price_change_5d = Column(Float)
    price_change_30d = Column(Float)
    
    # Trade outcome
    profit_loss = Column(Float)
    profit_loss_percent = Column(Float)
    hold_duration_days = Column(Integer)
    
    # Strategy parameters when pattern occurred
    confidence_threshold = Column(Float)
    position_size_percent = Column(Float)
    buy_sentiment_threshold = Column(Float)
    sell_sentiment_threshold = Column(Float)
    
    # Pattern metadata
    pattern_strength = Column(Float, default=1.0)  # How strong this pattern is
    occurrence_count = Column(Integer, default=1)  # How many times we've seen this pattern
    success_rate = Column(Float, default=0.0)  # Success rate of this pattern
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class StrategyLearning(Base):
    """Tracks strategy parameter adjustments and their performance impact"""
    __tablename__ = "strategy_learning"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    
    # Parameter changes
    parameter_name = Column(String)  # e.g., "confidence_threshold", "position_size"
    old_value = Column(Float)
    new_value = Column(Float)
    adjustment_reason = Column(String)  # WHY the adjustment was made
    
    # Performance before/after
    trades_before_count = Column(Integer, default=0)
    win_rate_before = Column(Float, default=0.0)
    avg_profit_before = Column(Float, default=0.0)
    
    trades_after_count = Column(Integer, default=0)
    win_rate_after = Column(Float, default=0.0)
    avg_profit_after = Column(Float, default=0.0)
    
    # Evaluation metrics
    improvement_score = Column(Float, default=0.0)  # Overall improvement rating
    confidence_level = Column(Float, default=0.5)  # How confident we are in this adjustment
    is_successful = Column(Boolean, default=None)  # Was this adjustment beneficial?
    
    # Learning metadata
    evaluation_period_days = Column(Integer, default=30)
    sample_size_trades = Column(Integer, default=0)
    statistical_significance = Column(Float, default=0.0)
    
    adjustment_date = Column(DateTime(timezone=True), server_default=func.now())
    evaluation_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    strategy = relationship("Strategy")

class LearningInsight(Base):
    """Stores high-level insights discovered by the learning system"""
    __tablename__ = "learning_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    insight_type = Column(String)  # "MARKET_CONDITION", "SYMBOL_SPECIFIC", "SECTOR_TREND", "TIMING_PATTERN"
    
    # The insight content
    title = Column(String)
    description = Column(Text)
    
    # Market context
    symbols_affected = Column(JSON)  # List of symbols this applies to
    sectors_affected = Column(JSON)  # List of sectors this applies to
    market_conditions = Column(JSON)  # Market conditions when this applies
    
    # Supporting evidence
    supporting_trades_count = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.0)  # How confident we are in this insight
    impact_magnitude = Column(Float, default=0.0)  # How much impact this has on performance
    
    # Usage tracking
    times_applied = Column(Integer, default=0)
    success_when_applied = Column(Integer, default=0)
    current_effectiveness = Column(Float, default=0.0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_validated = Column(Boolean, default=False)
    
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_validated = Column(DateTime(timezone=True), nullable=True)
    
class PerformanceBaseline(Base):
    """Tracks performance baselines for comparison and learning evaluation"""
    __tablename__ = "performance_baselines"
    
    id = Column(Integer, primary_key=True, index=True)
    baseline_type = Column(String)  # "OVERALL", "SYMBOL_SPECIFIC", "SECTOR_SPECIFIC", "STRATEGY_SPECIFIC"
    
    # Baseline context
    symbol = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True)
    market_condition = Column(String, nullable=True)  # BULL, BEAR, SIDEWAYS
    
    # Performance metrics
    win_rate = Column(Float)
    avg_profit = Column(Float)
    avg_loss = Column(Float)
    profit_factor = Column(Float)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    
    # Data points
    total_trades = Column(Integer)
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))
    
    # Metadata
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    strategy = relationship("Strategy")