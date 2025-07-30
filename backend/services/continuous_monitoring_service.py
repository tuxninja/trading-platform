"""
Continuous Stock Monitoring Service
Provides automated, continuous monitoring for watchlisted stocks with sentiment analysis,
price alerts, and trading signal generation.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import get_db
from models import WatchlistStock, WatchlistAlert, SentimentData, Trade
from services.sentiment_service import SentimentService
from services.data_service import DataService
from services.trading_service import TradingService
from config import config

class ContinuousMonitoringService:
    """Service for continuous monitoring of watchlisted stocks."""
    
    def __init__(self):
        self.sentiment_service = SentimentService()
        self.data_service = DataService()
        self.trading_service = TradingService()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Monitoring configuration
        self.sentiment_refresh_interval = config.SENTIMENT_REFRESH_INTERVAL_MINUTES or 30
        self.price_check_interval = config.PRICE_CHECK_INTERVAL_MINUTES or 5
        self.alert_cooldown_minutes = config.ALERT_COOLDOWN_MINUTES or 60
        
    async def run_continuous_monitoring(self, db: Session) -> Dict:
        """Run continuous monitoring for all active watchlist stocks."""
        try:
            self.logger.info("Starting continuous monitoring cycle...")
            
            # Get all active watchlist stocks
            active_stocks = db.query(WatchlistStock).filter(
                WatchlistStock.is_active == True
            ).all()
            
            if not active_stocks:
                self.logger.info("No active watchlist stocks to monitor")
                return {"message": "No active stocks to monitor", "monitored_count": 0}
            
            monitoring_results = {
                "monitored_count": len(active_stocks),
                "sentiment_updates": 0,
                "price_alerts": 0,
                "trading_signals": 0,
                "errors": []
            }
            
            # Process each stock
            for stock in active_stocks:
                try:
                    result = await self._monitor_stock(db, stock)
                    
                    if result.get("sentiment_updated"):
                        monitoring_results["sentiment_updates"] += 1
                    
                    if result.get("alerts_generated"):
                        monitoring_results["price_alerts"] += result["alerts_generated"]
                    
                    if result.get("trading_signal"):
                        monitoring_results["trading_signals"] += 1
                        
                except Exception as e:
                    error_msg = f"Error monitoring {stock.symbol}: {str(e)}"
                    monitoring_results["errors"].append(error_msg)
                    self.logger.error(error_msg)
            
            self.logger.info(
                f"Continuous monitoring completed: {monitoring_results['monitored_count']} stocks, "
                f"{monitoring_results['sentiment_updates']} sentiment updates, "
                f"{monitoring_results['price_alerts']} alerts, "
                f"{monitoring_results['trading_signals']} signals"
            )
            
            return monitoring_results
            
        except Exception as e:
            self.logger.error(f"Error in continuous monitoring: {str(e)}")
            return {"error": str(e)}
    
    async def _monitor_stock(self, db: Session, stock: WatchlistStock) -> Dict:
        """Monitor a single stock for sentiment changes, price alerts, and trading signals."""
        result = {
            "sentiment_updated": False,
            "alerts_generated": 0,
            "trading_signal": None
        }
        
        try:
            # Check if sentiment analysis is needed
            if stock.sentiment_monitoring and self._should_update_sentiment(db, stock.symbol):
                await self._update_stock_sentiment(db, stock.symbol)
                result["sentiment_updated"] = True
            
            # Get current market data
            market_data = self.data_service.get_market_data(stock.symbol, days=1, db=db)
            
            if "error" not in market_data:
                current_price = market_data["current_price"]
                
                # Check for price alerts
                alerts_generated = self._check_price_alerts(db, stock, current_price)
                result["alerts_generated"] = alerts_generated
                
                # Generate trading signals if auto-trading is enabled
                if stock.auto_trading:
                    trading_signal = await self._generate_trading_signal(db, stock, current_price)
                    result["trading_signal"] = trading_signal
            
            # Update last monitoring timestamp
            stock.last_monitored = datetime.now()
            db.commit()
            
        except Exception as e:
            self.logger.error(f"Error monitoring stock {stock.symbol}: {str(e)}")
            raise
        
        return result
    
    def _should_update_sentiment(self, db: Session, symbol: str) -> bool:
        """Check if sentiment data needs to be updated for a symbol."""
        try:
            latest_sentiment = db.query(SentimentData).filter(
                SentimentData.symbol == symbol
            ).order_by(SentimentData.timestamp.desc()).first()
            
            if not latest_sentiment:
                return True
            
            # Check if sentiment is older than refresh interval
            time_since_update = datetime.now() - latest_sentiment.timestamp
            return time_since_update.total_seconds() > (self.sentiment_refresh_interval * 60)
            
        except Exception as e:
            self.logger.error(f"Error checking sentiment update need for {symbol}: {str(e)}")
            return False
    
    async def _update_stock_sentiment(self, db: Session, symbol: str):
        """Update sentiment analysis for a stock."""
        try:
            self.logger.info(f"Updating sentiment for {symbol}")
            
            # Run sentiment analysis
            result = self.sentiment_service.analyze_sentiment(db, symbol)
            
            if "error" not in result:
                self.logger.info(f"Sentiment updated for {symbol}: {result.get('overall_sentiment', 'N/A')}")
            else:
                self.logger.warning(f"Sentiment analysis failed for {symbol}: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"Error updating sentiment for {symbol}: {str(e)}")
    
    def _check_price_alerts(self, db: Session, stock: WatchlistStock, current_price: float) -> int:
        """Check and generate price alerts for a stock."""
        alerts_generated = 0
        
        try:
            # Get existing alerts for this stock
            existing_alerts = db.query(WatchlistAlert).filter(
                WatchlistAlert.watchlist_stock_id == stock.id
            ).all()
            
            for alert in existing_alerts:
                if not alert.is_active:
                    continue
                
                # Check alert conditions
                alert_triggered = False
                
                if alert.alert_type == "price_above" and current_price > alert.threshold_value:
                    alert_triggered = True
                elif alert.alert_type == "price_below" and current_price < alert.threshold_value:
                    alert_triggered = True
                elif alert.alert_type == "price_change_percent":
                    # Calculate price change percentage
                    if stock.reference_price:
                        price_change_pct = ((current_price - stock.reference_price) / stock.reference_price) * 100
                        if abs(price_change_pct) > alert.threshold_value:
                            alert_triggered = True
                
                if alert_triggered and self._can_trigger_alert(db, alert):
                    self._trigger_alert(db, alert, stock, current_price)
                    alerts_generated += 1
            
            # Update reference price for percentage change calculations
            if not stock.reference_price or self._should_update_reference_price(stock):
                stock.reference_price = current_price
                db.commit()
                
        except Exception as e:
            self.logger.error(f"Error checking price alerts for {stock.symbol}: {str(e)}")
        
        return alerts_generated
    
    def _can_trigger_alert(self, db: Session, alert: WatchlistAlert) -> bool:
        """Check if an alert can be triggered (respects cooldown period)."""
        if not alert.last_triggered:
            return True
        
        time_since_last = datetime.now() - alert.last_triggered
        return time_since_last.total_seconds() > (self.alert_cooldown_minutes * 60)
    
    def _trigger_alert(self, db: Session, alert: WatchlistAlert, stock: WatchlistStock, current_price: float):
        """Trigger a price alert."""
        try:
            alert.last_triggered = datetime.now()
            alert.trigger_count = (alert.trigger_count or 0) + 1
            
            # Log the alert
            self.logger.info(
                f"Price alert triggered for {stock.symbol}: {alert.alert_type} "
                f"threshold {alert.threshold_value}, current price ${current_price:.2f}"
            )
            
            # Could extend this to send notifications, emails, etc.
            
            db.commit()
            
        except Exception as e:
            self.logger.error(f"Error triggering alert for {stock.symbol}: {str(e)}")
    
    def _should_update_reference_price(self, stock: WatchlistStock) -> bool:
        """Check if reference price should be updated (daily reset)."""
        if not stock.reference_price_updated:
            return True
        
        # Update reference price daily
        time_since_update = datetime.now() - stock.reference_price_updated
        return time_since_update.days >= 1
    
    async def _generate_trading_signal(self, db: Session, stock: WatchlistStock, current_price: float) -> Optional[Dict]:
        """Generate trading signals based on sentiment and price analysis."""
        try:
            if not stock.auto_trading:
                return None
            
            # Get latest sentiment data
            latest_sentiment = db.query(SentimentData).filter(
                SentimentData.symbol == stock.symbol
            ).order_by(SentimentData.timestamp.desc()).first()
            
            if not latest_sentiment:
                return None
            
            sentiment_score = latest_sentiment.overall_sentiment
            
            # Check if we already have an open position
            open_trades = db.query(Trade).filter(
                and_(
                    Trade.symbol == stock.symbol,
                    Trade.status == "OPEN"
                )
            ).all()
            
            has_open_position = len(open_trades) > 0
            
            # Generate signal based on sentiment and configuration
            signal = None
            
            # Buy signal conditions
            if (sentiment_score > config.BUY_SENTIMENT_THRESHOLD and 
                not has_open_position and 
                self._meets_buy_conditions(stock, current_price)):
                
                position_size = self._calculate_position_size(stock, current_price)
                if position_size > 0:
                    signal = {
                        "action": "BUY",
                        "symbol": stock.symbol,
                        "price": current_price,
                        "quantity": position_size,
                        "confidence": min(abs(sentiment_score) * 2, 1.0),
                        "reasoning": f"Positive sentiment ({sentiment_score:.3f}) above buy threshold",
                        "sentiment_score": sentiment_score
                    }
            
            # Sell signal conditions
            elif (sentiment_score < config.SELL_SENTIMENT_THRESHOLD and 
                  has_open_position and 
                  self._meets_sell_conditions(stock, current_price)):
                
                total_position = sum(trade.quantity for trade in open_trades if trade.trade_type == "BUY")
                if total_position > 0:
                    signal = {
                        "action": "SELL",
                        "symbol": stock.symbol,
                        "price": current_price,
                        "quantity": total_position,
                        "confidence": min(abs(sentiment_score) * 2, 1.0),
                        "reasoning": f"Negative sentiment ({sentiment_score:.3f}) below sell threshold",
                        "sentiment_score": sentiment_score
                    }
            
            if signal:
                self.logger.info(f"Trading signal generated for {stock.symbol}: {signal['action']} {signal['quantity']} shares")
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error generating trading signal for {stock.symbol}: {str(e)}")
            return None
    
    def _meets_buy_conditions(self, stock: WatchlistStock, current_price: float) -> bool:
        """Check if buy conditions are met based on stock preferences."""
        # Check maximum position size
        if stock.max_position_size:
            position_value = self._calculate_position_size(stock, current_price) * current_price
            if position_value > stock.max_position_size:
                return False
        
        # Add more sophisticated buy conditions based on risk tolerance
        if stock.risk_tolerance == "conservative":
            # More stringent conditions for conservative approach
            return True  # Simplified for now
        
        return True
    
    def _meets_sell_conditions(self, stock: WatchlistStock, current_price: float) -> bool:
        """Check if sell conditions are met based on stock preferences."""
        # Add sophisticated sell conditions
        return True  # Simplified for now
    
    def _calculate_position_size(self, stock: WatchlistStock, current_price: float) -> int:
        """Calculate appropriate position size based on stock preferences and available capital."""
        try:
            # Get current available balance
            available_balance = self.trading_service.current_balance
            
            # Determine position size based on preferences
            max_position_value = stock.max_position_size or (available_balance * config.MAX_POSITION_SIZE)
            
            # Limit position size based on available balance
            position_value = min(max_position_value, available_balance * 0.1)  # Never risk more than 10% per trade
            
            # Calculate quantity
            quantity = int(position_value / current_price)
            
            return max(0, quantity)  # Ensure non-negative
            
        except Exception as e:
            self.logger.error(f"Error calculating position size for {stock.symbol}: {str(e)}")
            return 0
    
    def get_monitoring_status(self, db: Session) -> Dict:
        """Get current monitoring status for all watchlist stocks."""
        try:
            active_stocks = db.query(WatchlistStock).filter(
                WatchlistStock.is_active == True
            ).all()
            
            status = {
                "total_active_stocks": len(active_stocks),
                "sentiment_monitoring_enabled": len([s for s in active_stocks if s.sentiment_monitoring]),
                "auto_trading_enabled": len([s for s in active_stocks if s.auto_trading]),
                "last_monitoring_cycle": None,
                "stocks": []
            }
            
            for stock in active_stocks:
                # Get latest sentiment
                latest_sentiment = db.query(SentimentData).filter(
                    SentimentData.symbol == stock.symbol
                ).order_by(SentimentData.timestamp.desc()).first()
                
                stock_status = {
                    "symbol": stock.symbol,
                    "company_name": stock.company_name,
                    "is_active": stock.is_active,
                    "sentiment_monitoring": stock.sentiment_monitoring,
                    "auto_trading": stock.auto_trading,
                    "last_monitored": stock.last_monitored.isoformat() if stock.last_monitored else None,
                    "latest_sentiment": latest_sentiment.overall_sentiment if latest_sentiment else None,
                    "sentiment_age_minutes": None
                }
                
                if latest_sentiment:
                    age = datetime.now() - latest_sentiment.timestamp
                    stock_status["sentiment_age_minutes"] = int(age.total_seconds() / 60)
                
                status["stocks"].append(stock_status)
            
            # Find most recent monitoring time
            if active_stocks:
                latest_monitored = max([s.last_monitored for s in active_stocks if s.last_monitored], default=None)
                if latest_monitored:
                    status["last_monitoring_cycle"] = latest_monitored.isoformat()
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting monitoring status: {str(e)}")
            return {"error": str(e)}

# Global monitoring service instance
continuous_monitoring_service = ContinuousMonitoringService()