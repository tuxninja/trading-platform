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
from models import Trade, SentimentData, StockData, TradeRecommendation
from schemas import (
    TradeCreate, TradeResponse, SentimentResponse,
    SentimentAnalysisRequest, BulkSentimentResponse,
    TradeRecommendationResponse, MarketScanResult,
    GoogleLoginRequest, AuthResponse
)
from services.trading_service import TradingService
from services.sentiment_service import SentimentService
from services.data_service import DataService
from services.recommendation_service import RecommendationService
from services.market_scanner import MarketScannerService
from config import config, setup_logging
from exceptions import TradingAppException
from auth import auth_service, get_current_user, optional_auth

# Setup logging
logger = setup_logging()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Trading Sentiment Analysis", 
    version="1.0.0",
    description="Sentiment-based paper trading system"
)

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
    return trading_service.get_all_trades(db)

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

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Trading Sentiment Analysis API starting up...")
    logger.info(f"Initial balance: ${config.INITIAL_BALANCE:,.2f}")
    logger.info(f"Max position size: {config.MAX_POSITION_SIZE:.1%}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Trading Sentiment Analysis API shutting down...")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 