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

# Position Management Schemas

class StrategyBase(BaseModel):
    name: str
    strategy_type: str
    description: str = ""
    parameters: dict = {}
    allocation_percentage: float = 10.0
    max_positions: int = 5
    risk_level: str = "MEDIUM"

class StrategyCreate(StrategyBase):
    pass

class StrategyResponse(StrategyBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PositionBase(BaseModel):
    symbol: str
    entry_price: float
    quantity: int
    position_size: float

class PositionResponse(PositionBase):
    id: int
    strategy_id: int
    status: str
    entry_timestamp: datetime
    exit_timestamp: Optional[datetime] = None
    exit_price: Optional[float] = None
    realized_pnl: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    max_hold_time: Optional[int] = None
    trailing_stop_percentage: Optional[float] = None
    sentiment_at_entry: Optional[float] = None
    
    class Config:
        from_attributes = True

class PositionExitEventResponse(BaseModel):
    id: int
    position_id: int
    exit_type: str
    trigger_price: float
    quantity_closed: int
    exit_price: float
    realized_pnl: float
    timestamp: datetime
    reason: str
    
    class Config:
        from_attributes = True

class StrategyPerformanceResponse(BaseModel):
    id: int
    strategy_id: int
    date: datetime
    total_positions: int
    open_positions: int
    closed_positions: int
    winning_positions: int
    losing_positions: int
    total_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    win_rate: float
    average_win: float
    average_loss: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    allocated_capital: float
    utilized_capital: float
    available_capital: float
    
    class Config:
        from_attributes = True

class PositionSummaryResponse(BaseModel):
    total_positions: int
    open_positions: int
    closed_positions: int
    total_invested: float
    total_unrealized_pnl: float
    total_realized_pnl: float
    positions: List[dict]

class ExitConditionRequest(BaseModel):
    position_id: int
    exit_type: str
    reason: str = ""
    partial_quantity: Optional[int] = None

class StrategyRunRequest(BaseModel):
    strategy_id: int
    symbols: Optional[List[str]] = None
    force_analysis: bool = False 

# NEW SCHEMAS FOR REAL TRADING CONTROL AND TRANSPARENCY

from enum import Enum
from typing import Dict, Any

class TradingModeEnum(str, Enum):
    MANUAL = "MANUAL"
    SEMI_AUTO = "SEMI_AUTO"  # Preview trades, manual approval
    AUTO = "AUTO"  # Fully automated

class CapitalAllocationSettings(BaseModel):
    max_total_investment: float  # Maximum total capital to invest
    max_position_size_percent: float = 5.0  # Max % of portfolio per position
    max_positions: int = 10  # Maximum number of open positions
    reserve_cash_percent: float = 10.0  # % of capital to keep as cash reserve

class ExitStrategySettings(BaseModel):
    stop_loss_percent: Optional[float] = None  # Stop loss as % below purchase price
    take_profit_percent: Optional[float] = None  # Take profit as % above purchase price
    max_hold_days: Optional[int] = None  # Maximum days to hold position
    trailing_stop_percent: Optional[float] = None  # Trailing stop loss %

class TradingControlSettings(BaseModel):
    trading_mode: TradingModeEnum = TradingModeEnum.SEMI_AUTO
    capital_allocation: CapitalAllocationSettings
    exit_strategy: ExitStrategySettings
    require_confirmation: bool = True  # Require manual confirmation before trades
    enable_notifications: bool = True  # Send notifications for trade events

class TradeSignalPreview(BaseModel):
    signal_id: str  # Unique identifier for this signal
    symbol: str
    action: str  # BUY, SELL
    quantity: int
    estimated_price: float
    estimated_total: float
    reasoning: str
    confidence: float
    sentiment_score: float
    risk_assessment: Dict[str, Any]
    capital_impact: Dict[str, float]  # Shows available capital before/after
    created_at: datetime
    expires_at: datetime  # Signals expire after some time

class TradeApprovalRequest(BaseModel):
    signal_id: str  # Signal ID to approve or reject
    approved: bool  # Whether to approve the trade
    override_quantity: Optional[int] = None  # Override suggested quantity
    override_price_limit: Optional[float] = None  # Set maximum price for BUY or minimum for SELL
    notes: Optional[str] = None  # Optional notes about the decision

class CapitalAllocationStatus(BaseModel):
    total_portfolio_value: float
    cash_available: float
    cash_allocated_to_trades: float
    cash_reserve_required: float
    cash_available_for_new_trades: float
    max_total_investment_limit: float
    current_investment_amount: float
    investment_capacity_remaining: float
    open_positions_count: int
    max_positions_limit: int
    position_capacity_remaining: int
    largest_position_percent: float
    sector_allocations: Dict[str, float]

class ExitSignalPreview(BaseModel):
    signal_id: str
    position_id: int
    symbol: str
    action: str = "SELL"
    quantity: int
    estimated_price: float
    estimated_total: float
    estimated_pnl: float
    exit_reason: str
    urgency: str  # LOW, MEDIUM, HIGH
    created_at: datetime
    expires_at: Optional[datetime] = None  # Some exits (stop loss) don't expire

class TradingNotification(BaseModel):
    id: str
    type: str  # SIGNAL_GENERATED, TRADE_EXECUTED, EXIT_TRIGGERED, RISK_WARNING
    title: str
    message: str
    symbol: Optional[str] = None
    priority: str  # LOW, MEDIUM, HIGH, URGENT
    action_required: bool = False
    action_url: Optional[str] = None
    created_at: datetime
    read: bool = False

class RiskAssessmentResponse(BaseModel):
    overall_risk_score: float  # 0-10 scale
    warnings: List[str]
    recommendations: List[str]
    portfolio_metrics: Dict[str, float]
    position_concentration: Dict[str, float]
    sector_concentration: Dict[str, float]
    volatility_analysis: Dict[str, Any]