from fastapi import FastAPI, HTTPException, Depends, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import uvicorn
from datetime import datetime, timedelta
import os
import sys
import yfinance
import logging
from typing import Dict, Any, List, Optional

from database import get_db, engine, Base
from models import Trade, SentimentData, StockData, TradeRecommendation, Strategy, Position
from schemas import (
    TradeCreate, TradeResponse, SentimentResponse,
    SentimentAnalysisRequest, BulkSentimentResponse,
    TradeRecommendationResponse, MarketScanResult,
    GoogleLoginRequest, AuthResponse,
    StrategyCreate, StrategyResponse, StrategyRunRequest,
    PositionResponse, PositionSummaryResponse, ExitConditionRequest
)
from services.trading_service import TradingService
from services.sentiment_service import SentimentService
from services.data_service import DataService
from services.recommendation_service import RecommendationService
from services.market_scanner import MarketScannerService
from services.strategy_service import StrategyService
from services.position_manager import PositionManager
from services.performance_service import PerformanceService
from config import config, setup_logging
from exceptions import TradingAppException
from auth import auth_service, get_current_user, optional_auth
from admin_api import admin_router

# Setup logging
logger = setup_logging()

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {str(e)}")
    # Continue anyway - tables might already exist

app = FastAPI(
    title="Trading Sentiment Analysis", 
    version="1.0.0",
    description="Sentiment-based paper trading system"
)

# Include admin routes
app.include_router(admin_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    logger.info(f"Request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
        return response
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Request failed: {request.method} {request.url} - {str(e)} - {process_time:.3f}s")
        raise

# Initialize services
trading_service = TradingService()
sentiment_service = SentimentService()
data_service = DataService()
recommendation_service = RecommendationService()
market_scanner = MarketScannerService()
strategy_service = StrategyService()
position_manager = PositionManager()
performance_service = PerformanceService()

logger.info(f"Python executable: {sys.executable}")
logger.info(f"yfinance version: {yfinance.__version__}")
logger.info(f"Backend started at: {datetime.now()}")
logger.info(f"Configuration loaded successfully")

@app.get("/")
async def root():
    return {"message": "Trading Sentiment Analysis API"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint for debugging"""
    return {
        "status": "healthy",
        "google_client_id_configured": bool(auth_service.google_client_id),
        "cors_origins": config.CORS_ORIGINS
    }

@app.get("/api/debug")
async def debug_info():
    """Debug endpoint to verify API connectivity"""
    try:
        # Test database connection
        db = next(get_db())
        db_status = "connected"
        try:
            # Try a simple query
            trade_count = db.query(Trade).count()
            db_query_status = f"ok - {trade_count} trades"
        except Exception as e:
            db_query_status = f"query failed: {str(e)}"
        finally:
            db.close()
    except Exception as e:
        db_status = f"failed: {str(e)}"
        db_query_status = "not tested"
    
    return {
        "status": "API is working",
        "timestamp": datetime.now().isoformat(),
        "backend_container": "trading-backend",
        "google_client_id_configured": bool(auth_service.google_client_id),
        "cors_origins": config.CORS_ORIGINS,
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "database_status": db_status,
        "database_query_status": db_query_status,
        "services_initialized": {
            "trading_service": trading_service is not None,
            "sentiment_service": sentiment_service is not None,
            "data_service": data_service is not None,
            "strategy_service": strategy_service is not None,
            "position_manager": position_manager is not None
        }
    }

@app.get("/api/debug/network")
async def network_debug():
    """Network debugging endpoint with detailed info"""
    return {
        "status": "ok",
        "message": "Backend is reachable",
        "timestamp": datetime.now().isoformat(),
        "cors_origins": config.CORS_ORIGINS,
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "available_endpoints": [
            "/api/health",
            "/api/debug/network", 
            "/api/trades",
            "/api/sentiment",
            "/api/auth/google",
            "/api/auth/me"
        ],
        "database_status": "connected"
    }

# Authentication endpoints
@app.post("/api/auth/google", response_model=AuthResponse)
async def google_login(login_request: GoogleLoginRequest):
    """Authenticate user with Google OAuth token"""
    try:
        logger.info(f"Received Google OAuth login request")
        logger.info(f"Token length: {len(login_request.token) if login_request.token else 'None'}")
        logger.info(f"Google Client ID configured: {bool(auth_service.google_client_id)}")
        
        user_data = auth_service.verify_google_token(login_request.token)
        logger.info(f"Google token verified for user: {user_data.get('email', 'unknown')}")
        
        jwt_token = auth_service.create_jwt_token(user_data)
        logger.info(f"JWT token created successfully")
        
        return AuthResponse(
            access_token=jwt_token,
            token_type="bearer",
            user=user_data
        )
    except HTTPException as e:
        logger.error(f"HTTP Exception in Google auth: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in Google authentication: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return {"user": current_user}

@app.get("/api/trades")
async def get_trades(db: Session = Depends(get_db)):
    """Get all paper trades"""
    try:
        return trading_service.get_all_trades(db)
    except Exception as e:
        logger.error(f"Error getting trades: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/debug/trades")
async def debug_trades(db: Session = Depends(get_db)):
    """Debug trades endpoint without auth"""
    try:
        trades = db.query(Trade).limit(5).all()
        return {
            "total_trades": db.query(Trade).count(),
            "sample_trades": [
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "trade_type": t.trade_type,
                    "quantity": t.quantity,
                    "price": t.price,
                    "timestamp": t.timestamp.isoformat() if t.timestamp else None
                } for t in trades
            ]
        }
    except Exception as e:
        logger.error(f"Error in debug trades: {str(e)}")
        return {"error": str(e), "type": type(e).__name__}

@app.get("/api/debug/portfolio")
async def debug_portfolio(db: Session = Depends(get_db)):
    """Debug portfolio calculations to identify production vs development discrepancies"""
    try:
        # Get basic trade counts and statistics
        all_trades = db.query(Trade).all()
        open_trades = [t for t in all_trades if t.status == "OPEN"]
        closed_trades = [t for t in all_trades if t.status == "CLOSED"]
        
        # Get trading service instance and recalculate balance
        trading_service.recalculate_current_balance(db)
        
        # Get performance metrics from both endpoints
        old_performance = trading_service.get_performance_metrics(db)
        portfolio_summary = trading_service.get_portfolio_summary(db)
        
        # Calculate manual portfolio values
        cash_balance = trading_service.current_balance
        open_positions_value = 0
        for trade in open_trades:
            if trade.trade_type == "BUY":
                # For open BUY positions, use current market price if available
                try:
                    market_data = trading_service.data_service.get_market_data(trade.symbol, days=1)
                    current_price = market_data.get("current_price", trade.price)
                    position_value = trade.quantity * current_price
                    open_positions_value += position_value
                except:
                    # Fallback to original trade value
                    open_positions_value += trade.total_value
        
        total_portfolio_value = cash_balance + open_positions_value
        
        # Debug configuration
        config_info = {
            "initial_balance": config.INITIAL_BALANCE,
            "database_url": os.getenv("DATABASE_URL", "not set"),
            "environment": os.getenv("ENVIRONMENT", "not set")
        }
        
        return {
            "config": config_info,
            "trade_counts": {
                "total_trades": len(all_trades),
                "open_trades": len(open_trades),
                "closed_trades": len(closed_trades)
            },
            "balance_calculations": {
                "trading_service_current_balance": trading_service.current_balance,
                "trading_service_initial_balance": trading_service.initial_balance,
                "calculated_cash_balance": cash_balance,
                "open_positions_value": open_positions_value,
                "total_portfolio_value": total_portfolio_value
            },
            "api_responses": {
                "old_performance_endpoint": {
                    "current_balance": old_performance.get("current_balance"),
                    "total_return": old_performance.get("total_return"),
                    "total_profit_loss": old_performance.get("total_profit_loss"),
                    "win_rate": old_performance.get("win_rate")
                },
                "portfolio_summary": {
                    "portfolio_value": portfolio_summary.get("portfolio_value"),
                    "current_balance": portfolio_summary.get("current_balance"),
                    "total_return": portfolio_summary.get("total_return")
                }
            },
            "sample_trades": [
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "trade_type": t.trade_type,
                    "quantity": t.quantity,
                    "price": t.price,
                    "total_value": t.total_value,
                    "status": t.status,
                    "profit_loss": getattr(t, 'profit_loss', None),
                    "timestamp": t.timestamp.isoformat() if t.timestamp else None
                } for t in all_trades[:10]
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in debug portfolio: {str(e)}")
        import traceback
        return {
            "error": str(e), 
            "type": type(e).__name__,
            "traceback": traceback.format_exc()
        }

@app.post("/api/debug/migrate")
async def run_database_migration():
    """Run database migration to add missing columns and tables"""
    try:
        import sqlite3
        import os
        
        # Database path
        db_path = os.getenv("DATABASE_URL", "sqlite:///./trading_app.db").replace("sqlite:///", "")
        db_path = db_path.replace("sqlite:///data/", "/app/data/")  # Adjust for container path
        
        logger.info(f"Running migration on database: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        migrations_applied = []
        
        # Add position_id to trades table if it doesn't exist
        try:
            cursor.execute("ALTER TABLE trades ADD COLUMN position_id INTEGER NULL;")
            migrations_applied.append("Added position_id to trades table")
            logger.info("✅ Added position_id column to trades table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logger.info("ℹ️ position_id column already exists in trades table")
            else:
                logger.error(f"Error adding position_id to trades: {e}")
        
        # Create new tables
        new_tables = [
            ("strategies", """
                CREATE TABLE IF NOT EXISTS strategies (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    strategy_type VARCHAR NOT NULL,
                    description TEXT,
                    parameters JSON,
                    is_active BOOLEAN DEFAULT 1,
                    allocation_percentage FLOAT DEFAULT 10.0,
                    max_positions INTEGER DEFAULT 5,
                    risk_level VARCHAR DEFAULT 'MEDIUM',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """),
            ("positions", """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    strategy_id INTEGER,
                    symbol VARCHAR NOT NULL,
                    entry_price FLOAT NOT NULL,
                    quantity INTEGER NOT NULL,
                    position_size FLOAT NOT NULL,
                    status VARCHAR DEFAULT 'OPEN',
                    entry_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    exit_timestamp TIMESTAMP NULL,
                    exit_price FLOAT NULL,
                    realized_pnl FLOAT NULL,
                    unrealized_pnl FLOAT NULL,
                    stop_loss_price FLOAT NULL,
                    take_profit_price FLOAT NULL,
                    max_hold_time INTEGER NULL,
                    trailing_stop_percentage FLOAT NULL,
                    entry_signal JSON NULL,
                    sentiment_at_entry FLOAT NULL,
                    market_conditions JSON NULL
                );
            """),
            ("position_exit_events", """
                CREATE TABLE IF NOT EXISTS position_exit_events (
                    id INTEGER PRIMARY KEY,  
                    position_id INTEGER,
                    exit_type VARCHAR NOT NULL,
                    trigger_price FLOAT NOT NULL,
                    quantity_closed INTEGER NOT NULL,
                    exit_price FLOAT NOT NULL,
                    realized_pnl FLOAT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT
                );
            """),
            ("strategy_performance", """
                CREATE TABLE IF NOT EXISTS strategy_performance (
                    id INTEGER PRIMARY KEY,
                    strategy_id INTEGER,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_positions INTEGER DEFAULT 0,
                    open_positions INTEGER DEFAULT 0,
                    closed_positions INTEGER DEFAULT 0,
                    winning_positions INTEGER DEFAULT 0,
                    losing_positions INTEGER DEFAULT 0,
                    total_pnl FLOAT DEFAULT 0.0,
                    unrealized_pnl FLOAT DEFAULT 0.0,
                    realized_pnl FLOAT DEFAULT 0.0,
                    win_rate FLOAT DEFAULT 0.0,
                    average_win FLOAT DEFAULT 0.0,
                    average_loss FLOAT DEFAULT 0.0,
                    profit_factor FLOAT DEFAULT 0.0,
                    max_drawdown FLOAT DEFAULT 0.0,
                    sharpe_ratio FLOAT NULL,
                    allocated_capital FLOAT DEFAULT 0.0,
                    utilized_capital FLOAT DEFAULT 0.0,
                    available_capital FLOAT DEFAULT 0.0
                );
            """)
        ]
        
        for table_name, create_sql in new_tables:
            try:
                cursor.execute(create_sql)
                migrations_applied.append(f"Created {table_name} table")
                logger.info(f"✅ Created {table_name} table")
            except Exception as e:
                logger.error(f"Error creating {table_name} table: {e}")
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "migrations_applied": migrations_applied,
            "message": f"Applied {len(migrations_applied)} database migrations"
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return {
            "status": "error", 
            "error": str(e),
            "message": "Database migration failed"
        }

@app.post("/api/trades")
async def create_trade(trade: TradeCreate, db: Session = Depends(get_db)):
    """Create a new paper trade"""
    try:
        logger.info(f"Creating trade: {trade.symbol} {trade.trade_type} {trade.quantity}")
        result = trading_service.create_trade(db, trade)
        logger.info(f"Trade created successfully: ID {result.id}")
        return result
    except TradingAppException as e:
        logger.error(f"Trading error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating trade: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/trades/{trade_id}")
async def get_trade(trade_id: int, db: Session = Depends(get_db)):
    """Get a specific trade"""
    return trading_service.get_trade(db, trade_id)

@app.post("/api/trades/{trade_id}/close")
async def close_trade(trade_id: int, close_price: Optional[float] = Body(None, embed=True), db: Session = Depends(get_db)):
    """Close an open trade"""
    try:
        logger.info(f"Closing trade: {trade_id}")
        result = trading_service.close_trade(db, trade_id, close_price)
        logger.info(f"Trade closed successfully: {trade_id}")
        return result
    except TradingAppException as e:
        logger.error(f"Error closing trade {trade_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error closing trade {trade_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/trades/{trade_id}")
async def delete_trade(trade_id: int, db: Session = Depends(get_db)):
    """Delete a trade"""
    try:
        logger.info(f"Deleting trade: {trade_id}")
        result = trading_service.delete_trade(db, trade_id)
        logger.info(f"Trade deleted successfully: {trade_id}")
        return result
    except TradingAppException as e:
        logger.error(f"Error deleting trade {trade_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting trade {trade_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/sentiment/{symbol}")
async def get_sentiment(symbol: str, db: Session = Depends(get_db)):
    """Get sentiment analysis for a stock"""
    return sentiment_service.get_stock_sentiment(db, symbol)

@app.get("/api/sentiment")
async def get_all_sentiment(db: Session = Depends(get_db)):
    """Get sentiment for all tracked stocks"""
    return sentiment_service.get_all_sentiment(db)

@app.post("/api/analyze-sentiment")
async def analyze_sentiment(symbol: str = Body(..., embed=True), db: Session = Depends(get_db)):
    """Trigger sentiment analysis for a stock"""
    try:
        logger.info(f"Analyzing sentiment for: {symbol}")
        result = sentiment_service.analyze_stock_sentiment(db, symbol)
        logger.info(f"Sentiment analysis completed for {symbol}")
        return result
    except TradingAppException as e:
        logger.error(f"Sentiment analysis error for {symbol}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error analyzing sentiment for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/performance")
async def get_performance(db: Session = Depends(get_db)):
    """Get trading performance metrics"""
    return trading_service.get_performance_metrics(db)

@app.get("/api/portfolio-history")
async def get_portfolio_history(days: int = 30, db: Session = Depends(get_db)):
    """Get portfolio value history for charting"""
    try:
        history = trading_service.get_portfolio_history(db, days)
        return history
    except Exception as e:
        logger.error(f"Error getting portfolio history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/recalculate-balance")
async def recalculate_balance(db: Session = Depends(get_db)):
    """Debug endpoint to force balance recalculation"""
    try:
        trading_service.recalculate_current_balance(db)
        return {
            "message": "Balance recalculated",
            "current_balance": trading_service.current_balance
        }
    except Exception as e:
        logger.error(f"Error recalculating balance: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/stocks")
async def get_stocks(db: Session = Depends(get_db)):
    """Get all tracked stocks"""
    return data_service.get_tracked_stocks(db)

@app.post("/api/stocks")
async def add_stock(symbol: str = Body(..., embed=True), db: Session = Depends(get_db)):
    """Add a new stock to track"""
    try:
        # Validate symbol format
        if not symbol or not symbol.isalpha() or len(symbol) > 10:
            raise HTTPException(status_code=400, detail="Invalid stock symbol format")
        
        symbol = symbol.upper().strip()
        logger.info(f"Adding stock to tracking: {symbol}")
        result = data_service.add_stock(db, symbol)
        logger.info(f"Stock added successfully: {symbol}")
        return result
    except HTTPException:
        raise
    except TradingAppException as e:
        logger.error(f"Error adding stock {symbol}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error adding stock {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/market-data/{symbol}")
async def get_market_data(symbol: str, days: int = 30):
    """Get market data for a stock"""
    return data_service.get_market_data(symbol, days)

@app.post("/api/run-strategy")
async def run_strategy(db: Session = Depends(get_db)):
    """Run the sentiment-based trading strategy"""
    try:
        logger.info("Running sentiment-based trading strategy")
        result = trading_service.run_sentiment_strategy(db)
        logger.info(f"Strategy execution completed: {result.get('trades_executed', 0)} trades executed")
        return result
    except TradingAppException as e:
        logger.error(f"Strategy execution error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error running strategy: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Manual Testing and Recommendation Endpoints

@app.post("/api/analyze-bulk-sentiment")
async def analyze_bulk_sentiment(request: SentimentAnalysisRequest, db: Session = Depends(get_db)):
    """Manually trigger sentiment analysis for multiple stocks"""
    try:
        logger.info(f"Analyzing sentiment for {len(request.symbols)} symbols: {request.symbols}")
        
        results = []
        errors = []
        
        for symbol in request.symbols:
            try:
                result = sentiment_service.analyze_stock_sentiment(db, symbol.upper().strip())
                results.append(result)
                logger.info(f"Sentiment analysis completed for {symbol}: {result.overall_sentiment:.3f}")
            except Exception as e:
                error_msg = f"Failed to analyze {symbol}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        response = BulkSentimentResponse(
            results=results,
            errors=errors,
            total_processed=len(request.symbols),
            successful=len(results),
            failed=len(errors)
        )
        
        logger.info(f"Bulk sentiment analysis completed: {len(results)} successful, {len(errors)} failed")
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error in bulk sentiment analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/generate-recommendations")
async def generate_recommendations(symbols: Optional[List[str]] = Body(None), db: Session = Depends(get_db)):
    """Generate trade recommendations based on current sentiment"""
    try:
        logger.info(f"Generating trade recommendations for symbols: {symbols or 'all tracked stocks'}")
        
        recommendations = recommendation_service.generate_recommendations(db, symbols)
        
        logger.info(f"Generated {len(recommendations)} trade recommendations")
        return {
            "recommendations": recommendations,
            "total_generated": len(recommendations),
            "message": f"Generated {len(recommendations)} trade recommendations"
        }
        
    except TradingAppException as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/recommendations")
async def get_pending_recommendations(db: Session = Depends(get_db)):
    """Get all pending trade recommendations"""
    try:
        recommendations = recommendation_service.get_pending_recommendations(db)
        return {
            "recommendations": recommendations,
            "total_pending": len(recommendations)
        }
    except Exception as e:
        logger.error(f"Error getting pending recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/recommendations/{recommendation_id}/approve")
async def approve_recommendation(recommendation_id: int, db: Session = Depends(get_db)):
    """Approve and execute a trade recommendation"""
    try:
        logger.info(f"Approving recommendation {recommendation_id}")
        result = recommendation_service.approve_recommendation(db, recommendation_id)
        logger.info(f"Recommendation {recommendation_id} approved and executed")
        return result
    except TradingAppException as e:
        logger.error(f"Error approving recommendation {recommendation_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error approving recommendation {recommendation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/recommendations/{recommendation_id}/reject")
async def reject_recommendation(recommendation_id: int, reason: str = Body("", embed=True), db: Session = Depends(get_db)):
    """Reject a trade recommendation"""
    try:
        logger.info(f"Rejecting recommendation {recommendation_id}")
        result = recommendation_service.reject_recommendation(db, recommendation_id, reason)
        logger.info(f"Recommendation {recommendation_id} rejected")
        return result
    except TradingAppException as e:
        logger.error(f"Error rejecting recommendation {recommendation_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error rejecting recommendation {recommendation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/full-analysis-cycle")
async def run_full_analysis_cycle(symbols: Optional[List[str]] = Body(None), db: Session = Depends(get_db)):
    """Run complete analysis cycle: sentiment analysis + generate recommendations"""
    try:
        target_symbols = symbols or data_service.tracked_stocks
        logger.info(f"Running full analysis cycle for {len(target_symbols)} symbols")
        
        # Step 1: Analyze sentiment for all symbols
        sentiment_results = []
        sentiment_errors = []
        
        for symbol in target_symbols:
            try:
                result = sentiment_service.analyze_stock_sentiment(db, symbol)
                sentiment_results.append(result)
            except Exception as e:
                sentiment_errors.append(f"Sentiment analysis failed for {symbol}: {str(e)}")
        
        # Step 2: Generate recommendations
        recommendations = recommendation_service.generate_recommendations(db, target_symbols)
        
        result = {
            "sentiment_analysis": {
                "successful": len(sentiment_results),
                "failed": len(sentiment_errors),
                "errors": sentiment_errors
            },
            "recommendations": {
                "generated": len(recommendations),
                "recommendations": recommendations
            },
            "summary": f"Analyzed {len(sentiment_results)} stocks, generated {len(recommendations)} recommendations"
        }
        
        logger.info(f"Full analysis cycle completed: {len(sentiment_results)} sentiment analyses, {len(recommendations)} recommendations")
        return result
        
    except Exception as e:
        logger.error(f"Error in full analysis cycle: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Market Discovery Endpoints

@app.post("/api/market-scan")
async def scan_market(limit: int = 10, db: Session = Depends(get_db)):
    """Scan market news for trending stocks"""
    try:
        logger.info(f"Scanning market for trending stocks (limit: {limit})")
        discoveries = market_scanner.scan_trending_stocks(db, limit)
        
        return {
            "discoveries": discoveries,
            "total_found": len(discoveries),
            "message": f"Found {len(discoveries)} trending stocks"
        }
        
    except Exception as e:
        logger.error(f"Error in market scan: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/auto-discover")
async def auto_discover_stocks(min_trending_score: float = 0.5, db: Session = Depends(get_db)):
    """Automatically discover and analyze trending stocks"""
    try:
        logger.info(f"Running auto-discovery with min trending score: {min_trending_score}")
        result = market_scanner.auto_discover_and_analyze(db, min_trending_score)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        logger.info(f"Auto-discovery completed: {result['summary']}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in auto-discovery: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/discovery-to-recommendations")
async def discovery_to_recommendations(min_trending_score: float = 0.5, db: Session = Depends(get_db)):
    """Complete pipeline: discover stocks -> analyze sentiment -> generate recommendations"""
    try:
        logger.info("Running complete discovery-to-recommendations pipeline")
        
        # Step 1: Auto-discover stocks
        discovery_result = market_scanner.auto_discover_and_analyze(db, min_trending_score)
        
        if "error" in discovery_result:
            raise HTTPException(status_code=400, detail=discovery_result["error"])
        
        added_stocks = discovery_result.get("added_stocks", [])
        
        # Step 2: Generate recommendations for discovered stocks
        recommendations = []
        if added_stocks:
            recommendations = recommendation_service.generate_recommendations(db, added_stocks)
        
        result = {
            "discovery": discovery_result,
            "recommendations": {
                "generated": len(recommendations),
                "recommendations": recommendations
            },
            "summary": f"Discovered {len(added_stocks)} stocks, generated {len(recommendations)} recommendations"
        }
        
        logger.info(f"Discovery-to-recommendations pipeline completed: {result['summary']}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in discovery-to-recommendations pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Position Management Endpoints

@app.get("/api/strategies", response_model=List[StrategyResponse])
async def get_strategies(active_only: bool = True, db: Session = Depends(get_db)):
    """Get all trading strategies."""
    try:
        strategies = strategy_service.get_strategies(db, active_only)
        return strategies
    except Exception as e:
        logger.error(f"Error getting strategies: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/strategies", response_model=StrategyResponse)
async def create_strategy(strategy: StrategyCreate, db: Session = Depends(get_db)):
    """Create a new trading strategy."""
    try:
        logger.info(f"Creating strategy: {strategy.name} ({strategy.strategy_type})")
        result = strategy_service.create_strategy(db, strategy)
        logger.info(f"Strategy created successfully: {result.name}")
        return result
    except TradingAppException as e:
        logger.error(f"Strategy creation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating strategy: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/strategies/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Get a specific strategy."""
    try:
        strategy = strategy_service.get_strategy(db, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        return strategy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy {strategy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/strategies/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(strategy_id: int, update_data: dict, db: Session = Depends(get_db)):
    """Update a strategy."""
    try:
        logger.info(f"Updating strategy: {strategy_id}")
        result = strategy_service.update_strategy(db, strategy_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="Strategy not found")
        logger.info(f"Strategy updated successfully: {strategy_id}")
        return result
    except HTTPException:
        raise
    except TradingAppException as e:
        logger.error(f"Strategy update error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating strategy {strategy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/strategies/{strategy_id}/run")
async def run_strategy(strategy_id: int, symbols: Optional[List[str]] = Body(None), 
                      force_analysis: bool = Body(False), db: Session = Depends(get_db)):
    """Run a specific trading strategy."""
    try:
        logger.info(f"Running strategy: {strategy_id}")
        request = StrategyRunRequest(
            strategy_id=strategy_id,
            symbols=symbols,
            force_analysis=force_analysis
        )
        result = strategy_service.run_strategy(db, request)
        logger.info(f"Strategy execution completed: {result.get('message', 'No message')}")
        return result
    except TradingAppException as e:
        logger.error(f"Strategy execution error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error running strategy {strategy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/strategies/run-all")
async def run_all_strategies(db: Session = Depends(get_db)):
    """Run all active trading strategies."""
    try:
        logger.info("Running all active strategies")
        result = strategy_service.run_all_active_strategies(db)
        logger.info(f"All strategies completed: {result.get('successful_strategies', 0)} successful")
        return result
    except Exception as e:
        logger.error(f"Error running all strategies: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/positions", response_model=PositionSummaryResponse)
async def get_positions(strategy_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get position summary for all strategies or a specific strategy."""
    try:
        summary = position_manager.get_position_summary(db, strategy_id)
        if 'error' in summary:
            raise HTTPException(status_code=400, detail=summary['error'])
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting positions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/positions/{position_id}/close")
async def close_position(position_id: int, request: ExitConditionRequest, db: Session = Depends(get_db)):
    """Manually close a position."""
    try:
        logger.info(f"Closing position: {position_id}")
        from models import ExitConditionType
        exit_type = ExitConditionType(request.exit_type)
        
        exit_event = position_manager.close_position(
            db, position_id, exit_type, request.reason, request.partial_quantity
        )
        
        logger.info(f"Position closed successfully: {position_id}")
        return {
            "message": f"Position {position_id} closed successfully",
            "exit_event": {
                "exit_type": exit_event.exit_type,
                "exit_price": exit_event.exit_price,
                "realized_pnl": exit_event.realized_pnl,
                "quantity_closed": exit_event.quantity_closed
            }
        }
    except TradingAppException as e:
        logger.error(f"Error closing position {position_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error closing position {position_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/positions/check-exits")
async def check_position_exits(db: Session = Depends(get_db)):
    """Check all positions for exit conditions and close if triggered."""
    try:
        logger.info("Checking position exit conditions")
        exit_events = position_manager.check_exit_conditions(db)
        
        return {
            "message": f"Checked exit conditions, processed {len(exit_events)} exits",
            "exit_events": exit_events,
            "total_exits": len(exit_events)
        }
    except Exception as e:
        logger.error(f"Error checking position exits: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/positions/update-pnl")
async def update_unrealized_pnl(db: Session = Depends(get_db)):
    """Update unrealized P&L for all open positions."""
    try:
        logger.info("Updating unrealized P&L for all positions")
        position_manager.update_unrealized_pnl(db)
        
        return {"message": "Unrealized P&L updated for all open positions"}
    except Exception as e:
        logger.error(f"Error updating unrealized P&L: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Performance Analysis Endpoints

@app.get("/api/performance/strategy/{strategy_id}")
async def get_strategy_performance(strategy_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Get performance metrics for a specific strategy."""
    try:
        logger.info(f"Getting performance metrics for strategy {strategy_id}")
        metrics = performance_service.calculate_strategy_metrics(db, strategy_id, days)
        
        if 'error' in metrics:
            raise HTTPException(status_code=404, detail=metrics['error'])
        
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/performance/compare")
async def compare_strategies(strategy_ids: List[int] = Body(...), days: int = Body(30), 
                           db: Session = Depends(get_db)):
    """Compare performance across multiple strategies."""
    try:
        logger.info(f"Comparing strategies: {strategy_ids}")
        comparison = performance_service.compare_strategies(db, strategy_ids, days)
        
        if 'error' in comparison:
            raise HTTPException(status_code=400, detail=comparison['error'])
        
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing strategies: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/performance/portfolio")
async def get_portfolio_performance(days: int = 30, db: Session = Depends(get_db)):
    """Get overall portfolio performance."""
    try:
        logger.info("Getting portfolio performance")
        
        # First try the new strategy-based performance service
        try:
            portfolio_perf = performance_service.get_portfolio_performance(db, days)
            if 'error' not in portfolio_perf:
                return portfolio_perf
        except Exception as e:
            logger.warning(f"Strategy-based performance failed, falling back to trade-based: {str(e)}")
        
        # Fallback to trading service performance if strategies don't exist
        logger.info("Using trade-based performance calculation")
        performance_metrics = trading_service.get_performance_metrics(db)
        portfolio_history = trading_service.get_portfolio_history(db, days)
        
        # Calculate additional portfolio metrics
        current_value = performance_metrics.get('current_balance', config.INITIAL_BALANCE)
        total_return_pct = ((current_value - config.INITIAL_BALANCE) / config.INITIAL_BALANCE) * 100
        
        # Calculate portfolio value including unrealized gains
        portfolio_summary = trading_service.get_portfolio_summary(db)
        portfolio_value = portfolio_summary.get('portfolio_value', current_value)
        total_return_portfolio_pct = ((portfolio_value - config.INITIAL_BALANCE) / config.INITIAL_BALANCE) * 100
        
        return {
            'total_return_percentage': round(total_return_portfolio_pct, 2),
            'portfolio_value': round(portfolio_value, 2),
            'initial_balance': config.INITIAL_BALANCE,
            'current_balance': round(current_value, 2),
            'total_trades': performance_metrics.get('total_trades', 0),
            'win_rate': round(performance_metrics.get('win_rate', 0), 2),
            'total_profit_loss': round(performance_metrics.get('total_profit_loss', 0), 2),
            'sharpe_ratio': round(performance_metrics.get('sharpe_ratio', 0), 3),
            'max_drawdown_percentage': round(performance_metrics.get('max_drawdown', 0), 2),
            'period_days': days,
            'history': portfolio_history[-7:] if portfolio_history else []  # Last 7 data points
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/performance/history")
async def get_performance_history(strategy_id: Optional[int] = None, days: int = 30, 
                                db: Session = Depends(get_db)):
    """Get historical performance data for charting."""
    try:
        logger.info(f"Getting performance history for strategy {strategy_id or 'portfolio'}")
        history = performance_service.get_performance_history(db, strategy_id, days)
        
        if 'error' in history:
            raise HTTPException(status_code=400, detail=history['error'])
        
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/performance/report")
async def generate_performance_report(strategy_id: Optional[int] = None, days: int = 30, 
                                    db: Session = Depends(get_db)):
    """Generate comprehensive performance report."""
    try:
        logger.info(f"Generating performance report for {'strategy ' + str(strategy_id) if strategy_id else 'portfolio'}")
        report = performance_service.generate_performance_report(db, strategy_id, days)
        
        if 'error' in report:
            raise HTTPException(status_code=400, detail=report['error'])
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating performance report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/portfolio/summary")
async def get_portfolio_summary(db: Session = Depends(get_db)):
    """Get comprehensive portfolio summary with current values."""
    try:
        # Get current balance and positions
        trading_service.recalculate_current_balance(db)
        
        # Get performance metrics
        performance = trading_service.get_performance_metrics(db)
        
        # Get portfolio summary from trading service
        portfolio_summary = trading_service.get_portfolio_summary(db)
        
        # Get recent trades
        recent_trades = db.query(Trade).order_by(desc(Trade.timestamp)).limit(5).all()
        
        # Combine all data
        summary = {
            "current_balance": trading_service.current_balance,
            "initial_balance": trading_service.initial_balance,
            "portfolio_value": portfolio_summary.get("portfolio_value", trading_service.current_balance),
            "total_return_pct": ((trading_service.current_balance - trading_service.initial_balance) / trading_service.initial_balance) * 100,
            "total_return_amount": trading_service.current_balance - trading_service.initial_balance,
            "performance_metrics": performance,
            "open_positions": len([t for t in db.query(Trade).filter(Trade.status == "OPEN").all()]),
            "closed_positions": len([t for t in db.query(Trade).filter(Trade.status == "CLOSED").all()]),
            "recent_trades": [
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "trade_type": t.trade_type,
                    "quantity": t.quantity,
                    "price": t.price,
                    "status": t.status,
                    "timestamp": t.timestamp.isoformat(),
                    "profit_loss": t.profit_loss
                } for t in recent_trades
            ]
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Portfolio summary error: {str(e)}")

@app.post("/api/debug/close-old-trades")
async def debug_close_old_trades(db: Session = Depends(get_db)):
    """Close old trades that have been open for more than 24 hours for testing."""
    try:
        from datetime import datetime, timedelta
        from services.data_service import DataService
        
        # Find trades older than 24 hours that are still open
        cutoff_time = datetime.now() - timedelta(hours=24)
        old_trades = db.query(Trade).filter(
            Trade.status == "OPEN",
            Trade.timestamp < cutoff_time
        ).limit(10).all()  # Limit to 10 to avoid overwhelming
        
        if not old_trades:
            return {
                "status": "success",
                "message": "No old trades found to close",
                "closed_trades": 0
            }
        
        data_service = DataService()
        closed_count = 0
        
        for trade in old_trades:
            try:
                # Get current market price
                market_data = data_service.get_market_data(trade.symbol, days=1)
                current_price = market_data.get('current_price', trade.price)
                
                # Close the trade
                closed_trade = trading_service.close_trade(db, trade.id, current_price)
                closed_count += 1
                
                logger.info(f"Debug closed trade {trade.id}: {trade.symbol} P&L: ${closed_trade.profit_loss:.2f}")
                
            except Exception as e:
                logger.error(f"Error closing trade {trade.id}: {str(e)}")
                continue
        
        return {
            "status": "success", 
            "message": f"Closed {closed_count} old trades",
            "closed_trades": closed_count
        }
        
    except Exception as e:
        logger.error(f"Error closing old trades: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}"
        }

# Tax Optimization Endpoints
@app.get("/api/tax/optimize")
async def get_tax_optimization(db: Session = Depends(get_db)):
    """Get tax-optimized trading recommendations."""
    try:
        from services.tax_optimization_service import tax_optimization_service
        
        recommendations = tax_optimization_service.optimize_trade_timing(db)
        
        if 'error' in recommendations:
            raise HTTPException(status_code=400, detail=recommendations['error'])
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tax optimization: {str(e)}")
        raise HTTPException(status_code=500, detail="Tax optimization error")

@app.get("/api/tax/loss-harvesting")
async def get_tax_loss_harvesting(db: Session = Depends(get_db)):
    """Get tax loss harvesting opportunities."""
    try:
        from services.tax_optimization_service import tax_optimization_service
        
        opportunities = tax_optimization_service.suggest_tax_loss_harvesting(db)
        
        if 'error' in opportunities:
            raise HTTPException(status_code=400, detail=opportunities['error'])
        
        return opportunities
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tax loss harvesting: {str(e)}")
        raise HTTPException(status_code=500, detail="Tax loss harvesting error")

@app.get("/api/tax/report")
async def get_tax_report(year: Optional[int] = None, db: Session = Depends(get_db)):
    """Generate annual tax report."""
    try:
        from services.tax_optimization_service import tax_optimization_service
        
        report = tax_optimization_service.calculate_annual_tax_report(db, year)
        
        if 'error' in report:
            raise HTTPException(status_code=400, detail=report['error'])
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating tax report: {str(e)}")
        raise HTTPException(status_code=500, detail="Tax report error")

@app.post("/api/tax/analyze-trade/{trade_id}")
async def analyze_trade_tax_impact(trade_id: int, db: Session = Depends(get_db)):
    """Analyze tax impact of closing a specific trade."""
    try:
        from services.tax_optimization_service import tax_optimization_service
        from services.data_service import DataService
        
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        if trade.status != "OPEN":
            raise HTTPException(status_code=400, detail="Trade is not open")
        
        # Get current market price
        data_service = DataService()
        market_data = data_service.get_market_data(trade.symbol, days=1)
        current_price = market_data.get('current_price', trade.price)
        
        # Calculate tax impact
        tax_analysis = tax_optimization_service.calculate_tax_impact(db, trade, current_price)
        
        if 'error' in tax_analysis:
            raise HTTPException(status_code=400, detail=tax_analysis['error'])
        
        return {
            "trade_id": trade_id,
            "symbol": trade.symbol,
            "entry_price": trade.price,
            "current_price": current_price,
            "tax_analysis": tax_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing trade tax impact: {str(e)}")
        raise HTTPException(status_code=500, detail="Trade tax analysis error")

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Trading Sentiment Analysis API starting up...")
    logger.info(f"Initial balance: ${config.INITIAL_BALANCE:,.2f}")
    logger.info(f"Max position size: {config.MAX_POSITION_SIZE:.1%}")
    
    # Start the scheduler service for automated trade management
    try:
        from services.scheduler_service import scheduler_service
        await scheduler_service.start()
        logger.info("Scheduler service started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler service: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Trading Sentiment Analysis API shutting down...")
    
    # Stop the scheduler service
    try:
        from services.scheduler_service import scheduler_service
        await scheduler_service.stop()
        logger.info("Scheduler service stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop scheduler service: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 