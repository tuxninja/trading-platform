"""
Position Management Service for automated trading strategy execution.
Handles position opening, monitoring, and automated closing based on exit conditions.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import (
    Position, Strategy, PositionExitEvent, Trade, StockData,
    PositionStatus, ExitConditionType, StrategyType
)
from schemas import TradeCreate
# Avoid circular import - import TradingService when needed
from services.data_service import DataService
from exceptions import TradingAppException
from config import config
import yfinance as yf

class PositionManager:
    """Manages trading positions with automated exit strategies."""
    
    def __init__(self):
        self.data_service = DataService()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._trading_service = None
    
    def open_position(self, db: Session, strategy_id: int, symbol: str, 
                     quantity: int, entry_signal: Dict) -> Position:
        """Open a new position for a strategy."""
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise TradingAppException(f"Strategy {strategy_id} not found")
            
            # Get current market price
            market_data = self.data_service.get_market_data(symbol, days=1)
            current_price = market_data.get('current_price', 0)
            
            if current_price <= 0:
                raise TradingAppException(f"Invalid price for {symbol}: {current_price}")
            
            # Calculate position size
            position_size = quantity * current_price
            
            # Check if strategy has enough allocated capital
            available_capital = self._get_available_capital(db, strategy_id)
            if position_size > available_capital:
                raise TradingAppException(
                    f"Insufficient capital. Need ${position_size:.2f}, have ${available_capital:.2f}"
                )
            
            # Create the position
            position = Position(
                strategy_id=strategy_id,
                symbol=symbol,
                entry_price=current_price,
                quantity=quantity,
                position_size=position_size,
                status=PositionStatus.OPEN.value,
                entry_signal=entry_signal,
                sentiment_at_entry=entry_signal.get('sentiment_score'),
                market_conditions=entry_signal.get('market_conditions')
            )
            
            # Set exit conditions based on strategy parameters
            self._set_exit_conditions(position, strategy, entry_signal)
            
            db.add(position)
            db.flush()  # Get the position ID
            
            # Create corresponding trade record (avoid circular import)
            if not self._trading_service:
                from services.trading_service import TradingService
                self._trading_service = TradingService()
            
            trade_data = TradeCreate(
                symbol=symbol,
                trade_type="BUY",
                quantity=quantity,
                price=current_price,
                strategy=strategy.strategy_type
            )
            
            trade = self._trading_service.create_trade(db, trade_data)
            position.trades.append(trade)
            
            db.commit()
            db.refresh(position)
            
            self.logger.info(
                f"Opened position: {symbol} x{quantity} @ ${current_price:.2f} "
                f"for strategy {strategy.name}"
            )
            
            return position
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error opening position: {str(e)}")
            raise
    
    def close_position(self, db: Session, position_id: int, 
                      exit_type: ExitConditionType, reason: str = "",
                      partial_quantity: Optional[int] = None) -> PositionExitEvent:
        """Close a position (fully or partially) and record the exit event."""
        try:
            position = db.query(Position).filter(Position.id == position_id).first()
            if not position:
                raise TradingAppException(f"Position {position_id} not found")
            
            if position.status != PositionStatus.OPEN.value:
                raise TradingAppException(f"Position {position_id} is not open")
            
            # Get current market price
            market_data = self.data_service.get_market_data(position.symbol, days=1)
            current_price = market_data.get('current_price', position.entry_price)
            
            # Determine quantity to close
            quantity_to_close = partial_quantity or position.quantity
            if quantity_to_close > position.quantity:
                quantity_to_close = position.quantity
            
            # Calculate P&L
            realized_pnl = (current_price - position.entry_price) * quantity_to_close
            
            # Create exit event
            exit_event = PositionExitEvent(
                position_id=position_id,
                exit_type=exit_type.value,
                trigger_price=current_price,
                quantity_closed=quantity_to_close,
                exit_price=current_price,
                realized_pnl=realized_pnl,
                reason=reason
            )
            
            db.add(exit_event)
            
            # Update position
            if quantity_to_close == position.quantity:
                # Full close
                position.status = PositionStatus.CLOSED.value
                position.exit_timestamp = datetime.now()
                position.exit_price = current_price
                position.realized_pnl = realized_pnl
                position.quantity = 0
            else:
                # Partial close
                position.status = PositionStatus.PARTIALLY_CLOSED.value
                position.quantity -= quantity_to_close
                position.realized_pnl = (position.realized_pnl or 0) + realized_pnl
            
            # Create corresponding trade record (avoid circular import)
            if not self._trading_service:
                from services.trading_service import TradingService
                self._trading_service = TradingService()
            
            trade_data = TradeCreate(
                symbol=position.symbol,
                trade_type="SELL",
                quantity=quantity_to_close,
                price=current_price,
                strategy=position.strategy.strategy_type
            )
            
            trade = self._trading_service.create_trade(db, trade_data)
            position.trades.append(trade)
            
            db.commit()
            db.refresh(exit_event)
            
            self.logger.info(
                f"Closed position: {position.symbol} x{quantity_to_close} @ ${current_price:.2f} "
                f"P&L: ${realized_pnl:.2f} ({exit_type.value})"
            )
            
            return exit_event
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error closing position: {str(e)}")
            raise
    
    def check_exit_conditions(self, db: Session) -> List[Dict]:
        """Check all open positions for exit conditions and close if triggered."""
        exit_events = []
        
        try:
            # Get all open positions
            open_positions = db.query(Position).filter(
                Position.status == PositionStatus.OPEN.value
            ).all()
            
            for position in open_positions:
                try:
                    exit_condition = self._evaluate_exit_conditions(db, position)
                    if exit_condition:
                        exit_event = self.close_position(
                            db, position.id, 
                            exit_condition['type'], 
                            exit_condition['reason']
                        )
                        exit_events.append({
                            'position_id': position.id,
                            'symbol': position.symbol,
                            'exit_type': exit_condition['type'].value,
                            'exit_price': exit_event.exit_price,
                            'pnl': exit_event.realized_pnl,
                            'reason': exit_condition['reason']
                        })
                        
                except Exception as e:
                    self.logger.error(f"Error checking position {position.id}: {str(e)}")
                    continue
            
            if exit_events:
                self.logger.info(f"Processed {len(exit_events)} position exits")
            
            return exit_events
            
        except Exception as e:
            self.logger.error(f"Error checking exit conditions: {str(e)}")
            return exit_events
    
    def update_unrealized_pnl(self, db: Session) -> None:
        """Update unrealized P&L for all open positions."""
        try:
            open_positions = db.query(Position).filter(
                Position.status == PositionStatus.OPEN.value
            ).all()
            
            for position in open_positions:
                try:
                    # Get current price
                    market_data = self.data_service.get_market_data(position.symbol, days=1)
                    current_price = market_data.get('current_price', position.entry_price)
                    
                    # Calculate unrealized P&L
                    unrealized_pnl = (current_price - position.entry_price) * position.quantity
                    position.unrealized_pnl = unrealized_pnl
                    
                    # Update trailing stop if configured
                    if position.trailing_stop_percentage:
                        self._update_trailing_stop(position, current_price)
                    
                except Exception as e:
                    self.logger.error(f"Error updating P&L for position {position.id}: {str(e)}")
                    continue
            
            db.commit()
            
        except Exception as e:
            self.logger.error(f"Error updating unrealized P&L: {str(e)}")
            db.rollback()
    
    def get_position_summary(self, db: Session, strategy_id: Optional[int] = None) -> Dict:
        """Get summary of positions for a strategy or all strategies."""
        try:
            query = db.query(Position)
            if strategy_id:
                query = query.filter(Position.strategy_id == strategy_id)
            
            positions = query.all()
            
            summary = {
                'total_positions': len(positions),
                'open_positions': len([p for p in positions if p.status == PositionStatus.OPEN.value]),
                'closed_positions': len([p for p in positions if p.status == PositionStatus.CLOSED.value]),
                'total_invested': sum(p.position_size for p in positions if p.status == PositionStatus.OPEN.value),
                'total_unrealized_pnl': sum(p.unrealized_pnl or 0 for p in positions if p.status == PositionStatus.OPEN.value),
                'total_realized_pnl': sum(p.realized_pnl or 0 for p in positions if p.status == PositionStatus.CLOSED.value),
                'positions': []
            }
            
            for position in positions:
                summary['positions'].append({
                    'id': position.id,
                    'symbol': position.symbol,
                    'strategy': position.strategy.name,
                    'entry_price': position.entry_price,
                    'current_price': self._get_current_price(position.symbol),
                    'quantity': position.quantity,
                    'status': position.status,
                    'unrealized_pnl': position.unrealized_pnl,
                    'realized_pnl': position.realized_pnl,
                    'entry_timestamp': position.entry_timestamp,
                    'exit_timestamp': position.exit_timestamp
                })
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting position summary: {str(e)}")
            return {'error': str(e)}
    
    def _set_exit_conditions(self, position: Position, strategy: Strategy, entry_signal: Dict) -> None:
        """Set exit conditions based on strategy parameters."""
        params = strategy.parameters or {}
        
        # Stop loss
        stop_loss_pct = params.get('stop_loss_percentage', 0.05)  # 5% default
        if stop_loss_pct > 0:
            position.stop_loss_price = position.entry_price * (1 - stop_loss_pct)
        
        # Take profit
        take_profit_pct = params.get('take_profit_percentage', 0.15)  # 15% default
        if take_profit_pct > 0:
            position.take_profit_price = position.entry_price * (1 + take_profit_pct)
        
        # Max hold time
        max_hold_hours = params.get('max_hold_hours', 168)  # 1 week default
        if max_hold_hours > 0:
            position.max_hold_time = max_hold_hours
        
        # Trailing stop
        trailing_stop_pct = params.get('trailing_stop_percentage')
        if trailing_stop_pct and trailing_stop_pct > 0:
            position.trailing_stop_percentage = trailing_stop_pct
    
    def _evaluate_exit_conditions(self, db: Session, position: Position) -> Optional[Dict]:
        """Evaluate if any exit conditions are met for a position."""
        try:
            # Get current price
            market_data = self.data_service.get_market_data(position.symbol, days=1)
            current_price = market_data.get('current_price', position.entry_price)
            
            # Check stop loss
            if position.stop_loss_price and current_price <= position.stop_loss_price:
                return {
                    'type': ExitConditionType.STOP_LOSS,
                    'reason': f"Stop loss triggered at ${current_price:.2f} (target: ${position.stop_loss_price:.2f})"
                }
            
            # Check take profit
            if position.take_profit_price and current_price >= position.take_profit_price:
                return {
                    'type': ExitConditionType.TAKE_PROFIT,
                    'reason': f"Take profit triggered at ${current_price:.2f} (target: ${position.take_profit_price:.2f})"
                }
            
            # Check time-based exit
            if position.max_hold_time:
                hours_held = (datetime.now() - position.entry_timestamp).total_seconds() / 3600
                if hours_held >= position.max_hold_time:
                    return {
                        'type': ExitConditionType.TIME_BASED,
                        'reason': f"Max hold time reached ({hours_held:.1f} hours)"
                    }
            
            # Check trailing stop
            if position.trailing_stop_percentage and position.stop_loss_price:
                # Trailing stop logic is handled in update_unrealized_pnl
                if current_price <= position.stop_loss_price:
                    return {
                        'type': ExitConditionType.TRAILING_STOP,
                        'reason': f"Trailing stop triggered at ${current_price:.2f}"
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error evaluating exit conditions for position {position.id}: {str(e)}")
            return None
    
    def _update_trailing_stop(self, position: Position, current_price: float) -> None:
        """Update trailing stop loss price."""
        if not position.trailing_stop_percentage:
            return
        
        # Calculate new trailing stop
        new_stop_price = current_price * (1 - position.trailing_stop_percentage)
        
        # Only update if the new stop is higher (for long positions)
        if not position.stop_loss_price or new_stop_price > position.stop_loss_price:
            position.stop_loss_price = new_stop_price
    
    def _get_available_capital(self, db: Session, strategy_id: int) -> float:
        """Calculate available capital for a strategy."""
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                return 0.0
            
            # Calculate allocated capital based on percentage
            total_balance = config.INITIAL_BALANCE  # This should be updated to current balance
            allocated_capital = total_balance * (strategy.allocation_percentage / 100.0)
            
            # Calculate used capital (sum of open positions)
            open_positions = db.query(Position).filter(
                and_(
                    Position.strategy_id == strategy_id,
                    Position.status == PositionStatus.OPEN.value
                )
            ).all()
            
            used_capital = sum(p.position_size for p in open_positions)
            
            return max(0.0, allocated_capital - used_capital)
            
        except Exception as e:
            self.logger.error(f"Error calculating available capital: {str(e)}")
            return 0.0
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        try:
            market_data = self.data_service.get_market_data(symbol, days=1)
            return market_data.get('current_price', 0.0)
        except:
            return 0.0