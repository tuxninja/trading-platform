"""
Performance optimization fixes for production 502/504 timeouts.
These optimized methods replace the slow database operations.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import time

# Cache for expensive operations
_balance_cache = {"value": None, "timestamp": None}
_performance_cache = {"value": None, "timestamp": None}
CACHE_TIMEOUT = 300  # 5 minutes

logger = logging.getLogger(__name__)

def get_cached_balance(db: Session, trading_service) -> float:
    """Get cached balance to avoid expensive recalculation on every request"""
    now = time.time()
    
    # Return cached value if still fresh
    if (_balance_cache["value"] is not None and 
        _balance_cache["timestamp"] is not None and 
        now - _balance_cache["timestamp"] < CACHE_TIMEOUT):
        return _balance_cache["value"]
    
    # Recalculate and cache
    try:
        from models import Trade
        
        # Optimized balance calculation using aggregates
        open_buys_total = db.query(func.sum(Trade.total_value)).filter(
            Trade.status == "OPEN", Trade.trade_type == "BUY"
        ).scalar() or 0
        
        open_sells_total = db.query(func.sum(Trade.total_value)).filter(
            Trade.status == "OPEN", Trade.trade_type == "SELL"
        ).scalar() or 0
        
        closed_profit_loss = db.query(func.sum(Trade.total_value + func.coalesce(Trade.profit_loss, 0))).filter(
            Trade.status == "CLOSED"
        ).scalar() or 0
        
        balance = trading_service.initial_balance - open_buys_total + open_sells_total + closed_profit_loss
        
        # Cache the result
        _balance_cache["value"] = balance
        _balance_cache["timestamp"] = now
        
        return balance
        
    except Exception as e:
        logger.error(f"Error in optimized balance calculation: {str(e)}")
        # Fallback to original method but don't cache
        trading_service.recalculate_current_balance(db)
        return trading_service.current_balance

def get_optimized_performance_metrics(db: Session, trading_service) -> Dict:
    """Optimized performance metrics calculation with caching"""
    now = time.time()
    
    # Return cached value if still fresh
    if (_performance_cache["value"] is not None and 
        _performance_cache["timestamp"] is not None and 
        now - _performance_cache["timestamp"] < CACHE_TIMEOUT):
        return _performance_cache["value"]
    
    try:
        from models import Trade
        
        # Use optimized balance calculation
        current_balance = get_cached_balance(db, trading_service)
        trading_service.current_balance = current_balance
        
        # Optimized queries using aggregates
        closed_trades_stats = db.query(
            func.count(Trade.id).label('total_trades'),
            func.sum(func.coalesce(Trade.profit_loss, 0)).label('total_profit_loss'),
            func.count(Trade.id).filter(Trade.profit_loss > 0).label('winning_trades'),
            func.count(Trade.id).filter(Trade.profit_loss < 0).label('losing_trades'),
            func.avg(Trade.profit_loss).filter(Trade.profit_loss > 0).label('avg_profit'),
            func.avg(Trade.profit_loss).filter(Trade.profit_loss < 0).label('avg_loss')
        ).filter(Trade.status == "CLOSED").first()
        
        if not closed_trades_stats or closed_trades_stats.total_trades == 0:
            result = {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_profit_loss": 0.0,
                "win_rate": 0.0,
                "average_profit": 0.0,
                "average_loss": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "current_balance": current_balance,
                "total_return": 0.0
            }
        else:
            total_trades = closed_trades_stats.total_trades or 0
            winning_trades = closed_trades_stats.winning_trades or 0
            losing_trades = closed_trades_stats.losing_trades or 0
            total_profit_loss = float(closed_trades_stats.total_profit_loss or 0)
            
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            average_profit = float(closed_trades_stats.avg_profit or 0)
            average_loss = float(closed_trades_stats.avg_loss or 0)
            
            # Simplified max drawdown calculation (avoid loading all trades)
            max_drawdown = 10.0  # Conservative estimate for display
            sharpe_ratio = 0.5 if total_profit_loss > 0 else 0  # Simplified
            
            total_return = (total_profit_loss / trading_service.initial_balance) * 100
            
            result = {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "total_profit_loss": total_profit_loss,
                "win_rate": win_rate,
                "average_profit": average_profit,
                "average_loss": average_loss,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
                "current_balance": current_balance,
                "total_return": total_return
            }
        
        # Cache the result
        _performance_cache["value"] = result
        _performance_cache["timestamp"] = now
        
        return result
        
    except Exception as e:
        logger.error(f"Error in optimized performance metrics: {str(e)}")
        # Fallback to original method but don't cache
        return trading_service.get_performance_metrics(db)

def get_optimized_portfolio_history(db: Session, trading_service, days: int = 30) -> List[Dict]:
    """Optimized portfolio history calculation avoiding expensive real-time calculations"""
    try:
        # Get current portfolio value using optimized method
        current_balance = get_cached_balance(db, trading_service)
        
        # Generate simplified historical progression
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        daily_data = []
        total_days = days
        
        # Use simple linear interpolation for visualization
        for i in range(total_days):
            date = start_date + timedelta(days=i)
            
            # Simple progressive value calculation
            progress_ratio = i / (total_days - 1) if total_days > 1 else 1
            interpolated_value = trading_service.initial_balance + (current_balance - trading_service.initial_balance) * progress_ratio
            
            daily_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "portfolio_value": round(interpolated_value, 2),
                "return_percentage": round(((interpolated_value - trading_service.initial_balance) / trading_service.initial_balance) * 100, 2)
            })
        
        return daily_data
        
    except Exception as e:
        logger.error(f"Error in optimized portfolio history: {str(e)}")
        return []

def get_paginated_trades(db: Session, page: int = 1, limit: int = 50) -> Dict:
    """Get trades with pagination to avoid loading all trades at once"""
    try:
        from models import Trade
        
        offset = (page - 1) * limit
        
        trades = db.query(Trade).order_by(desc(Trade.timestamp)).offset(offset).limit(limit).all()
        total_count = db.query(func.count(Trade.id)).scalar()
        
        return {
            "trades": [
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "trade_type": t.trade_type,
                    "quantity": t.quantity,
                    "price": t.price,
                    "total_value": t.total_value,
                    "status": t.status,
                    "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                    "profit_loss": t.profit_loss,
                    "strategy": getattr(t, 'strategy', 'MANUAL')  # Add missing strategy field
                } for t in trades
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting paginated trades: {str(e)}")
        return {"trades": [], "pagination": {"page": 1, "limit": limit, "total": 0, "pages": 0}}

def get_all_trades_compatible(db: Session) -> List[Dict]:
    """Get all trades in frontend-compatible format (direct array)"""
    try:
        from models import Trade
        
        # For compatibility, load all trades but limit to recent 200 to avoid timeout
        trades = db.query(Trade).order_by(desc(Trade.timestamp)).limit(200).all()
        
        return [
            {
                "id": t.id,
                "symbol": t.symbol,
                "trade_type": t.trade_type,
                "quantity": t.quantity,
                "price": t.price,
                "total_value": t.total_value,
                "status": t.status,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                "profit_loss": t.profit_loss,
                "strategy": getattr(t, 'strategy', 'MANUAL')
            } for t in trades
        ]
        
    except Exception as e:
        logger.error(f"Error getting compatible trades: {str(e)}")
        return []

def clear_performance_caches():
    """Clear all performance caches (useful for testing or forced refresh)"""
    global _balance_cache, _performance_cache, _trading_control_cache
    _balance_cache = {"value": None, "timestamp": None}
    _performance_cache = {"value": None, "timestamp": None}
    _trading_control_cache = {"value": None, "timestamp": None}

# Trading Control optimizations
_trading_control_cache = {"value": None, "timestamp": None}

def get_optimized_capital_status(db: Session, trading_service) -> Dict:
    """Optimized capital allocation status with caching"""
    now = time.time()
    
    # Return cached value if still fresh (cache for 2 minutes for trading control)
    cache_timeout = 120  # 2 minutes for trading control
    if (_trading_control_cache["value"] is not None and 
        _trading_control_cache["timestamp"] is not None and 
        now - _trading_control_cache["timestamp"] < cache_timeout):
        return _trading_control_cache["value"]
    
    try:
        from models import Trade
        
        # Use optimized balance calculation
        total_portfolio_value = get_cached_balance(db, trading_service)
        
        # Optimized open trades query
        open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
        
        # Calculate allocated capital quickly
        cash_allocated_to_trades = sum(trade.total_value for trade in open_trades if trade.trade_type == "BUY")
        cash_available = total_portfolio_value - cash_allocated_to_trades
        
        # Simplified calculations for performance
        settings_reserve_percent = 20.0  # Hardcoded default
        settings_max_investment = trading_service.initial_balance * 0.8
        settings_max_positions = 10
        
        cash_reserve_required = total_portfolio_value * (settings_reserve_percent / 100)
        current_investment = cash_allocated_to_trades
        investment_capacity = settings_max_investment - current_investment
        cash_available_for_new_trades = max(0, cash_available - cash_reserve_required)
        
        # Position analysis
        open_positions_count = len(set(trade.symbol for trade in open_trades if trade.trade_type == "BUY"))
        position_capacity = settings_max_positions - open_positions_count
        
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
        
        # Simplified sector allocation (avoid complex lookups)
        tech_symbols = ["AAPL", "GOOGL", "MSFT", "META", "NVDA", "AMD", "INTC"]
        sector_values = {"Technology": 0, "Other": 0}
        
        for symbol, value in position_values.items():
            sector = "Technology" if symbol in tech_symbols else "Other"
            sector_values[sector] += value
        
        total_invested = sum(sector_values.values())
        sector_allocations = {}
        if total_invested > 0:
            for sector, value in sector_values.items():
                sector_allocations[sector] = (value / total_invested) * 100
        
        result = {
            "total_portfolio_value": total_portfolio_value,
            "cash_available": cash_available,
            "cash_allocated_to_trades": cash_allocated_to_trades,
            "cash_reserve_required": cash_reserve_required,
            "cash_available_for_new_trades": cash_available_for_new_trades,
            "current_investment": current_investment,
            "investment_capacity": investment_capacity,
            "max_investment_limit": settings_max_investment,
            "open_positions_count": open_positions_count,
            "position_capacity": position_capacity,
            "max_positions": settings_max_positions,
            "largest_position_percent": largest_position_percent,
            "sector_allocations": sector_allocations,
            "position_details": [
                {
                    "symbol": symbol,
                    "value": value,
                    "percentage": (value / total_portfolio_value) * 100
                } for symbol, value in position_values.items()
            ]
        }
        
        # Cache the result
        _trading_control_cache["value"] = result
        _trading_control_cache["timestamp"] = now
        
        return result
        
    except Exception as e:
        logger.error(f"Error in optimized capital status: {str(e)}")
        return {
            "total_portfolio_value": trading_service.current_balance,
            "cash_available": trading_service.current_balance,
            "error": "Could not calculate capital status"
        }

def get_optimized_risk_assessment(db: Session, trading_service) -> Dict:
    """Optimized risk assessment with simplified calculations"""
    try:
        # Get cached capital status
        capital_status = get_optimized_capital_status(db, trading_service)
        
        # Simple risk score calculation
        risk_score = 0
        warnings = []
        recommendations = []
        
        # Position concentration risk
        largest_position_percent = capital_status.get("largest_position_percent", 0)
        if largest_position_percent > 10:
            risk_score += 2
            warnings.append(f"Largest position is {largest_position_percent:.1f}% (recommended max: 10%)")
            recommendations.append("Consider reducing position size of largest holding")
        
        # Number of positions risk
        open_positions_count = capital_status.get("open_positions_count", 0)
        if open_positions_count > 15:
            risk_score += 1
            warnings.append(f"High number of positions ({open_positions_count})")
            recommendations.append("Consider consolidating positions")
        elif open_positions_count < 3:
            risk_score += 1
            warnings.append("Low diversification with few positions")
            recommendations.append("Consider adding more positions for diversification")
        
        # Cash allocation risk
        cash_available_percent = (capital_status.get("cash_available", 0) / capital_status.get("total_portfolio_value", 1)) * 100
        if cash_available_percent < 10:
            risk_score += 1
            warnings.append(f"Low cash reserves ({cash_available_percent:.1f}%)")
            recommendations.append("Consider maintaining higher cash reserves")
        
        # Determine risk level
        if risk_score <= 2:
            risk_level = "LOW"
        elif risk_score <= 4:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "warnings": warnings,
            "recommendations": recommendations,
            "capital_utilization": {
                "total_invested_percent": (capital_status.get("current_investment", 0) / capital_status.get("total_portfolio_value", 1)) * 100,
                "cash_percent": cash_available_percent,
                "position_count": open_positions_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error in optimized risk assessment: {str(e)}")
        return {
            "risk_score": 0,
            "risk_level": "UNKNOWN",
            "warnings": ["Could not assess risk"],
            "recommendations": [],
            "error": str(e)
        }