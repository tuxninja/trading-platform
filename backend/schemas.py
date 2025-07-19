from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List

class TradeBase(BaseModel):
    symbol: str
    trade_type: str
    quantity: int
    price: float
    strategy: str = "MANUAL"

class TradeCreate(TradeBase):
    pass

class TradeResponse(TradeBase):
    id: int
    total_value: float
    timestamp: datetime
    status: str
    sentiment_score: Optional[float] = None
    profit_loss: Optional[float] = None
    close_timestamp: Optional[datetime] = None
    close_price: Optional[float] = None

    class Config:
        from_attributes = True

class SentimentBase(BaseModel):
    symbol: str
    news_sentiment: float
    social_sentiment: float
    overall_sentiment: float
    news_count: int
    social_count: int
    source: str

class SentimentResponse(SentimentBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class StockDataBase(BaseModel):
    symbol: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None

class StockDataResponse(StockDataBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class PerformanceMetricsResponse(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_profit_loss: float
    win_rate: float
    average_profit: float
    average_loss: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None

    class Config:
        from_attributes = True

class StrategySignal(BaseModel):
    symbol: str
    action: str  # "BUY", "SELL", "HOLD"
    confidence: float
    sentiment_score: float
    price: float
    reasoning: str

class TradeRecommendation(BaseModel):
    symbol: str
    action: str  # "BUY", "SELL", "HOLD"
    confidence: float
    sentiment_score: float
    current_price: float
    recommended_quantity: int
    recommended_value: float
    reasoning: str
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    news_summary: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    
class TradeRecommendationResponse(TradeRecommendation):
    id: int
    status: str  # "PENDING", "APPROVED", "REJECTED", "EXPIRED"
    
    class Config:
        from_attributes = True

class MarketScanResult(BaseModel):
    symbol: str
    company_name: str
    current_price: float
    sentiment_score: float
    news_count: int
    trending_score: float
    reason_found: str
    discovered_at: datetime

class SentimentAnalysisRequest(BaseModel):
    symbols: List[str]
    force_refresh: bool = True

class BulkSentimentResponse(BaseModel):
    results: List[SentimentResponse]
    errors: List[str]
    total_processed: int
    successful: int
    failed: int

class GoogleLoginRequest(BaseModel):
    token: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict 