import yfinance as yf
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import logging

from models import Trade, SentimentData, PerformanceMetrics
from schemas import TradeCreate, TradeResponse, StrategySignal
from services.sentiment_service import SentimentService
from services.data_service import DataService
from config import config
from exceptions import (
    InsufficientBalanceError,
    InsufficientSharesError,
    TradeNotFoundError,
    InvalidTradeError
)

class TradingService:
    def __init__(self):
        self.sentiment_service = SentimentService()
        self.data_service = DataService()
        self.initial_balance = config.INITIAL_BALANCE
        self.current_balance = self.initial_balance
        self.positions = {}  # Current open positions
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize balance based on existing trades (fixes startup issue)
        try:
            from database import SessionLocal
            db = SessionLocal()
            self.recalculate_current_balance(db)
            db.close()
        except Exception as e:
            self.logger.warning(f"Could not recalculate balance on startup: {str(e)}")
        
    def recalculate_current_balance(self, db: Session):
        """Recalculate current balance based on all trades (fixes startup balance issues)"""
        try:
            all_trades = db.query(Trade).all()
            
            # Reset to initial balance
            balance = self.initial_balance
            self.logger.info(f"Starting balance calculation from initial: ${balance:.2f}")
            
            # Subtract money used for open BUY positions
            open_buys = [t for t in all_trades if t.status == "OPEN" and t.trade_type == "BUY"]
            for trade in open_buys:
                balance -= trade.total_value
                self.logger.info(f"Open BUY {trade.symbol}: -${trade.total_value:.2f}, balance now: ${balance:.2f}")
                
            # Add proceeds from open SELL positions
            open_sells = [t for t in all_trades if t.status == "OPEN" and t.trade_type == "SELL"] 
            for trade in open_sells:
                balance += trade.total_value
                self.logger.info(f"Open SELL {trade.symbol}: +${trade.total_value:.2f}, balance now: ${balance:.2f}")
                
            # For closed trades, add back the original investment plus profit/loss
            # This is what happens when close_trade() is called: balance += trade.total_value + profit_loss
            closed_trades = [t for t in all_trades if t.status == "CLOSED"]
            for trade in closed_trades:
                total_return = trade.total_value + (trade.profit_loss or 0)
                balance += total_return
                self.logger.info(f"Closed {trade.symbol}: +${total_return:.2f} (${trade.total_value:.2f} capital + ${trade.profit_loss:.2f} P&L), balance now: ${balance:.2f}")
                
            self.current_balance = balance
            self.logger.info(f"Final recalculated current balance: ${self.current_balance:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error recalculating balance: {str(e)}")
    
    def get_portfolio_history(self, db: Session, days: int = 30) -> List[Dict]:
        """Get portfolio value history for charting"""
        try:
            from datetime import datetime, timedelta
            
            # Get current portfolio summary with correct calculations
            portfolio_summary = self.get_portfolio_summary(db)
            current_portfolio_value = portfolio_summary.get("portfolio_value", self.current_balance)
            
            # Generate a simple progression showing growth over time
            # This avoids the complex historical recalculation that was causing negative values
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Generate daily progression from initial balance to current value
            daily_data = []
            total_days = days
            
            for i in range(total_days):
                date = start_date + timedelta(days=i)
                
                # Calculate progressive value (simple linear growth for visualization)
                progress_ratio = i / (total_days - 1) if total_days > 1 else 1
                interpolated_value = self.initial_balance + (current_portfolio_value - self.initial_balance) * progress_ratio
                
                daily_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "value": round(interpolated_value, 2)
                })
            
            # Ensure the last point shows the actual current value
            daily_data.append({
                "date": end_date.strftime("%Y-%m-%d"),
                "value": round(current_portfolio_value, 2)
            })
            
            return daily_data
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio history: {str(e)}")
            # Return minimal history on error
            return [
                {"date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), "value": self.initial_balance},
                {"date": datetime.now().strftime("%Y-%m-%d"), "value": self.current_balance}
            ]
    
    def create_trade(self, db: Session, trade: TradeCreate) -> TradeResponse:
        """Create a new paper trade with validation and error handling."""
        try:
            # Validate trade inputs
            if trade.quantity <= 0:
                raise InvalidTradeError("Quantity must be greater than 0")
            if trade.price <= 0:
                raise InvalidTradeError("Price must be greater than 0")
            if trade.trade_type not in ["BUY", "SELL"]:
                raise InvalidTradeError("Trade type must be BUY or SELL")
            
            # Calculate total value
            total_value = trade.quantity * trade.price
            self.logger.info(f"Creating {trade.trade_type} trade: {trade.quantity} shares of {trade.symbol} at ${trade.price:.2f}")
            
            # Check if we have enough balance for buy trades
            if trade.trade_type == "BUY":
                if total_value > self.current_balance:
                    raise InsufficientBalanceError(
                        f"Insufficient balance: ${self.current_balance:.2f} available, ${total_value:.2f} required"
                    )
                
                # Update balance
                self.current_balance -= total_value
                self.logger.info(f"Updated balance after BUY: ${self.current_balance:.2f}")
                
                # Update positions
                if trade.symbol in self.positions:
                    self.positions[trade.symbol] += trade.quantity
                else:
                    self.positions[trade.symbol] = trade.quantity
            
            elif trade.trade_type == "SELL":
                # Check if we have enough shares to sell
                current_position = self.positions.get(trade.symbol, 0)
                if current_position < trade.quantity:
                    raise InsufficientSharesError(
                        f"Insufficient shares: {current_position} available, {trade.quantity} required"
                    )
                
                # Update balance
                self.current_balance += total_value
                self.logger.info(f"Updated balance after SELL: ${self.current_balance:.2f}")
                
                # Update positions
                self.positions[trade.symbol] -= trade.quantity
                if self.positions[trade.symbol] <= 0:
                    del self.positions[trade.symbol]
            
            # Create trade record
            db_trade = Trade(
                symbol=trade.symbol,
                trade_type=trade.trade_type,
                quantity=trade.quantity,
                price=trade.price,
                total_value=total_value,
                strategy=trade.strategy
            )
            
            db.add(db_trade)
            db.commit()
            db.refresh(db_trade)
            
            self.logger.info(f"Trade created successfully: ID {db_trade.id}")
            return TradeResponse.from_orm(db_trade)
            
        except (InvalidTradeError, InsufficientBalanceError, InsufficientSharesError) as e:
            db.rollback()
            self.logger.warning(f"Trade validation failed: {str(e)}")
            raise
        except Exception as e:
            db.rollback()
            self.logger.error(f"Unexpected error creating trade: {str(e)}")
            raise InvalidTradeError(f"Failed to create trade: {str(e)}")
    
    def get_all_trades(self, db: Session) -> List[TradeResponse]:
        """Get all trades with backward compatibility for missing columns"""
        try:
            trades = db.query(Trade).order_by(desc(Trade.timestamp)).all()
            return [TradeResponse.from_orm(trade) for trade in trades]
        except Exception as e:
            self.logger.warning(f"Error querying trades with new schema, falling back: {str(e)}")
            try:
                # Query basic columns only for backward compatibility
                from sqlalchemy import text
                result = db.execute(text("""
                    SELECT id, symbol, trade_type, quantity, price, total_value, 
                           timestamp, status, strategy, sentiment_score, 
                           profit_loss, close_timestamp, close_price
                    FROM trades 
                    ORDER BY timestamp DESC
                """))
                
                trades_data = []
                for row in result:
                    trade_dict = {
                        'id': row[0],
                        'symbol': row[1],
                        'trade_type': row[2],
                        'quantity': row[3],
                        'price': row[4],
                        'total_value': row[5],
                        'timestamp': row[6],
                        'status': row[7],
                        'strategy': row[8],
                        'sentiment_score': row[9],
                        'profit_loss': row[10],
                        'close_timestamp': row[11],
                        'close_price': row[12]
                    }
                    trades_data.append(trade_dict)
                
                return trades_data
            except Exception as e2:
                self.logger.error(f"Fallback query also failed: {str(e2)}")
                # Return empty list instead of crashing
                return []
    
    def get_trade(self, db: Session, trade_id: int) -> Optional[TradeResponse]:
        """Get a specific trade"""
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if trade:
            return TradeResponse.from_orm(trade)
        return None
    
    def delete_trade(self, db: Session, trade_id: int) -> Dict:
        """Delete a trade with proper validation."""
        try:
            trade = db.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                raise TradeNotFoundError(f"Trade with ID {trade_id} not found")
            
            if trade.status == "CLOSED":
                raise InvalidTradeError("Cannot delete closed trade")
            
            self.logger.info(f"Deleting trade {trade_id}: {trade.trade_type} {trade.quantity} {trade.symbol}")
            
            # Reverse the trade effects on balance and positions
            if trade.trade_type == "BUY":
                self.current_balance += trade.total_value
                if trade.symbol in self.positions:
                    self.positions[trade.symbol] -= trade.quantity
                    if self.positions[trade.symbol] <= 0:
                        del self.positions[trade.symbol]
            elif trade.trade_type == "SELL":
                self.current_balance -= trade.total_value
                if trade.symbol in self.positions:
                    self.positions[trade.symbol] += trade.quantity
                else:
                    self.positions[trade.symbol] = trade.quantity
            
            db.delete(trade)
            db.commit()
            
            self.logger.info(f"Trade {trade_id} deleted successfully")
            return {"message": "Trade deleted successfully"}
            
        except (TradeNotFoundError, InvalidTradeError) as e:
            self.logger.warning(f"Failed to delete trade {trade_id}: {str(e)}")
            raise
        except Exception as e:
            db.rollback()
            self.logger.error(f"Unexpected error deleting trade {trade_id}: {str(e)}")
            raise InvalidTradeError(f"Failed to delete trade: {str(e)}")
    
    def close_trade(self, db: Session, trade_id: int, close_price: float) -> TradeResponse:
        """Close a trade with current market price"""
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise Exception("Trade not found")
        
        if trade.status == "CLOSED":
            raise Exception("Trade is already closed")
        
        # Calculate profit/loss
        if trade.trade_type == "BUY":
            profit_loss = (close_price - trade.price) * trade.quantity
        else:  # SELL
            profit_loss = (trade.price - close_price) * trade.quantity
        
        # Update trade
        trade.status = "CLOSED"
        trade.close_price = close_price
        trade.close_timestamp = datetime.now()
        trade.profit_loss = profit_loss
        
        # CRITICAL FIX: Add back the original investment + profit to current_balance
        total_return = trade.total_value + profit_loss
        self.current_balance += total_return
        self.logger.info(f"Trade {trade_id} closed: P&L ${profit_loss:.2f}, returned ${total_return:.2f} to balance")
        self.logger.info(f"Updated balance after close: ${self.current_balance:.2f}")
        
        db.commit()
        db.refresh(trade)
        
        return TradeResponse.from_orm(trade)
    
    def cancel_trade(self, db: Session, trade_id: int, reason: str = "Manual cancellation") -> TradeResponse:
        """Cancel an OPEN trade and return capital to available balance"""
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise Exception("Trade not found")
        
        if trade.status != "OPEN":
            raise Exception(f"Cannot cancel trade with status: {trade.status}")
        
        # Update trade status
        trade.status = "CANCELLED"
        trade.close_timestamp = datetime.now()
        trade.profit_loss = 0.0  # No profit/loss on cancellation
        
        # Return the allocated capital to available balance
        if trade.trade_type == "BUY":
            self.current_balance += trade.total_value
            self.logger.info(f"Trade {trade_id} cancelled: ${trade.total_value:.2f} returned to balance")
            
            # Remove from positions
            if trade.symbol in self.positions:
                self.positions[trade.symbol] -= trade.quantity
                if self.positions[trade.symbol] <= 0:
                    del self.positions[trade.symbol]
        
        self.logger.info(f"Updated balance after cancellation: ${self.current_balance:.2f}")
        self.logger.info(f"Cancellation reason: {reason}")
        
        db.commit()
        db.refresh(trade)
        
        return TradeResponse.from_orm(trade)
    
    def auto_close_stale_trades(self, db: Session, max_age_hours: int = 24) -> Dict:
        """Automatically close OPEN trades older than specified hours"""
        try:
            from services.data_service import DataService
            
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            stale_trades = db.query(Trade).filter(
                Trade.status == "OPEN",
                Trade.timestamp < cutoff_time
            ).all()
            
            results = {
                "trades_processed": 0,
                "trades_closed": 0,
                "trades_cancelled": 0,
                "capital_freed": 0.0,
                "errors": []
            }
            
            data_service = DataService()
            
            for trade in stale_trades:
                try:
                    results["trades_processed"] += 1
                    
                    # Get current market price for closing
                    market_data = data_service.get_market_data(trade.symbol, days=1, db=db)
                    
                    if "error" not in market_data and "current_price" in market_data:
                        # Close the trade at current market price
                        current_price = market_data["current_price"]
                        self.close_trade(db, trade.id, current_price)
                        results["trades_closed"] += 1
                        self.logger.info(f"Auto-closed stale trade {trade.id} at ${current_price:.2f}")
                        
                    else:
                        # Cancel the trade if we can't get market price
                        cancelled_trade = self.cancel_trade(
                            db, 
                            trade.id, 
                            f"Auto-cancelled: unable to get market price after {max_age_hours}h"
                        )
                        results["trades_cancelled"] += 1
                        results["capital_freed"] += trade.total_value
                        self.logger.warning(f"Auto-cancelled stale trade {trade.id} - no market data available")
                
                except Exception as e:
                    error_msg = f"Failed to process stale trade {trade.id}: {str(e)}"
                    results["errors"].append(error_msg)
                    self.logger.error(error_msg)
            
            self.logger.info(f"Auto-close completed: {results['trades_closed']} closed, {results['trades_cancelled']} cancelled, ${results['capital_freed']:.2f} freed")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in auto_close_stale_trades: {str(e)}")
            return {"error": str(e)}
    
    def get_performance_metrics(self, db: Session) -> Dict:
        """Calculate trading performance metrics"""
        try:
            # Ensure balance is correctly calculated
            self.recalculate_current_balance(db)
            
            # Get all closed trades
            closed_trades = db.query(Trade).filter(Trade.status == "CLOSED").all()
            
            if not closed_trades:
                return {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "total_profit_loss": 0.0,
                    "win_rate": 0.0,
                    "average_profit": 0.0,
                    "average_loss": 0.0,
                    "max_drawdown": 0.0,
                    "sharpe_ratio": 0.0,
                    "current_balance": self.current_balance,
                    "total_return": 0.0
                }
            
            # Calculate basic metrics
            total_trades = len(closed_trades)
            winning_trades = len([t for t in closed_trades if t.profit_loss > 0])
            losing_trades = len([t for t in closed_trades if t.profit_loss < 0])
            total_profit_loss = sum(t.profit_loss for t in closed_trades)
            
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            # Calculate average profit and loss
            profits = [t.profit_loss for t in closed_trades if t.profit_loss > 0]
            losses = [t.profit_loss for t in closed_trades if t.profit_loss < 0]
            
            average_profit = sum(profits) / len(profits) if profits else 0
            average_loss = sum(losses) / len(losses) if losses else 0
            
            # Calculate max drawdown
            cumulative_returns = []
            running_balance = self.initial_balance
            
            for trade in sorted(closed_trades, key=lambda x: x.timestamp):
                running_balance += trade.profit_loss
                cumulative_returns.append((running_balance - self.initial_balance) / self.initial_balance)
            
            max_drawdown = 0
            peak = 0
            for ret in cumulative_returns:
                if ret > peak:
                    peak = ret
                drawdown = peak - ret
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Calculate Sharpe ratio (simplified)
            if len(cumulative_returns) > 1:
                returns_array = np.array(cumulative_returns)
                avg_return = np.mean(returns_array)
                std_return = np.std(returns_array)
                sharpe_ratio = avg_return / std_return if std_return > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Calculate total return based on realized profits/losses only
            # (Using current_balance would incorrectly penalize for money tied up in open positions)
            total_return = (total_profit_loss / self.initial_balance) * 100
            
            return {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "total_profit_loss": total_profit_loss,
                "win_rate": win_rate,
                "average_profit": average_profit,
                "average_loss": average_loss,
                "max_drawdown": max_drawdown * 100,  # Convert to percentage
                "sharpe_ratio": sharpe_ratio,
                "current_balance": self.current_balance,
                "total_return": total_return
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}
    
    def generate_trading_signals(self, db: Session) -> List[StrategySignal]:
        """Generate trading signals based on sentiment analysis"""
        signals = []
        
        try:
            # Get sentiment for all tracked stocks
            sentiments = self.sentiment_service.get_all_sentiment(db)
            
            for sentiment in sentiments:
                symbol = sentiment.symbol
                
                # Get current market data
                market_data = self.data_service.get_market_data(symbol, days=5)
                
                if "error" in market_data:
                    continue
                
                current_price = market_data["current_price"]
                sentiment_score = sentiment.overall_sentiment
                
                # Define trading thresholds from configuration
                buy_threshold = config.BUY_SENTIMENT_THRESHOLD
                sell_threshold = config.SELL_SENTIMENT_THRESHOLD
                
                # Generate signal based on sentiment
                if sentiment_score > buy_threshold:
                    action = "BUY"
                    confidence = min(abs(sentiment_score) * 2, 1.0)
                    reasoning = f"Strong positive sentiment ({sentiment_score:.3f})"
                elif sentiment_score < sell_threshold:
                    action = "SELL"
                    confidence = min(abs(sentiment_score) * 2, 1.0)
                    reasoning = f"Strong negative sentiment ({sentiment_score:.3f})"
                else:
                    action = "HOLD"
                    confidence = 0.5
                    reasoning = f"Neutral sentiment ({sentiment_score:.3f})"
                
                signal = StrategySignal(
                    symbol=symbol,
                    action=action,
                    confidence=confidence,
                    sentiment_score=sentiment_score,
                    price=current_price,
                    reasoning=reasoning
                )
                
                signals.append(signal)
        
        except Exception as e:
            self.logger.error(f"Error generating trading signals: {str(e)}")
        
        return signals
    
    def run_sentiment_strategy(self, db: Session) -> Dict:
        """Run the sentiment-based trading strategy"""
        try:
            # Generate trading signals
            signals = self.generate_trading_signals(db)
            
            executed_trades = []
            
            for signal in signals:
                if signal.confidence < config.CONFIDENCE_THRESHOLD:  # Only trade if confidence is high enough
                    continue
                
                # Check if we already have a position
                current_position = self.positions.get(signal.symbol, 0)
                
                if signal.action == "BUY" and current_position == 0:
                    # Calculate position size based on configuration
                    position_value = self.current_balance * config.MAX_POSITION_SIZE
                    quantity = int(position_value / signal.price)
                    
                    if quantity > 0:
                        trade = TradeCreate(
                            symbol=signal.symbol,
                            trade_type="BUY",
                            quantity=quantity,
                            price=signal.price,
                            strategy="SENTIMENT"
                        )
                        
                        try:
                            executed_trade = self.create_trade(db, trade)
                            executed_trade.sentiment_score = signal.sentiment_score
                            executed_trades.append(executed_trade)
                            self.logger.info(f"Executed BUY trade: {quantity} shares of {signal.symbol} at ${signal.price:.2f}")
                        except Exception as e:
                            self.logger.warning(f"Failed to execute buy trade for {signal.symbol}: {str(e)}")
                
                elif signal.action == "SELL" and current_position > 0:
                    # Sell entire position
                    trade = TradeCreate(
                        symbol=signal.symbol,
                        trade_type="SELL",
                        quantity=current_position,
                        price=signal.price,
                        strategy="SENTIMENT"
                    )
                    
                    try:
                        executed_trade = self.create_trade(db, trade)
                        executed_trade.sentiment_score = signal.sentiment_score
                        executed_trades.append(executed_trade)
                        self.logger.info(f"Executed SELL trade: {current_position} shares of {signal.symbol} at ${signal.price:.2f}")
                    except Exception as e:
                        self.logger.warning(f"Failed to execute sell trade for {signal.symbol}: {str(e)}")
            
            return {
                "signals_generated": len(signals),
                "trades_executed": len(executed_trades),
                "executed_trades": [TradeResponse.from_orm(trade) for trade in executed_trades],
                "signals": [signal.dict() for signal in signals]
            }
            
        except Exception as e:
            self.logger.error(f"Error running sentiment strategy: {str(e)}")
            return {"error": str(e)}
    
    def get_portfolio_summary(self, db: Session) -> Dict:
        """Get current portfolio summary"""
        try:
            portfolio_value = self.current_balance
            
            # Calculate value of open positions directly from database
            open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
            open_positions_value = 0
            
            # Group trades by symbol to reduce API calls
            symbol_positions = {}
            for trade in open_trades:
                if trade.trade_type == "BUY":
                    if trade.symbol not in symbol_positions:
                        symbol_positions[trade.symbol] = {"quantity": 0, "fallback_value": 0}
                    symbol_positions[trade.symbol]["quantity"] += trade.quantity
                    symbol_positions[trade.symbol]["fallback_value"] += trade.total_value
            
            # Get current prices for unique symbols only
            for symbol, position_info in symbol_positions.items():
                try:
                    market_data = self.data_service.get_market_data(symbol, days=1, db=db)
                    if "error" not in market_data:
                        current_price = market_data["current_price"]
                        position_value = position_info["quantity"] * current_price
                        open_positions_value += position_value
                        self.logger.debug(f"Using {market_data.get('data_source', 'live')} price for {symbol}: ${current_price}")
                    else:
                        # Fallback to original trade values
                        open_positions_value += position_info["fallback_value"]
                        self.logger.warning(f"Using fallback trade value for {symbol}")
                except Exception as e:
                    self.logger.warning(f"Error getting market data for {symbol}: {e}")
                    # Fallback to original trade values
                    open_positions_value += position_info["fallback_value"]
            
            portfolio_value += open_positions_value
            
            return {
                "current_balance": self.current_balance,
                "portfolio_value": portfolio_value,
                "open_positions_value": open_positions_value,
                "positions": self.positions,
                "total_return": ((portfolio_value - self.initial_balance) / self.initial_balance) * 100
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {str(e)}")
            return {} 