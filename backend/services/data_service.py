import yfinance as yf
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import random
import logging

from models import StockData
from schemas import StockDataResponse
from config import config
from exceptions import StockDataError, APIRateLimitError

class DataService:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.last_api_call = 0  # For rate limiting
    
    def get_market_data(self, symbol: str, days: int = 30, db: Session = None) -> Dict:
        """Get market data for a stock symbol with proper caching fallback"""
        try:
            # First, try to get real-time data from Yahoo Finance with enhanced retry
            stock = yf.Ticker(symbol)
            hist = None
            
            # Try multiple approaches to get current market data
            approaches = [
                ("1d", "1 day history"),
                ("5d", "5 day history"), 
                ("1mo", "1 month history"),
                ("3mo", "3 month history"),
                ("ytd", "year to date history"),
                ("1y", "1 year history")
            ]
            
            for period, description in approaches:
                try:
                    self.logger.debug(f"Attempting {description} for {symbol}")
                    hist = stock.history(period=period)
                    if not hist.empty:
                        self.logger.info(f"Successfully retrieved {description} for {symbol}")
                        break
                except Exception as e:
                    self.logger.debug(f"Failed {description} for {symbol}: {str(e)}")
                    continue
            
            # If history failed, try getting current info directly
            if hist is None or hist.empty:
                try:
                    self.logger.info(f"History failed for {symbol}, trying direct info lookup")
                    info = stock.info
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                    
                    if current_price and current_price > 0:
                        self.logger.info(f"Retrieved current price {current_price} for {symbol} from info")
                        return {
                            "symbol": symbol,
                            "current_price": float(current_price),
                            "company_name": info.get('longName', f"{symbol} Inc."),
                            "sector": info.get('sector', 'Unknown'),
                            "industry": info.get('industry', 'Unknown'),
                            "market_cap": info.get('marketCap'),
                            "pe_ratio": info.get('trailingPE'),
                            "dividend_yield": info.get('dividendYield'),
                            "historical_data": [],  # No historical data available
                            "data_source": "yahoo_info_direct",
                            "price_change": 0,
                            "price_change_pct": 0
                        }
                except Exception as e:
                    self.logger.warning(f"Direct info lookup also failed for {symbol}: {str(e)}")
            
            # If real-time data failed, try to get cached data from database (only if recent)
            if (hist is None or hist.empty) and db is not None:
                self.logger.info(f"Yahoo Finance failed for {symbol}, checking database cache")
                cached_data = db.query(StockData).filter(StockData.symbol == symbol).order_by(StockData.timestamp.desc()).first()
                
                if cached_data and cached_data.close_price > 0:
                    # Only use cached data if it's less than 4 hours old
                    from datetime import datetime, timedelta
                    cache_age_hours = (datetime.now() - cached_data.timestamp).total_seconds() / 3600
                    
                    if cache_age_hours <= 4:
                        self.logger.info(f"Using cached data for {symbol} from {cached_data.timestamp} ({cache_age_hours:.1f} hours old)")
                        return {
                            "symbol": symbol,
                            "current_price": float(cached_data.close_price),
                            "price_change": 0,  # Could calculate from previous record
                            "price_change_pct": 0,
                            "market_cap": cached_data.market_cap,
                            "pe_ratio": cached_data.pe_ratio,
                            "dividend_yield": cached_data.dividend_yield,
                            "historical_data": [],
                            "company_name": symbol,
                            "sector": "Unknown",
                            "industry": "Unknown",
                            "data_source": f"cached_{cache_age_hours:.1f}h_old"
                        }
                    else:
                        self.logger.warning(f"Cached data for {symbol} is too old ({cache_age_hours:.1f} hours), will return error if no real-time data")
            
            # If both real-time and cached data failed, return error - NO MOCK DATA
            if hist is None or hist.empty:
                self.logger.error(f"CRITICAL: No real market data available for {symbol}")
                return {
                    "error": f"Unable to retrieve current market data for {symbol}",
                    "message": "Real-time market data is temporarily unavailable. Please try again.",
                    "symbol": symbol,
                    "data_source": "unavailable"
                }
            
            # Get current stock info
            try:
                info = stock.info
            except:
                info = {}
            
            # Format historical data
            historical_data = []
            for index, row in hist.iterrows():
                historical_data.append({
                    "date": index.strftime("%Y-%m-%d"),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume'])
                })
            
            # Calculate basic metrics
            current_price = float(hist['Close'].iloc[-1])
            if len(hist) > 1:
                price_change = float(hist['Close'].iloc[-1] - hist['Close'].iloc[-2])
                price_change_pct = (price_change / hist['Close'].iloc[-2]) * 100
            else:
                price_change = 0
                price_change_pct = 0
            
            # Get additional info
            market_cap = info.get('marketCap', None)
            pe_ratio = info.get('trailingPE', None)
            dividend_yield = info.get('dividendYield', None)
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "price_change": price_change,
                "price_change_pct": price_change_pct,
                "market_cap": market_cap,
                "pe_ratio": pe_ratio,
                "dividend_yield": dividend_yield,
                "historical_data": historical_data,
                "company_name": info.get('longName', symbol),
                "sector": info.get('sector', 'Unknown'),
                "industry": info.get('industry', 'Unknown')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {str(e)}")
            return {
                "error": f"Failed to retrieve market data for {symbol}: {str(e)}",
                "symbol": symbol,
                "data_source": "error"
            }
    
    def save_stock_data(self, db: Session, symbol: str) -> StockDataResponse:
        """Save current stock data to database"""
        try:
            market_data = self.get_market_data(symbol, days=1)
            
            # Check if we have valid market data
            if "error" in market_data:
                self.logger.error(f"Cannot save stock data for {symbol}: {market_data['error']}")
                raise Exception(f"Market data unavailable for {symbol}")
            
            # Use current price data if no historical data available
            if not market_data.get("historical_data"):
                hist_data = {
                    "open": market_data["current_price"],
                    "high": market_data["current_price"],
                    "low": market_data["current_price"],
                    "close": market_data["current_price"],
                    "volume": 0  # No volume data available
                }
            else:
                hist_data = market_data["historical_data"][-1]
            
            stock_data = StockData(
                symbol=symbol,
                open_price=hist_data["open"],
                high_price=hist_data["high"],
                low_price=hist_data["low"],
                close_price=hist_data["close"],
                volume=hist_data["volume"],
                market_cap=market_data.get("market_cap"),
                pe_ratio=market_data.get("pe_ratio"),
                dividend_yield=market_data.get("dividend_yield")
            )
            
            db.add(stock_data)
            db.commit()
            db.refresh(stock_data)
            
            return StockDataResponse.from_orm(stock_data)
            
        except Exception as e:
            self.logger.error(f"Error saving stock data for {symbol}: {str(e)}")
            db.rollback()
            raise StockDataError(f"Failed to save stock data for {symbol}: {str(e)}")
    
    def get_tracked_stocks(self, db: Session) -> List[Dict]:
        """Get list of tracked stocks with latest data from DB if available, else live/mock data. Tracked stocks are all unique symbols in stock_data."""
        # Get all unique symbols from the stock_data table
        symbols = [row[0] for row in db.query(StockData.symbol).distinct().all()]
        stocks_data = []
        for symbol in symbols:
            try:
                # Get real-time market data with historical charts
                market_data = self.get_market_data(symbol, days=30, db=db)
                
                if "error" not in market_data:
                    stocks_data.append(market_data)
                else:
                    # If market data failed, try to get basic cached data
                    stock_db = db.query(StockData).filter(StockData.symbol == symbol).order_by(StockData.timestamp.desc()).first()
                    if stock_db:
                        # Get historical data for price chart (last 30 days)
                        historical_stocks = db.query(StockData).filter(
                            StockData.symbol == symbol
                        ).order_by(StockData.timestamp.desc()).limit(30).all()
                        
                        historical_data = [
                            {
                                "date": stock.timestamp.strftime("%Y-%m-%d"),
                                "close": float(stock.close_price),
                                "open": float(stock.open_price),
                                "high": float(stock.high_price),
                                "low": float(stock.low_price),
                                "volume": stock.volume or 0
                            }
                            for stock in reversed(historical_stocks)  # Reverse to get chronological order
                        ]
                        
                        stocks_data.append({
                            "symbol": stock_db.symbol,
                            "current_price": float(stock_db.close_price),
                            "price_change": 0,  # Could be calculated if needed
                            "price_change_pct": 0,
                            "market_cap": stock_db.market_cap,
                            "pe_ratio": stock_db.pe_ratio,
                            "dividend_yield": stock_db.dividend_yield,
                            "historical_data": historical_data,
                            "company_name": symbol,
                            "sector": "Unknown",
                            "industry": "Unknown",
                            "data_source": "cached_with_history"
                        })
                    else:
                        # No market data available at all
                        self.logger.warning(f"No market data available for {symbol}")
                        stocks_data.append({
                            "symbol": symbol,
                            "error": f"Market data unavailable for {symbol}",
                            "historical_data": [],
                            "data_source": "unavailable"
                        })
                        
            except Exception as e:
                self.logger.error(f"Exception getting data for {symbol}: {str(e)}")
                stocks_data.append({
                    "symbol": symbol,
                    "error": f"Failed to retrieve data for {symbol}: {str(e)}",
                    "historical_data": [],
                    "data_source": "error"
                })
                
        return stocks_data
    
    def add_stock(self, db: Session, symbol: str) -> Dict:
        """Add a stock to tracking by getting real market data and saving to database"""
        try:
            # Get real market data for the symbol
            market_data = self.get_market_data(symbol, days=30, db=db)
            
            if "error" in market_data:
                raise Exception(f"Cannot add {symbol}: {market_data['error']}")
            
            # Save the stock data to database
            try:
                self.save_stock_data(db, symbol)
                self.logger.info(f"Successfully added {symbol} to tracking with real market data")
            except Exception as save_error:
                self.logger.warning(f"Could not save {symbol} to database: {str(save_error)}")
            
            return {
                "message": f"Successfully added {symbol} to tracking",
                "symbol": symbol,
                "current_price": market_data.get("current_price"),
                "company_name": market_data.get("company_name"),
                "sector": market_data.get("sector"),
                "data_source": market_data.get("data_source")
            }
            
        except Exception as e:
            self.logger.error(f"Error adding stock {symbol}: {str(e)}")
            raise Exception(f"Failed to add {symbol}: {str(e)}")
    
    def _rate_limit(self) -> None:
        """Implement rate limiting for API calls."""
        elapsed = time.time() - self.last_api_call
        if elapsed < config.API_RATE_LIMIT:
            sleep_time = config.API_RATE_LIMIT - elapsed
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_api_call = time.time()
    
    def add_stock(self, db: Session, symbol: str) -> Dict:
        """Add a new stock to track with validation and error handling."""
        try:
            # Validate input
            if not symbol or not symbol.strip():
                raise StockDataError("Symbol cannot be empty")
            
            symbol = symbol.upper().strip()
            
            # Validate symbol format (basic check)
            if not symbol.isalpha() or len(symbol) > 10:
                raise StockDataError(f"Invalid symbol format: {symbol}")
            
            self.logger.info(f"Adding stock to tracking: {symbol}")
            
            # Remove symbol from tracked_stocks if it already exists
            if symbol in self.tracked_stocks:
                self.tracked_stocks.remove(symbol)
                self.logger.info(f"Removed existing {symbol} from tracked stocks")
            
            # Delete all existing StockData entries for this symbol
            deleted_count = db.query(StockData).filter(StockData.symbol == symbol).delete()
            if deleted_count > 0:
                self.logger.info(f"Deleted {deleted_count} existing records for {symbol}")
            db.commit()

            # Rate limiting
            self._rate_limit()
            
            # Validate symbol by getting market data
            market_data = self.get_market_data(symbol, days=1)
            
            # Check if market data indicates an invalid symbol
            if "error" in market_data or market_data.get("current_price", 0) <= 0:
                raise StockDataError(f"Invalid or unavailable stock symbol: {symbol}")

            # Add to tracked stocks
            self.tracked_stocks.append(symbol)

            # Save initial data
            try:
                stock_data = self.save_stock_data(db, symbol)
                self.logger.info(f"Saved initial stock data for {symbol}")
            except Exception as e:
                self.logger.warning(f"Could not save initial stock data for {symbol}: {str(e)}")
                # Don't fail the entire operation if we can't save to DB

            self.logger.info(f"Successfully added {symbol} to tracking")
            return {
                "message": f"Successfully added {symbol}",
                "symbol": symbol,
                "data": market_data
            }

        except StockDataError:
            db.rollback()
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error adding stock {symbol}: {str(e)}")
            db.rollback()
            raise StockDataError(f"Failed to add stock {symbol}: {str(e)}")
    
    def get_stock_history(self, db: Session, symbol: str, days: int = 30) -> List[StockDataResponse]:
        """Get historical stock data from database"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        stock_data = db.query(StockData).filter(
            StockData.symbol == symbol,
            StockData.timestamp >= cutoff_date
        ).order_by(StockData.timestamp).all()
        
        return [StockDataResponse.from_orm(data) for data in stock_data]
    
    def run_daily_data_collection(self, db: Session):
        """Collect daily market data for all tracked stocks"""
        results = []
        
        for symbol in self.tracked_stocks:
            try:
                result = self.save_stock_data(db, symbol)
                results.append(result)
                self._rate_limit()  # Rate limiting
            except Exception as e:
                self.logger.error(f"Error collecting data for {symbol}: {str(e)}")
        
        return results 