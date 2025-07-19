from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

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