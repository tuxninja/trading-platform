"""
Watchlist Service for managing user-curated stock monitoring and trading.
Handles adding/removing stocks, configuring monitoring preferences, and tracking performance.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from models import WatchlistStock, WatchlistAlert, StockData, SentimentData
from services.data_service import DataService
from services.sentiment_service import SentimentService
from exceptions import TradingAppException

class WatchlistService:
    """Service for managing stock watchlist and monitoring preferences"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.data_service = DataService()
        self.sentiment_service = SentimentService()
    
    def add_stock_to_watchlist(self, db: Session, symbol: str, user_email: str, 
                              preferences: Dict = None) -> WatchlistStock:
        """Add a stock to the user's watchlist with monitoring preferences"""
        try:
            # Check if stock already exists in watchlist
            existing = db.query(WatchlistStock).filter(
                WatchlistStock.symbol == symbol.upper(),
                WatchlistStock.added_by == user_email
            ).first()
            
            if existing:
                if existing.is_active:
                    raise TradingAppException(f"{symbol} is already in your active watchlist")
                else:
                    # Reactivate existing stock
                    existing.is_active = True
                    existing.updated_at = datetime.now()
                    db.commit()
                    db.refresh(existing)
                    self.logger.info(f"Reactivated {symbol} in watchlist for {user_email}")
                    return existing
            
            # Get stock information
            market_data = self.data_service.get_market_data(symbol.upper(), db=db)
            if "error" in market_data:
                raise TradingAppException(f"Could not find market data for {symbol}")
            
            # Set default preferences if not provided
            if preferences is None:
                preferences = {}
            
            # Create new watchlist entry
            watchlist_stock = WatchlistStock(
                symbol=symbol.upper(),
                company_name=market_data.get("company_name", f"{symbol.upper()} Inc."),
                sector=market_data.get("sector", "Unknown"),
                industry=market_data.get("industry", "Unknown"),
                
                # User preferences with defaults
                is_active=preferences.get("is_active", True),
                sentiment_monitoring=preferences.get("sentiment_monitoring", True),
                auto_trading=preferences.get("auto_trading", True),
                
                # Trading parameters
                position_size_limit=preferences.get("position_size_limit", 5000.0),
                min_confidence_threshold=preferences.get("min_confidence_threshold", 0.3),
                custom_buy_threshold=preferences.get("custom_buy_threshold"),
                custom_sell_threshold=preferences.get("custom_sell_threshold"),
                
                # Monitoring preferences
                priority_level=preferences.get("priority_level", "NORMAL"),
                news_alerts=preferences.get("news_alerts", True),
                price_alerts=preferences.get("price_alerts", False),
                
                # Metadata
                added_by=user_email,
                added_reason=preferences.get("reason", f"Added {symbol} for monitoring")
            )
            
            db.add(watchlist_stock)
            db.commit()
            db.refresh(watchlist_stock)
            
            # Create welcome alert
            self._create_alert(
                db, watchlist_stock.id, "WATCHLIST_ADDED",
                f"Added {symbol} to Watchlist",
                f"Now monitoring {symbol} ({watchlist_stock.company_name}) for sentiment and trading opportunities.",
                "INFO"
            )
            
            self.logger.info(f"Added {symbol} to watchlist for {user_email}")
            return watchlist_stock
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error adding {symbol} to watchlist: {str(e)}")
            raise TradingAppException(f"Failed to add {symbol} to watchlist: {str(e)}")
    
    def remove_stock_from_watchlist(self, db: Session, symbol: str, user_email: str) -> Dict:
        """Remove a stock from the user's watchlist"""
        try:
            watchlist_stock = db.query(WatchlistStock).filter(
                WatchlistStock.symbol == symbol.upper(),
                WatchlistStock.added_by == user_email,
                WatchlistStock.is_active == True
            ).first()
            
            if not watchlist_stock:
                raise TradingAppException(f"{symbol} not found in your active watchlist")
            
            # Soft delete - deactivate instead of deleting
            watchlist_stock.is_active = False
            watchlist_stock.updated_at = datetime.now()
            
            # Create removal alert
            self._create_alert(
                db, watchlist_stock.id, "WATCHLIST_REMOVED",
                f"Removed {symbol} from Watchlist", 
                f"Stopped monitoring {symbol}. Historical data and performance metrics are preserved.",
                "INFO"
            )
            
            db.commit()
            
            self.logger.info(f"Removed {symbol} from watchlist for {user_email}")
            return {
                "symbol": symbol,
                "message": f"Successfully removed {symbol} from watchlist",
                "total_trades": watchlist_stock.total_trades,
                "total_pnl": watchlist_stock.total_pnl
            }
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error removing {symbol} from watchlist: {str(e)}")
            raise TradingAppException(f"Failed to remove {symbol} from watchlist: {str(e)}")
    
    def get_watchlist(self, db: Session, user_email: str = None, include_inactive: bool = False) -> List[Dict]:
        """Get user's watchlist with current market data and performance"""
        try:
            query = db.query(WatchlistStock)
            
            # Only filter by user if user_email is provided
            if user_email:
                query = query.filter(WatchlistStock.added_by == user_email)
            
            if not include_inactive:
                query = query.filter(WatchlistStock.is_active == True)
            
            watchlist_stocks = query.order_by(desc(WatchlistStock.created_at)).all()
            
            result = []
            for stock in watchlist_stocks:
                # Get current market data
                market_data = self.data_service.get_market_data(stock.symbol, db=db)
                
                # Get latest sentiment
                latest_sentiment = db.query(SentimentData).filter(
                    SentimentData.symbol == stock.symbol
                ).order_by(desc(SentimentData.timestamp)).first()
                
                # Calculate win rate
                win_rate = 0.0
                if stock.total_trades > 0:
                    win_rate = (stock.successful_trades / stock.total_trades) * 100
                
                # Get recent alerts
                recent_alerts = db.query(WatchlistAlert).filter(
                    WatchlistAlert.watchlist_stock_id == stock.id,
                    WatchlistAlert.created_at >= datetime.now() - timedelta(days=7)
                ).count()
                
                stock_data = {
                    "id": stock.id,
                    "symbol": stock.symbol,
                    "company_name": stock.company_name,
                    "sector": stock.sector,
                    "industry": stock.industry,
                    
                    # Current market data
                    "current_price": market_data.get("current_price", 0.0),
                    "price_change": market_data.get("price_change", 0.0),
                    "price_change_pct": market_data.get("price_change_pct", 0.0),
                    "data_source": market_data.get("data_source", "unknown"),
                    
                    # Sentiment data
                    "sentiment_score": latest_sentiment.overall_sentiment if latest_sentiment else None,
                    "sentiment_updated": latest_sentiment.timestamp if latest_sentiment else None,
                    
                    # User preferences - with safe attribute access
                    "is_active": getattr(stock, 'is_active', True),
                    "sentiment_monitoring": getattr(stock, 'sentiment_monitoring', True),
                    "auto_trading": getattr(stock, 'auto_trading', True),
                    "priority_level": getattr(stock, 'priority_level', 'NORMAL'),
                    "position_size_limit": getattr(stock, 'position_size_limit', 5000.0),
                    "min_confidence_threshold": getattr(stock, 'min_confidence_threshold', 0.3),
                    
                    # Performance metrics - with safe attribute access
                    "total_trades": getattr(stock, 'total_trades', 0),
                    "successful_trades": getattr(stock, 'successful_trades', 0),
                    "win_rate": win_rate,
                    "total_pnl": getattr(stock, 'total_pnl', 0.0),
                    "recent_alerts": recent_alerts,
                    
                    # Metadata - with safe attribute access
                    "added_at": getattr(stock, 'created_at', datetime.now()),
                    "updated_at": getattr(stock, 'updated_at', datetime.now()),
                    "last_sentiment_check": getattr(stock, 'last_sentiment_check', None),
                    "last_trade_signal": getattr(stock, 'last_trade_signal', None),
                    
                    # Monitoring fields - with safe attribute access for new fields
                    "last_monitored": getattr(stock, 'last_monitored', None),
                    "reference_price": getattr(stock, 'reference_price', None),
                    "reference_price_updated": getattr(stock, 'reference_price_updated', None),
                    "risk_tolerance": getattr(stock, 'risk_tolerance', 'medium')
                }
                
                result.append(stock_data)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting watchlist for {user_email}: {str(e)}")
            raise TradingAppException(f"Failed to get watchlist: {str(e)}")
    
    def update_stock_preferences(self, db: Session, stock_id: int, user_email: str, 
                                preferences: Dict) -> WatchlistStock:
        """Update monitoring and trading preferences for a watchlist stock"""
        try:
            watchlist_stock = db.query(WatchlistStock).filter(
                WatchlistStock.id == stock_id,
                WatchlistStock.added_by == user_email,
                WatchlistStock.is_active == True
            ).first()
            
            if not watchlist_stock:
                raise TradingAppException("Watchlist stock not found")
            
            # Update preferences
            updates = []
            for key, value in preferences.items():
                if hasattr(watchlist_stock, key):
                    old_value = getattr(watchlist_stock, key)
                    setattr(watchlist_stock, key, value)
                    updates.append(f"{key}: {old_value} → {value}")
            
            watchlist_stock.updated_at = datetime.now()
            
            # Create update alert
            if updates:
                self._create_alert(
                    db, stock_id, "PREFERENCES_UPDATED",
                    f"Updated {watchlist_stock.symbol} Preferences",
                    f"Updated settings: {', '.join(updates[:3])}{'...' if len(updates) > 3 else ''}",
                    "INFO"
                )
            
            db.commit()
            db.refresh(watchlist_stock)
            
            self.logger.info(f"Updated preferences for {watchlist_stock.symbol}")
            return watchlist_stock
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating stock preferences: {str(e)}")
            raise TradingAppException(f"Failed to update preferences: {str(e)}")
    
    def get_active_monitoring_symbols(self, db: Session) -> List[str]:
        """Get list of symbols that should be actively monitored for sentiment"""
        try:
            active_stocks = db.query(WatchlistStock).filter(
                WatchlistStock.is_active == True,
                WatchlistStock.sentiment_monitoring == True
            ).all()
            
            return [stock.symbol for stock in active_stocks]
            
        except Exception as e:
            self.logger.error(f"Error getting active monitoring symbols: {str(e)}")
            return []
    
    def get_auto_trading_symbols(self, db: Session) -> List[Dict]:
        """Get symbols enabled for automated trading with their preferences"""
        try:
            trading_stocks = db.query(WatchlistStock).filter(
                WatchlistStock.is_active == True,
                WatchlistStock.auto_trading == True
            ).all()
            
            result = []
            for stock in trading_stocks:
                result.append({
                    "symbol": stock.symbol,
                    "position_size_limit": stock.position_size_limit,
                    "min_confidence_threshold": stock.min_confidence_threshold,
                    "custom_buy_threshold": stock.custom_buy_threshold,
                    "custom_sell_threshold": stock.custom_sell_threshold,
                    "priority_level": stock.priority_level
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting auto trading symbols: {str(e)}")
            return []
    
    def update_stock_performance(self, db: Session, symbol: str, trade_successful: bool, pnl: float):
        """Update performance metrics after a trade"""
        try:
            watchlist_stock = db.query(WatchlistStock).filter(
                WatchlistStock.symbol == symbol,
                WatchlistStock.is_active == True
            ).first()
            
            if watchlist_stock:
                watchlist_stock.total_trades += 1
                if trade_successful:
                    watchlist_stock.successful_trades += 1
                watchlist_stock.total_pnl += pnl
                watchlist_stock.updated_at = datetime.now()
                
                db.commit()
                self.logger.info(f"Updated performance for {symbol}: PnL {pnl:+.2f}")
                
        except Exception as e:
            self.logger.error(f"Error updating stock performance for {symbol}: {str(e)}")
    
    def _create_alert(self, db: Session, watchlist_stock_id: int, alert_type: str, 
                     title: str, message: str, severity: str = "INFO"):
        """Create an alert for a watchlist stock"""
        try:
            alert = WatchlistAlert(
                watchlist_stock_id=watchlist_stock_id,
                alert_type=alert_type,
                title=title,
                message=message,
                severity=severity
            )
            
            db.add(alert)
            db.commit()
            
        except Exception as e:
            self.logger.error(f"Error creating alert: {str(e)}")
    
    def get_watchlist_alerts(self, db: Session, user_email: str, unread_only: bool = False) -> List[Dict]:
        """Get alerts for user's watchlist stocks"""
        try:
            query = db.query(WatchlistAlert).join(WatchlistStock).filter(
                WatchlistStock.added_by == user_email,
                WatchlistStock.is_active == True
            )
            
            if unread_only:
                query = query.filter(WatchlistAlert.is_read == False)
            
            alerts = query.order_by(desc(WatchlistAlert.created_at)).limit(50).all()
            
            result = []
            for alert in alerts:
                result.append({
                    "id": alert.id,
                    "watchlist_stock_id": alert.watchlist_stock_id,
                    "symbol": alert.watchlist_stock.symbol,
                    "alert_type": alert.alert_type,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity,
                    "is_read": alert.is_read,
                    "is_dismissed": alert.is_dismissed,
                    "requires_action": alert.requires_action,
                    "created_at": alert.created_at,
                    "trigger_value": alert.trigger_value,
                    "threshold_value": alert.threshold_value
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting watchlist alerts: {str(e)}")
            return []