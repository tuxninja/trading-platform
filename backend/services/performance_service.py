"""
Performance Service for strategy comparison and optimization.
Handles performance metrics calculation, comparison, and reporting.
"""
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from models import (
    Strategy, Position, StrategyPerformance, PositionExitEvent,
    PositionStatus, ExitConditionType
)
from config import config

class PerformanceService:
    """Service for strategy performance analysis and comparison."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def calculate_strategy_metrics(self, db: Session, strategy_id: int, 
                                 days: int = 30) -> Dict:
        """Calculate comprehensive performance metrics for a strategy."""
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                return {'error': f'Strategy {strategy_id} not found'}
            
            # Get positions for the time period
            cutoff_date = datetime.now() - timedelta(days=days)
            positions = db.query(Position).filter(
                and_(
                    Position.strategy_id == strategy_id,
                    Position.entry_timestamp >= cutoff_date
                )
            ).all()
            
            if not positions:
                return self._empty_metrics(strategy.name)
            
            # Basic counts
            total_positions = len(positions)
            open_positions = len([p for p in positions if p.status == PositionStatus.OPEN.value])
            closed_positions = len([p for p in positions if p.status == PositionStatus.CLOSED.value])
            
            # Closed positions analysis
            closed_pos = [p for p in positions if p.status == PositionStatus.CLOSED.value and p.realized_pnl is not None]
            winning_positions = len([p for p in closed_pos if p.realized_pnl > 0])
            losing_positions = len([p for p in closed_pos if p.realized_pnl < 0])
            
            # P&L calculations
            total_realized_pnl = sum(p.realized_pnl or 0 for p in closed_pos)
            total_unrealized_pnl = sum(p.unrealized_pnl or 0 for p in positions if p.status == PositionStatus.OPEN.value)
            total_pnl = total_realized_pnl + total_unrealized_pnl
            
            # Win/Loss analysis
            wins = [p.realized_pnl for p in closed_pos if p.realized_pnl > 0]
            losses = [abs(p.realized_pnl) for p in closed_pos if p.realized_pnl < 0]
            
            win_rate = (winning_positions / closed_positions * 100) if closed_positions > 0 else 0
            avg_win = sum(wins) / len(wins) if wins else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            profit_factor = sum(wins) / sum(losses) if losses else float('inf') if wins else 0
            
            # Risk metrics
            max_drawdown = self._calculate_max_drawdown(positions)
            sharpe_ratio = self._calculate_sharpe_ratio(positions)
            sortino_ratio = self._calculate_sortino_ratio(positions)
            
            # Time-based metrics
            avg_hold_time = self._calculate_avg_hold_time(closed_pos)
            
            # Capital efficiency
            allocated_capital = config.INITIAL_BALANCE * (strategy.allocation_percentage / 100.0)
            utilized_capital = sum(p.position_size for p in positions if p.status == PositionStatus.OPEN.value)
            capital_efficiency = (utilized_capital / allocated_capital * 100) if allocated_capital > 0 else 0
            
            # Return calculations
            roi_percentage = (total_pnl / allocated_capital * 100) if allocated_capital > 0 else 0
            daily_return = roi_percentage / days if days > 0 else 0
            annualized_return = daily_return * 252  # Trading days in a year
            
            return {
                'strategy_name': strategy.name,
                'strategy_type': strategy.strategy_type,
                'period_days': days,
                'total_positions': total_positions,
                'open_positions': open_positions,
                'closed_positions': closed_positions,
                'winning_positions': winning_positions,
                'losing_positions': losing_positions,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'realized_pnl': round(total_realized_pnl, 2),
                'unrealized_pnl': round(total_unrealized_pnl, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'profit_factor': round(profit_factor, 2),
                'max_drawdown': round(max_drawdown, 2),
                'sharpe_ratio': round(sharpe_ratio, 3) if sharpe_ratio else None,
                'sortino_ratio': round(sortino_ratio, 3) if sortino_ratio else None,
                'avg_hold_time_hours': round(avg_hold_time, 1),
                'allocated_capital': round(allocated_capital, 2),
                'utilized_capital': round(utilized_capital, 2),
                'available_capital': round(allocated_capital - utilized_capital, 2),
                'capital_efficiency': round(capital_efficiency, 1),
                'roi_percentage': round(roi_percentage, 2),
                'daily_return': round(daily_return, 3),
                'annualized_return': round(annualized_return, 1)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating strategy metrics: {str(e)}")
            return {'error': str(e)}
    
    def compare_strategies(self, db: Session, strategy_ids: List[int], 
                          days: int = 30) -> Dict:
        """Compare performance metrics across multiple strategies."""
        try:
            comparisons = []
            
            for strategy_id in strategy_ids:
                metrics = self.calculate_strategy_metrics(db, strategy_id, days)
                if 'error' not in metrics:
                    comparisons.append(metrics)
            
            if not comparisons:
                return {'error': 'No valid strategies to compare'}
            
            # Calculate rankings
            rankings = self._calculate_rankings(comparisons)
            
            # Summary statistics
            summary = {
                'total_strategies': len(comparisons),
                'period_days': days,
                'combined_pnl': sum(c['total_pnl'] for c in comparisons),
                'avg_win_rate': sum(c['win_rate'] for c in comparisons) / len(comparisons),
                'best_performer': max(comparisons, key=lambda x: x['total_pnl'])['strategy_name'],
                'worst_performer': min(comparisons, key=lambda x: x['total_pnl'])['strategy_name'],
                'most_active': max(comparisons, key=lambda x: x['total_positions'])['strategy_name'],
                'highest_win_rate': max(comparisons, key=lambda x: x['win_rate'])['strategy_name']
            }
            
            return {
                'summary': summary,
                'comparisons': comparisons,
                'rankings': rankings
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing strategies: {str(e)}")
            return {'error': str(e)}
    
    def get_portfolio_performance(self, db: Session, days: int = 30) -> Dict:
        """Get overall portfolio performance across all strategies."""
        try:
            # Get all active strategies
            strategies = db.query(Strategy).filter(Strategy.is_active == True).all()
            
            if not strategies:
                return {'error': 'No active strategies found'}
            
            strategy_ids = [s.id for s in strategies]
            comparison = self.compare_strategies(db, strategy_ids, days)
            
            if 'error' in comparison:
                return comparison
            
            # Portfolio-level calculations
            total_allocated = sum(
                config.INITIAL_BALANCE * (s.allocation_percentage / 100.0) 
                for s in strategies
            )
            total_utilized = sum(c['utilized_capital'] for c in comparison['comparisons'])
            total_available = total_allocated - total_utilized
            
            portfolio_roi = (comparison['summary']['combined_pnl'] / total_allocated * 100) if total_allocated > 0 else 0
            
            portfolio_metrics = {
                'total_strategies': len(strategies),
                'active_strategies': len([s for s in strategies if s.is_active]),
                'total_allocated_capital': round(total_allocated, 2),
                'total_utilized_capital': round(total_utilized, 2),
                'total_available_capital': round(total_available, 2),
                'portfolio_utilization': round((total_utilized / total_allocated * 100) if total_allocated > 0 else 0, 1),
                'total_pnl': round(comparison['summary']['combined_pnl'], 2),
                'portfolio_roi': round(portfolio_roi, 2),
                'avg_win_rate': round(comparison['summary']['avg_win_rate'], 2),
                'period_days': days
            }
            
            return {
                'portfolio_metrics': portfolio_metrics,
                'strategy_breakdown': comparison['comparisons'],
                'performance_rankings': comparison['rankings']
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio performance: {str(e)}")
            return {'error': str(e)}
    
    def get_performance_history(self, db: Session, strategy_id: Optional[int] = None, 
                               days: int = 30) -> Dict:
        """Get historical performance data for charting."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if strategy_id:
                # Single strategy history
                performance_records = db.query(StrategyPerformance).filter(
                    and_(
                        StrategyPerformance.strategy_id == strategy_id,
                        StrategyPerformance.date >= cutoff_date
                    )
                ).order_by(StrategyPerformance.date).all()
                
                strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
                strategy_name = strategy.name if strategy else f"Strategy {strategy_id}"
                
                history_data = [{
                    'date': record.date.isoformat(),
                    'total_pnl': record.total_pnl,
                    'realized_pnl': record.realized_pnl,
                    'unrealized_pnl': record.unrealized_pnl,
                    'win_rate': record.win_rate,
                    'total_positions': record.total_positions,
                    'strategy_name': strategy_name
                } for record in performance_records]
                
            else:
                # Portfolio history (all strategies combined)
                performance_records = db.query(StrategyPerformance).filter(
                    StrategyPerformance.date >= cutoff_date
                ).order_by(StrategyPerformance.date).all()
                
                # Group by date and sum across strategies
                date_groups = {}
                for record in performance_records:
                    date_key = record.date.date().isoformat()
                    if date_key not in date_groups:
                        date_groups[date_key] = {
                            'date': date_key,
                            'total_pnl': 0,
                            'realized_pnl': 0,
                            'unrealized_pnl': 0,
                            'total_positions': 0,
                            'winning_positions': 0,
                            'closed_positions': 0
                        }
                    
                    date_groups[date_key]['total_pnl'] += record.total_pnl
                    date_groups[date_key]['realized_pnl'] += record.realized_pnl
                    date_groups[date_key]['unrealized_pnl'] += record.unrealized_pnl
                    date_groups[date_key]['total_positions'] += record.total_positions
                    date_groups[date_key]['winning_positions'] += record.winning_positions
                    date_groups[date_key]['closed_positions'] += record.closed_positions
                
                # Calculate win rates and format
                history_data = []
                for date_key in sorted(date_groups.keys()):
                    data = date_groups[date_key]
                    win_rate = (data['winning_positions'] / data['closed_positions'] * 100) if data['closed_positions'] > 0 else 0
                    data['win_rate'] = round(win_rate, 2)
                    data['strategy_name'] = 'Portfolio'
                    history_data.append(data)
            
            return {
                'period_days': days,
                'data_points': len(history_data),
                'history': history_data
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance history: {str(e)}")
            return {'error': str(e)}
    
    def generate_performance_report(self, db: Session, strategy_id: Optional[int] = None, 
                                   days: int = 30) -> Dict:
        """Generate a comprehensive performance report."""
        try:
            if strategy_id:
                # Single strategy report
                metrics = self.calculate_strategy_metrics(db, strategy_id, days)
                if 'error' in metrics:
                    return metrics
                
                history = self.get_performance_history(db, strategy_id, days)
                
                # Get recent positions for analysis
                recent_positions = self._get_recent_positions(db, strategy_id, days)
                
                return {
                    'report_type': 'strategy',
                    'strategy_id': strategy_id,
                    'generated_at': datetime.now().isoformat(),
                    'metrics': metrics,
                    'history': history,
                    'recent_positions': recent_positions,
                    'recommendations': self._generate_strategy_recommendations(metrics)
                }
            else:
                # Portfolio report
                portfolio_perf = self.get_portfolio_performance(db, days)
                if 'error' in portfolio_perf:
                    return portfolio_perf
                
                history = self.get_performance_history(db, None, days)
                
                return {
                    'report_type': 'portfolio',
                    'generated_at': datetime.now().isoformat(),
                    'portfolio_performance': portfolio_perf,
                    'history': history,
                    'recommendations': self._generate_portfolio_recommendations(portfolio_perf)
                }
                
        except Exception as e:
            self.logger.error(f"Error generating performance report: {str(e)}")
            return {'error': str(e)}
    
    def _empty_metrics(self, strategy_name: str) -> Dict:
        """Return empty metrics structure."""
        return {
            'strategy_name': strategy_name,
            'total_positions': 0,
            'open_positions': 0,
            'closed_positions': 0,
            'winning_positions': 0,
            'losing_positions': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'realized_pnl': 0,
            'unrealized_pnl': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
            'sharpe_ratio': None,
            'roi_percentage': 0
        }
    
    def _calculate_max_drawdown(self, positions: List[Position]) -> float:
        """Calculate maximum drawdown for positions."""
        if not positions:
            return 0.0
        
        # Sort positions by entry timestamp
        sorted_positions = sorted(positions, key=lambda p: p.entry_timestamp)
        
        running_pnl = 0
        peak_pnl = 0
        max_drawdown = 0
        
        for position in sorted_positions:
            pnl = position.realized_pnl or position.unrealized_pnl or 0
            running_pnl += pnl
            
            if running_pnl > peak_pnl:
                peak_pnl = running_pnl
            
            drawdown = peak_pnl - running_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown
    
    def _calculate_sharpe_ratio(self, positions: List[Position]) -> Optional[float]:
        """Calculate Sharpe ratio based on position returns."""
        if not positions:
            return None
        
        returns = []
        for position in positions:
            if position.realized_pnl is not None:
                # Calculate return as percentage of position size
                if position.position_size > 0:
                    returns.append(position.realized_pnl / position.position_size)
        
        if len(returns) < 2:
            return None
        
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return None
        
        # Assuming risk-free rate of 2% annually, daily rate ~0.0001
        risk_free_rate = 0.0001
        return (avg_return - risk_free_rate) / std_dev
    
    def _calculate_sortino_ratio(self, positions: List[Position]) -> Optional[float]:
        """Calculate Sortino ratio (similar to Sharpe but only considers downside deviation)."""
        if not positions:
            return None
        
        returns = []
        for position in positions:
            if position.realized_pnl is not None and position.position_size > 0:
                returns.append(position.realized_pnl / position.position_size)
        
        if len(returns) < 2:
            return None
        
        avg_return = sum(returns) / len(returns)
        negative_returns = [r for r in returns if r < 0]
        
        if not negative_returns:
            return float('inf')
        
        downside_variance = sum(r ** 2 for r in negative_returns) / len(negative_returns)
        downside_deviation = downside_variance ** 0.5
        
        if downside_deviation == 0:
            return None
        
        risk_free_rate = 0.0001
        return (avg_return - risk_free_rate) / downside_deviation
    
    def _calculate_avg_hold_time(self, closed_positions: List[Position]) -> float:
        """Calculate average holding time in hours."""
        if not closed_positions:
            return 0.0
        
        total_hours = 0
        count = 0
        
        for position in closed_positions:
            if position.exit_timestamp:
                hold_time = (position.exit_timestamp - position.entry_timestamp).total_seconds() / 3600
                total_hours += hold_time
                count += 1
        
        return total_hours / count if count > 0 else 0.0
    
    def _calculate_rankings(self, comparisons: List[Dict]) -> Dict:
        """Calculate performance rankings across strategies."""
        if not comparisons:
            return {}
        
        # Sort by various metrics
        by_pnl = sorted(comparisons, key=lambda x: x['total_pnl'], reverse=True)
        by_win_rate = sorted(comparisons, key=lambda x: x['win_rate'], reverse=True)
        by_roi = sorted(comparisons, key=lambda x: x['roi_percentage'], reverse=True)
        by_sharpe = sorted([c for c in comparisons if c['sharpe_ratio']], 
                          key=lambda x: x['sharpe_ratio'], reverse=True)
        
        return {
            'by_total_pnl': [{'rank': i+1, 'strategy': s['strategy_name'], 'value': s['total_pnl']} 
                            for i, s in enumerate(by_pnl)],
            'by_win_rate': [{'rank': i+1, 'strategy': s['strategy_name'], 'value': s['win_rate']} 
                           for i, s in enumerate(by_win_rate)],
            'by_roi': [{'rank': i+1, 'strategy': s['strategy_name'], 'value': s['roi_percentage']} 
                      for i, s in enumerate(by_roi)],
            'by_sharpe_ratio': [{'rank': i+1, 'strategy': s['strategy_name'], 'value': s['sharpe_ratio']} 
                               for i, s in enumerate(by_sharpe)]
        }
    
    def _get_recent_positions(self, db: Session, strategy_id: int, days: int) -> List[Dict]:
        """Get recent positions for a strategy."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        positions = db.query(Position).filter(
            and_(
                Position.strategy_id == strategy_id,
                Position.entry_timestamp >= cutoff_date
            )
        ).order_by(desc(Position.entry_timestamp)).limit(10).all()
        
        return [{
            'symbol': p.symbol,
            'entry_price': p.entry_price,
            'exit_price': p.exit_price,
            'quantity': p.quantity,
            'realized_pnl': p.realized_pnl,
            'unrealized_pnl': p.unrealized_pnl,
            'status': p.status,
            'entry_timestamp': p.entry_timestamp.isoformat(),
            'exit_timestamp': p.exit_timestamp.isoformat() if p.exit_timestamp else None
        } for p in positions]
    
    def _generate_strategy_recommendations(self, metrics: Dict) -> List[str]:
        """Generate recommendations based on strategy performance."""
        recommendations = []
        
        if metrics['win_rate'] < 40:
            recommendations.append("Consider tightening entry criteria - win rate is below 40%")
        
        if metrics['profit_factor'] < 1.2:
            recommendations.append("Review exit conditions - profit factor suggests room for improvement")
        
        if metrics['max_drawdown'] > metrics['total_pnl'] * 2:
            recommendations.append("Consider implementing stricter risk management - drawdown is high relative to profits")
        
        if metrics['capital_efficiency'] < 50:
            recommendations.append("Consider increasing position sizes or allocation - capital utilization is low")
        
        if metrics['avg_hold_time_hours'] > 168:  # 1 week
            recommendations.append("Consider shorter holding periods or more aggressive profit-taking")
        
        return recommendations
    
    def _generate_portfolio_recommendations(self, portfolio_perf: Dict) -> List[str]:
        """Generate recommendations for overall portfolio."""
        recommendations = []
        
        portfolio_metrics = portfolio_perf['portfolio_metrics']
        
        if portfolio_metrics['portfolio_utilization'] < 60:
            recommendations.append("Consider increasing strategy allocations - portfolio utilization is low")
        
        if portfolio_metrics['portfolio_roi'] < 0:
            recommendations.append("Review underperforming strategies - overall portfolio is negative")
        
        # Check for strategy concentration
        strategy_breakdown = portfolio_perf['strategy_breakdown']
        max_pnl = max(s['total_pnl'] for s in strategy_breakdown) if strategy_breakdown else 0
        total_pnl = portfolio_metrics['total_pnl']
        
        if max_pnl > abs(total_pnl) * 0.8:
            recommendations.append("Consider diversifying - one strategy dominates portfolio performance")
        
        return recommendations