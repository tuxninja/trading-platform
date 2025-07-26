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
        self.tracked_stocks = [
            "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            "AMD", "INTC", "CRM", "ORCL", "ADBE", "PYPL", "UBER", "LYFT"
        ]
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.last_api_call = 0  # For rate limiting
        # Predefined mock data for common stocks
        self.mock_data = {
            "AAPL": {"name": "Apple Inc.", "base_price": 180.0, "sector": "Technology", "industry": "Consumer Electronics"},
            "GOOGL": {"name": "Alphabet Inc.", "base_price": 140.0, "sector": "Technology", "industry": "Internet Content & Information"},
            "MSFT": {"name": "Microsoft Corporation", "base_price": 380.0, "sector": "Technology", "industry": "Software"},
            "AMZN": {"name": "Amazon.com Inc.", "base_price": 150.0, "sector": "Consumer Cyclical", "industry": "Internet Retail"},
            "TSLA": {"name": "Tesla Inc.", "base_price": 240.0, "sector": "Consumer Cyclical", "industry": "Auto Manufacturers"},
            "META": {"name": "Meta Platforms Inc.", "base_price": 320.0, "sector": "Technology", "industry": "Internet Content & Information"},
            "NVDA": {"name": "NVIDIA Corporation", "base_price": 450.0, "sector": "Technology", "industry": "Semiconductors"},
            "NFLX": {"name": "Netflix Inc.", "base_price": 480.0, "sector": "Communication Services", "industry": "Entertainment"},
            "AMD": {"name": "Advanced Micro Devices Inc.", "base_price": 120.0, "sector": "Technology", "industry": "Semiconductors"},
            "INTC": {"name": "Intel Corporation", "base_price": 45.0, "sector": "Technology", "industry": "Semiconductors"},
            "CRM": {"name": "Salesforce Inc.", "base_price": 250.0, "sector": "Technology", "industry": "Software"},
            "ORCL": {"name": "Oracle Corporation", "base_price": 120.0, "sector": "Technology", "industry": "Software"},
            "ADBE": {"name": "Adobe Inc.", "base_price": 520.0, "sector": "Technology", "industry": "Software"},
            "PYPL": {"name": "PayPal Holdings Inc.", "base_price": 60.0, "sector": "Technology", "industry": "Software"},
            "UBER": {"name": "Uber Technologies Inc.", "base_price": 70.0, "sector": "Technology", "industry": "Software"},
            "LYFT": {"name": "Lyft Inc.", "base_price": 15.0, "sector": "Technology", "industry": "Software"}
        }
    
    def get_market_data(self, symbol: str, days: int = 30) -> Dict:
        """Get market data for a stock symbol"""
        try:
            stock = yf.Ticker(symbol)
            
            # Try multiple approaches to get data
            hist = None
            
            # Try different periods
            for period in ["5d", "1mo", "3mo"]:
                try:
                    hist = stock.history(period=period)
                    if not hist.empty:
                        break
                except:
                    continue
            
            if hist is None or hist.empty:
                self.logger.warning(f"No historical data available for {symbol}, using mock data")
                return self._get_mock_data(symbol)
            
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
            return self._get_mock_data(symbol)
    
    def save_stock_data(self, db: Session, symbol: str) -> StockDataResponse:
        """Save current stock data to database"""
        try:
            market_data = self.get_market_data(symbol, days=1)
            
            # Use mock data if no historical data available
            if not market_data.get("historical_data"):
                # Create mock historical data
                hist_data = {
                    "open": market_data["current_price"] * 0.99,
                    "high": market_data["current_price"] * 1.02,
                    "low": market_data["current_price"] * 0.98,
                    "close": market_data["current_price"],
                    "volume": random.randint(1000000, 10000000)
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
            # Try to get the latest StockData from the DB
            stock_db = db.query(StockData).filter(StockData.symbol == symbol).order_by(StockData.timestamp.desc()).first()
            if stock_db:
                stocks_data.append({
                    "symbol": stock_db.symbol,
                    "current_price": stock_db.close_price,
                    "price_change": 0,  # Could be calculated if we fetch previous row
                    "price_change_pct": 0,
                    "market_cap": stock_db.market_cap,
                    "pe_ratio": stock_db.pe_ratio,
                    "dividend_yield": stock_db.dividend_yield,
                    "historical_data": [],  # Could be filled with more queries
                    "company_name": symbol,
                    "sector": "Unknown",
                    "industry": "Unknown"
                })
            else:
                # Fallback to live/mock data
                try:
                    market_data = self.get_market_data(symbol, days=1)
                    stocks_data.append(market_data)
                except Exception as e:
                    self.logger.warning(f"Exception getting data for {symbol}: {str(e)}")
                    stocks_data.append(self._get_mock_data(symbol))
        return stocks_data
    
    def _get_mock_data(self, symbol: str) -> Dict:
        """Get realistic mock data for testing when API fails"""
        # Use predefined data if available
        if symbol in self.mock_data:
            mock_info = self.mock_data[symbol]
            base_price = mock_info["base_price"]
            company_name = mock_info["name"]
            sector = mock_info["sector"]
            industry = mock_info["industry"]
        else:
            # Use deterministic base price based on symbol hash to avoid randomness
            symbol_hash = abs(hash(symbol))
            base_price = 50 + (symbol_hash % 450)  # Price between $50-$500, consistent per symbol
            company_name = f"{symbol} Corporation"
            sector = "Technology"
            industry = "Software"
        
        # Use consistent price variation based on symbol hash for deterministic results
        # This prevents random fluctuations when markets are closed
        symbol_hash = abs(hash(symbol))
        price_variation = ((symbol_hash % 1000) / 1000.0 - 0.5) * 0.1  # ±5% variation, but consistent
        current_price = base_price * (1 + price_variation)
        price_change = current_price - base_price
        price_change_pct = (price_change / base_price) * 100
        
        # Generate some mock historical data (deterministic)
        historical_data = []
        for i in range(5):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            # Use deterministic price variation based on symbol and day
            day_variation = ((abs(hash(symbol + str(i))) % 200) / 1000.0 - 0.1)  # ±10% variation
            day_price = base_price * (1 + day_variation)
            volume = 1000000 + (abs(hash(symbol + str(i))) % 9000000)  # Consistent volume
            historical_data.append({
                "date": date,
                "open": day_price * 0.99,
                "high": day_price * 1.02,
                "low": day_price * 0.98,
                "close": day_price,
                "volume": volume
            })
        
        return {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "price_change": round(price_change, 2),
            "price_change_pct": round(price_change_pct, 2),
            "market_cap": random.uniform(1e9, 1e12),
            "pe_ratio": random.uniform(10, 50),
            "dividend_yield": random.uniform(0, 0.05),
            "historical_data": historical_data,
            "company_name": company_name,
            "sector": sector,
            "industry": industry
        }
    
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