"""
Trading Control Service - Provides transparency and control for real trading.

This service adds the following capabilities for real trading:
1. Capital allocation tracking and limits
2. Trade signal preview before execution
3. Manual approval workflows
4. Exit strategy management
5. Risk assessment and warnings
6. Real-time notifications
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Trade, SentimentData, StockData
from schemas import (
    TradingControlSettings, CapitalAllocationSettings, ExitStrategySettings,
    TradeSignalPreview, TradeApprovalRequest, CapitalAllocationStatus,
    ExitSignalPreview, TradingNotification, RiskAssessmentResponse,
    TradingModeEnum, StrategySignal
)
from services.data_service import DataService
from config import config


class TradingControlService:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.data_service = DataService()
        
        # In-memory storage for pending signals (in production, use Redis or database)
        self.pending_signals: Dict[str, TradeSignalPreview] = {}
        self.pending_exits: Dict[str, ExitSignalPreview] = {}
        self.notifications: List[TradingNotification] = []
        
        # Default trading control settings
        self.trading_settings = TradingControlSettings(
            trading_mode=TradingModeEnum.SEMI_AUTO,
            capital_allocation=CapitalAllocationSettings(
                max_total_investment=config.INITIAL_BALANCE * 0.8,  # 80% of total
                max_position_size_percent=5.0,  # 5% max per position
                max_positions=10,
                reserve_cash_percent=20.0  # Keep 20% cash
            ),
            exit_strategy=ExitStrategySettings(
                stop_loss_percent=8.0,
                take_profit_percent=15.0,
                max_hold_days=30,
                trailing_stop_percent=5.0
            ),
            require_confirmation=True,
            enable_notifications=True
        )
    
    def get_capital_allocation_status(self, db: Session) -> CapitalAllocationStatus:
        """Get detailed capital allocation status."""
        try:
            # Get current portfolio state
            total_portfolio_value = self._get_portfolio_value(db)
            open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
            
            # Calculate allocated capital
            cash_allocated_to_trades = sum(trade.total_value for trade in open_trades if trade.trade_type == "BUY")
            cash_available = total_portfolio_value - cash_allocated_to_trades
            
            # Calculate reserves and limits
            settings = self.trading_settings.capital_allocation
            cash_reserve_required = total_portfolio_value * (settings.reserve_cash_percent / 100)
            max_investment_limit = settings.max_total_investment
            current_investment = cash_allocated_to_trades
            investment_capacity = max_investment_limit - current_investment
            cash_available_for_new_trades = max(0, cash_available - cash_reserve_required)
            
            # Position analysis
            open_positions_count = len(set(trade.symbol for trade in open_trades if trade.trade_type == "BUY"))
            position_capacity = settings.max_positions - open_positions_count
            
            # Calculate largest position percentage
            position_values = {}
            for trade in open_trades:
                if trade.trade_type == "BUY":
                    if trade.symbol not in position_values:
                        position_values[trade.symbol] = 0
                    position_values[trade.symbol] += trade.total_value
            
            largest_position_percent = 0
            if position_values:
                largest_position_value = max(position_values.values())
                largest_position_percent = (largest_position_value / total_portfolio_value) * 100
            
            # Sector allocation analysis
            sector_allocations = self._calculate_sector_allocations(db, open_trades)
            
            return CapitalAllocationStatus(
                total_portfolio_value=total_portfolio_value,
                cash_available=cash_available,
                cash_allocated_to_trades=cash_allocated_to_trades,
                cash_reserve_required=cash_reserve_required,
                cash_available_for_new_trades=cash_available_for_new_trades,
                max_total_investment_limit=max_investment_limit,
                current_investment_amount=current_investment,
                investment_capacity_remaining=max(0, investment_capacity),
                open_positions_count=open_positions_count,
                max_positions_limit=settings.max_positions,
                position_capacity_remaining=max(0, position_capacity),
                largest_position_percent=largest_position_percent,
                sector_allocations=sector_allocations
            )
            
        except Exception as e:
            self.logger.error(f"Error getting capital allocation status: {str(e)}")
            raise
    
    def preview_trade_signal(self, db: Session, signal: StrategySignal) -> TradeSignalPreview:
        """Preview a trading signal before execution."""
        try:
            signal_id = str(uuid.uuid4())
            
            # Calculate position size based on current settings
            capital_status = self.get_capital_allocation_status(db)
            max_position_value = capital_status.total_portfolio_value * (self.trading_settings.capital_allocation.max_position_size_percent / 100)
            available_cash = capital_status.cash_available_for_new_trades
            
            # Determine quantity
            if signal.action == "BUY":
                position_value = min(max_position_value, available_cash)
                quantity = int(position_value / signal.price)
                estimated_total = quantity * signal.price
            else:  # SELL
                # For sell signals, sell existing position
                existing_trades = db.query(Trade).filter(
                    Trade.symbol == signal.symbol,
                    Trade.status == "OPEN",
                    Trade.trade_type == "BUY"
                ).all()
                quantity = sum(trade.quantity for trade in existing_trades)
                estimated_total = quantity * signal.price
            
            # Risk assessment
            risk_assessment = self._assess_trade_risk(db, signal, quantity, estimated_total)
            
            # Capital impact
            capital_impact = {
                "available_before": capital_status.cash_available_for_new_trades,
                "available_after": capital_status.cash_available_for_new_trades - (estimated_total if signal.action == "BUY" else -estimated_total),
                "reserve_cash_maintained": capital_status.cash_reserve_required,
                "position_size_percent": (estimated_total / capital_status.total_portfolio_value) * 100
            }
            
            preview = TradeSignalPreview(
                signal_id=signal_id,
                symbol=signal.symbol,
                action=signal.action,
                quantity=quantity,
                estimated_price=signal.price,
                estimated_total=estimated_total,
                reasoning=signal.reasoning,
                confidence=signal.confidence,
                sentiment_score=signal.sentiment_score,
                risk_assessment=risk_assessment,
                capital_impact=capital_impact,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=6)  # Signals expire in 6 hours
            )
            
            # Store for approval
            self.pending_signals[signal_id] = preview
            
            # Create notification if enabled
            if self.trading_settings.enable_notifications:
                self._create_notification(
                    type="SIGNAL_GENERATED",
                    title=f"New {signal.action} Signal: {signal.symbol}",
                    message=f"Generated {signal.action} signal for {quantity} shares of {signal.symbol} at ${signal.price:.2f}. Confidence: {signal.confidence:.1%}",
                    symbol=signal.symbol,
                    priority="MEDIUM",
                    action_required=self.trading_settings.require_confirmation
                )
            
            return preview
            
        except Exception as e:
            self.logger.error(f"Error previewing trade signal: {str(e)}")
            raise
    
    def approve_trade_signal(self, approval: TradeApprovalRequest) -> Dict[str, Any]:
        """Approve or reject a pending trade signal."""
        try:
            if approval.signal_id not in self.pending_signals:
                raise ValueError(f"Signal {approval.signal_id} not found or expired")
            
            signal = self.pending_signals[approval.signal_id]
            
            # Check if signal expired
            if datetime.now() > signal.expires_at:
                del self.pending_signals[approval.signal_id]
                raise ValueError(f"Signal {approval.signal_id} has expired")
            
            if approval.approved:
                # Apply any overrides
                final_quantity = approval.override_quantity or signal.quantity
                final_price_limit = approval.override_price_limit or signal.estimated_price
                
                # Create notification
                if self.trading_settings.enable_notifications:
                    self._create_notification(
                        type="TRADE_APPROVED",
                        title=f"Trade Approved: {signal.symbol}",
                        message=f"Approved {signal.action} of {final_quantity} shares of {signal.symbol} at ${final_price_limit:.2f}",
                        symbol=signal.symbol,
                        priority="HIGH"
                    )
                
                result = {
                    "status": "approved",
                    "signal_id": approval.signal_id,
                    "ready_for_execution": True,
                    "final_quantity": final_quantity,
                    "price_limit": final_price_limit,
                    "notes": approval.notes
                }
            else:
                # Create notification for rejection
                if self.trading_settings.enable_notifications:
                    self._create_notification(
                        type="TRADE_REJECTED",
                        title=f"Trade Rejected: {signal.symbol}",
                        message=f"Rejected {signal.action} signal for {signal.symbol}. Reason: {approval.notes or 'User decision'}",
                        symbol=signal.symbol,
                        priority="LOW"
                    )
                
                result = {
                    "status": "rejected",
                    "signal_id": approval.signal_id,
                    "ready_for_execution": False,
                    "notes": approval.notes
                }
            
            # Remove from pending
            del self.pending_signals[approval.signal_id]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error approving trade signal: {str(e)}")
            raise
    
    def get_pending_signals(self) -> List[TradeSignalPreview]:
        """Get all pending trade signals awaiting approval."""
        # Remove expired signals
        current_time = datetime.now()
        expired_ids = [sid for sid, signal in self.pending_signals.items() if current_time > signal.expires_at]
        for sid in expired_ids:
            del self.pending_signals[sid]
        
        return list(self.pending_signals.values())
    
    def assess_portfolio_risk(self, db: Session) -> RiskAssessmentResponse:
        """Provide comprehensive portfolio risk assessment."""
        try:
            capital_status = self.get_capital_allocation_status(db)
            open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
            
            # Calculate risk score (0-10)
            risk_score = 0
            warnings = []
            recommendations = []
            
            # Position concentration risk
            if capital_status.largest_position_percent > 10:
                risk_score += 2
                warnings.append(f"Largest position is {capital_status.largest_position_percent:.1f}% (recommended max: 10%)")
                recommendations.append("Consider reducing position size of largest holding")
            
            # Number of positions risk
            if capital_status.open_positions_count > 15:
                risk_score += 1
                warnings.append(f"High number of positions ({capital_status.open_positions_count})")
                recommendations.append("Consider consolidating positions")
            elif capital_status.open_positions_count < 3:
                risk_score += 1
                warnings.append("Low diversification with few positions")
                recommendations.append("Consider adding more positions for diversification")
            
            # Sector concentration risk
            max_sector_allocation = max(capital_status.sector_allocations.values()) if capital_status.sector_allocations else 0
            if max_sector_allocation > 40:
                risk_score += 2
                max_sector = max(capital_status.sector_allocations, key=capital_status.sector_allocations.get)
                warnings.append(f"{max_sector} sector concentration at {max_sector_allocation:.1f}% (recommended max: 40%)")
                recommendations.append(f"Diversify away from {max_sector} sector")
            
            # Cash allocation risk
            cash_percent = (capital_status.cash_available / capital_status.total_portfolio_value) * 100
            if cash_percent < 5:
                risk_score += 1
                warnings.append(f"Low cash reserves ({cash_percent:.1f}%)")
                recommendations.append("Maintain higher cash reserves for opportunities")
            elif cash_percent > 50:
                risk_score += 1
                warnings.append(f"High cash allocation ({cash_percent:.1f}%) - underinvested")
                recommendations.append("Consider deploying more capital")
            
            # Portfolio metrics
            portfolio_metrics = self._calculate_portfolio_metrics(db, open_trades)
            
            return RiskAssessmentResponse(
                overall_risk_score=min(risk_score, 10),
                warnings=warnings,
                recommendations=recommendations,
                portfolio_metrics=portfolio_metrics,
                position_concentration={
                    "max_position_percent": capital_status.largest_position_percent,
                    "positions_over_5_percent": len([v for v in capital_status.sector_allocations.values() if v > 5])
                },
                sector_concentration=capital_status.sector_allocations,
                volatility_analysis={"portfolio_beta": 1.0}  # Simplified for now
            )
            
        except Exception as e:
            self.logger.error(f"Error assessing portfolio risk: {str(e)}")
            raise
    
    def update_trading_settings(self, new_settings: TradingControlSettings) -> Dict[str, str]:
        """Update trading control settings."""
        try:
            self.trading_settings = new_settings
            
            # Create notification about settings change
            if new_settings.enable_notifications:
                self._create_notification(
                    type="SETTINGS_UPDATED",
                    title="Trading Settings Updated",
                    message=f"Trading mode: {new_settings.trading_mode.value}, Max investment: ${new_settings.capital_allocation.max_total_investment:,.2f}",
                    priority="LOW"
                )
            
            return {"status": "success", "message": "Trading settings updated successfully"}
            
        except Exception as e:
            self.logger.error(f"Error updating trading settings: {str(e)}")
            raise
    
    def get_trading_settings(self) -> TradingControlSettings:
        """Get current trading control settings."""
        return self.trading_settings
    
    def get_notifications(self, unread_only: bool = False) -> List[TradingNotification]:
        """Get trading notifications."""
        if unread_only:
            return [n for n in self.notifications if not n.read]
        return self.notifications
    
    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.read = True
                return True
        return False
    
    # Private helper methods
    
    def _get_portfolio_value(self, db: Session) -> float:
        """Calculate current portfolio value."""
        # This should integrate with existing portfolio calculation logic
        from services.trading_service import TradingService
        trading_service = TradingService()
        portfolio_summary = trading_service.get_portfolio_summary(db)
        return portfolio_summary.get("portfolio_value", config.INITIAL_BALANCE)
    
    def _calculate_sector_allocations(self, db: Session, open_trades: List[Trade]) -> Dict[str, float]:
        """Calculate sector allocation percentages."""
        sector_values = {}
        total_value = 0
        
        # Group by symbol first
        symbol_values = {}
        for trade in open_trades:
            if trade.trade_type == "BUY":
                if trade.symbol not in symbol_values:
                    symbol_values[trade.symbol] = 0
                symbol_values[trade.symbol] += trade.total_value
        
        # Get sector for each symbol (simplified - could use real sector data)
        tech_symbols = ["AAPL", "GOOGL", "MSFT", "META", "NVDA", "AMD", "INTC"]
        for symbol, value in symbol_values.items():
            sector = "Technology" if symbol in tech_symbols else "Other"
            if sector not in sector_values:
                sector_values[sector] = 0
            sector_values[sector] += value
            total_value += value
        
        # Convert to percentages
        if total_value > 0:
            return {sector: (value / total_value) * 100 for sector, value in sector_values.items()}
        return {}
    
    def _assess_trade_risk(self, db: Session, signal: StrategySignal, quantity: int, estimated_total: float) -> Dict[str, Any]:
        """Assess risk for a specific trade."""
        capital_status = self.get_capital_allocation_status(db)
        
        # Position size risk
        position_percent = (estimated_total / capital_status.total_portfolio_value) * 100
        max_allowed = self.trading_settings.capital_allocation.max_position_size_percent
        
        risk_level = "LOW"
        if position_percent > max_allowed:
            risk_level = "HIGH"
        elif position_percent > max_allowed * 0.8:
            risk_level = "MEDIUM"
        
        return {
            "risk_level": risk_level,
            "position_size_percent": position_percent,
            "max_allowed_percent": max_allowed,
            "violates_position_limit": position_percent > max_allowed,
            "sentiment_strength": abs(signal.sentiment_score),
            "confidence_level": "HIGH" if signal.confidence > 0.8 else "MEDIUM" if signal.confidence > 0.6 else "LOW"
        }
    
    def _calculate_portfolio_metrics(self, db: Session, open_trades: List[Trade]) -> Dict[str, float]:
        """Calculate basic portfolio performance metrics."""
        # Simplified metrics - could be expanded
        closed_trades = db.query(Trade).filter(Trade.status == "CLOSED").all()
        
        if not closed_trades:
            return {"total_return": 0.0, "win_rate": 0.0, "total_trades": 0}
        
        total_pnl = sum(trade.profit_loss for trade in closed_trades if trade.profit_loss)
        winning_trades = len([t for t in closed_trades if t.profit_loss and t.profit_loss > 0])
        win_rate = (winning_trades / len(closed_trades)) * 100
        
        return {
            "total_return": total_pnl,
            "win_rate": win_rate,
            "total_trades": len(closed_trades),
            "average_trade": total_pnl / len(closed_trades) if closed_trades else 0
        }
    
    def _create_notification(self, type: str, title: str, message: str, symbol: str = None, 
                           priority: str = "MEDIUM", action_required: bool = False) -> None:
        """Create a new notification."""
        notification = TradingNotification(
            id=str(uuid.uuid4()),
            type=type,
            title=title,
            message=message,
            symbol=symbol,
            priority=priority,
            action_required=action_required,
            created_at=datetime.now(),
            read=False
        )
        
        self.notifications.append(notification)
        
        # Keep only last 100 notifications
        if len(self.notifications) > 100:
            self.notifications = self.notifications[-100:]
        
        self.logger.info(f"Created notification: {title}")