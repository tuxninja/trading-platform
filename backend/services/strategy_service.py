"""
Strategy Service for managing and executing different trading strategies.
Handles strategy creation, execution, and performance tracking.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from models import (
    Strategy, Position, StrategyPerformance, SentimentData,
    StrategyType, PositionStatus
)
from schemas import StrategyCreate, StrategyResponse, StrategyRunRequest
from services.position_manager import PositionManager
from services.sentiment_service import SentimentService
from services.data_service import DataService
from exceptions import TradingAppException
from config import config

class StrategyService:
    """Service for managing trading strategies."""
    
    def __init__(self):
        self.position_manager = PositionManager()
        self.sentiment_service = SentimentService()
        self.data_service = DataService()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create_strategy(self, db: Session, strategy_data: StrategyCreate) -> StrategyResponse:
        """Create a new trading strategy."""
        try:
            # Validate strategy type
            if strategy_data.strategy_type not in [e.value for e in StrategyType]:
                raise TradingAppException(f"Invalid strategy type: {strategy_data.strategy_type}")
            
            # Validate allocation percentage
            if not 0 < strategy_data.allocation_percentage <= 100:
                raise TradingAppException("Allocation percentage must be between 0 and 100")
            
            # Set default parameters based on strategy type
            default_params = self._get_default_parameters(strategy_data.strategy_type)
            params = {**default_params, **strategy_data.parameters}
            
            strategy = Strategy(
                name=strategy_data.name,
                strategy_type=strategy_data.strategy_type,
                description=strategy_data.description,
                parameters=params,
                allocation_percentage=strategy_data.allocation_percentage,
                max_positions=strategy_data.max_positions,
                risk_level=strategy_data.risk_level
            )
            
            db.add(strategy)
            db.commit()
            db.refresh(strategy)
            
            # Create initial performance record
            self._create_performance_record(db, strategy.id)
            
            self.logger.info(f"Created strategy: {strategy.name} ({strategy.strategy_type})")
            return StrategyResponse.from_orm(strategy)
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating strategy: {str(e)}")
            raise
    
    def get_strategies(self, db: Session, active_only: bool = True) -> List[StrategyResponse]:
        """Get all strategies."""
        try:
            query = db.query(Strategy)
            if active_only:
                query = query.filter(Strategy.is_active == True)
            
            strategies = query.all()
            return [StrategyResponse.from_orm(s) for s in strategies]
            
        except Exception as e:
            self.logger.error(f"Error getting strategies: {str(e)}")
            return []
    
    def get_strategy(self, db: Session, strategy_id: int) -> Optional[StrategyResponse]:
        """Get a specific strategy."""
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            return StrategyResponse.from_orm(strategy) if strategy else None
            
        except Exception as e:
            self.logger.error(f"Error getting strategy {strategy_id}: {str(e)}")
            return None
    
    def update_strategy(self, db: Session, strategy_id: int, 
                       update_data: Dict) -> Optional[StrategyResponse]:
        """Update a strategy."""
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise TradingAppException(f"Strategy {strategy_id} not found")
            
            # Update allowed fields
            updatable_fields = [
                'name', 'description', 'parameters', 'allocation_percentage',
                'max_positions', 'risk_level', 'is_active'
            ]
            
            for field, value in update_data.items():
                if field in updatable_fields:
                    setattr(strategy, field, value)
            
            strategy.updated_at = datetime.now()
            
            db.commit()
            db.refresh(strategy)
            
            self.logger.info(f"Updated strategy: {strategy.name}")
            return StrategyResponse.from_orm(strategy)
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating strategy {strategy_id}: {str(e)}")
            raise
    
    def run_strategy(self, db: Session, request: StrategyRunRequest) -> Dict:
        """Execute a trading strategy."""
        try:
            strategy = db.query(Strategy).filter(Strategy.id == request.strategy_id).first()
            if not strategy:
                raise TradingAppException(f"Strategy {request.strategy_id} not found")
            
            if not strategy.is_active:
                raise TradingAppException(f"Strategy {strategy.name} is not active")
            
            self.logger.info(f"Running strategy: {strategy.name}")
            
            # Determine symbols to analyze
            symbols = request.symbols or self.data_service.tracked_stocks
            
            # Execute strategy based on type
            if strategy.strategy_type == StrategyType.SENTIMENT.value:
                return self._run_sentiment_strategy(db, strategy, symbols, request.force_analysis)
            elif strategy.strategy_type == StrategyType.MOMENTUM.value:
                return self._run_momentum_strategy(db, strategy, symbols)
            elif strategy.strategy_type == StrategyType.MEAN_REVERSION.value:
                return self._run_mean_reversion_strategy(db, strategy, symbols)
            elif strategy.strategy_type == StrategyType.BREAKOUT.value:
                return self._run_breakout_strategy(db, strategy, symbols)
            else:
                raise TradingAppException(f"Strategy type {strategy.strategy_type} not implemented")
            
        except Exception as e:
            self.logger.error(f"Error running strategy: {str(e)}")
            raise
    
    def run_all_active_strategies(self, db: Session) -> Dict:
        """Run all active strategies."""
        results = []
        errors = []
        
        try:
            active_strategies = db.query(Strategy).filter(Strategy.is_active == True).all()
            
            for strategy in active_strategies:
                try:
                    request = StrategyRunRequest(strategy_id=strategy.id)
                    result = self.run_strategy(db, request)
                    results.append({
                        'strategy_id': strategy.id,
                        'strategy_name': strategy.name,
                        'result': result
                    })
                except Exception as e:
                    error_msg = f"Strategy {strategy.name} failed: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
            
            return {
                'successful_strategies': len(results),
                'failed_strategies': len(errors),
                'results': results,
                'errors': errors
            }
            
        except Exception as e:
            self.logger.error(f"Error running all strategies: {str(e)}")
            return {'error': str(e)}
    
    def update_strategy_performance(self, db: Session, strategy_id: int) -> None:
        """Update performance metrics for a strategy."""
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                return
            
            # Get all positions for this strategy
            positions = db.query(Position).filter(Position.strategy_id == strategy_id).all()
            
            if not positions:
                return
            
            # Calculate metrics
            total_positions = len(positions)
            open_positions = len([p for p in positions if p.status == PositionStatus.OPEN.value])
            closed_positions = len([p for p in positions if p.status == PositionStatus.CLOSED.value])
            
            closed_pos = [p for p in positions if p.status == PositionStatus.CLOSED.value and p.realized_pnl is not None]
            winning_positions = len([p for p in closed_pos if p.realized_pnl > 0])
            losing_positions = len([p for p in closed_pos if p.realized_pnl < 0])
            
            total_pnl = sum(p.realized_pnl or 0 for p in positions)
            unrealized_pnl = sum(p.unrealized_pnl or 0 for p in positions if p.status == PositionStatus.OPEN.value)
            realized_pnl = sum(p.realized_pnl or 0 for p in closed_pos)
            
            win_rate = (winning_positions / closed_positions * 100) if closed_positions > 0 else 0
            
            wins = [p.realized_pnl for p in closed_pos if p.realized_pnl > 0]
            losses = [abs(p.realized_pnl) for p in closed_pos if p.realized_pnl < 0]
            
            average_win = sum(wins) / len(wins) if wins else 0
            average_loss = sum(losses) / len(losses) if losses else 0
            
            profit_factor = sum(wins) / sum(losses) if losses else 0
            
            # Calculate allocated and utilized capital
            allocated_capital = config.INITIAL_BALANCE * (strategy.allocation_percentage / 100.0)
            utilized_capital = sum(p.position_size for p in positions if p.status == PositionStatus.OPEN.value)
            available_capital = max(0, allocated_capital - utilized_capital)
            
            # Update or create performance record
            perf = db.query(StrategyPerformance).filter(
                and_(
                    StrategyPerformance.strategy_id == strategy_id,
                    func.date(StrategyPerformance.date) == datetime.now().date()
                )
            ).first()
            
            if not perf:
                perf = StrategyPerformance(
                    strategy_id=strategy_id,
                    date=datetime.now()
                )
                db.add(perf)
            
            # Update metrics
            perf.total_positions = total_positions
            perf.open_positions = open_positions
            perf.closed_positions = closed_positions
            perf.winning_positions = winning_positions
            perf.losing_positions = losing_positions
            perf.total_pnl = total_pnl
            perf.unrealized_pnl = unrealized_pnl
            perf.realized_pnl = realized_pnl
            perf.win_rate = win_rate
            perf.average_win = average_win
            perf.average_loss = average_loss
            perf.profit_factor = profit_factor
            perf.allocated_capital = allocated_capital
            perf.utilized_capital = utilized_capital
            perf.available_capital = available_capital
            
            db.commit()
            
        except Exception as e:
            self.logger.error(f"Error updating strategy performance: {str(e)}")
            db.rollback()
    
    def _get_default_parameters(self, strategy_type: str) -> Dict:
        """Get default parameters for a strategy type."""
        defaults = {
            StrategyType.SENTIMENT.value: {
                'sentiment_threshold': 0.6,
                'min_news_count': 3,
                'stop_loss_percentage': 0.05,
                'take_profit_percentage': 0.15,
                'max_hold_hours': 168,  # 1 week
                'position_size_percentage': 2.0  # 2% of allocated capital per position
            },
            StrategyType.MOMENTUM.value: {
                'momentum_threshold': 0.05,  # 5% price change
                'volume_threshold': 1.5,  # 1.5x average volume
                'lookback_days': 5,
                'stop_loss_percentage': 0.03,
                'take_profit_percentage': 0.10,
                'max_hold_hours': 72,  # 3 days
                'position_size_percentage': 3.0
            },
            StrategyType.MEAN_REVERSION.value: {
                'oversold_threshold': -2.0,  # 2 standard deviations
                'overbought_threshold': 2.0,
                'lookback_days': 20,
                'stop_loss_percentage': 0.04,
                'take_profit_percentage': 0.08,
                'max_hold_hours': 120,  # 5 days
                'position_size_percentage': 2.5
            },
            StrategyType.BREAKOUT.value: {
                'breakout_threshold': 0.03,  # 3% above resistance
                'volume_confirmation': 2.0,  # 2x average volume
                'lookback_days': 10,
                'stop_loss_percentage': 0.04,
                'take_profit_percentage': 0.12,
                'max_hold_hours': 96,  # 4 days
                'position_size_percentage': 2.5
            }
        }
        
        return defaults.get(strategy_type, {})
    
    def _run_sentiment_strategy(self, db: Session, strategy: Strategy, 
                               symbols: List[str], force_analysis: bool) -> Dict:
        """Execute sentiment-based trading strategy."""
        try:
            params = strategy.parameters
            sentiment_threshold = params.get('sentiment_threshold', 0.6)
            min_news_count = params.get('min_news_count', 3)
            
            signals = []
            positions_opened = 0
            
            for symbol in symbols:
                try:
                    # Get or analyze sentiment
                    if force_analysis:
                        sentiment_data = self.sentiment_service.analyze_stock_sentiment(db, symbol)
                    else:
                        sentiment_data = self.sentiment_service.get_stock_sentiment(db, symbol)
                    
                    if not sentiment_data:
                        continue
                    
                    # Check if signal meets criteria
                    if (sentiment_data.overall_sentiment >= sentiment_threshold and
                        sentiment_data.news_count >= min_news_count):
                        
                        # Check if we can open a position
                        if self._can_open_position(db, strategy, symbol):
                            # Calculate position size
                            position_size_pct = params.get('position_size_percentage', 2.0)
                            available_capital = self.position_manager._get_available_capital(db, strategy.id)
                            position_value = available_capital * (position_size_pct / 100.0)
                            
                            # Get current price and calculate quantity
                            market_data = self.data_service.get_market_data(symbol, days=1)
                            current_price = market_data.get('current_price', 0)
                            
                            if current_price > 0:
                                quantity = int(position_value / current_price)
                                
                                if quantity > 0:
                                    # Create entry signal
                                    entry_signal = {
                                        'strategy_type': 'SENTIMENT',
                                        'sentiment_score': sentiment_data.overall_sentiment,
                                        'news_count': sentiment_data.news_count,
                                        'signal_strength': sentiment_data.overall_sentiment,
                                        'market_conditions': {
                                            'price': current_price,
                                            'timestamp': datetime.now().isoformat()
                                        }
                                    }
                                    
                                    # Open position
                                    position = self.position_manager.open_position(
                                        db, strategy.id, symbol, quantity, entry_signal
                                    )
                                    
                                    signals.append({
                                        'symbol': symbol,
                                        'action': 'BUY',
                                        'quantity': quantity,
                                        'price': current_price,
                                        'sentiment_score': sentiment_data.overall_sentiment,
                                        'position_id': position.id
                                    })
                                    
                                    positions_opened += 1
                
                except Exception as e:
                    self.logger.error(f"Error processing {symbol} for sentiment strategy: {str(e)}")
                    continue
            
            # Update strategy performance
            self.update_strategy_performance(db, strategy.id)
            
            return {
                'strategy_name': strategy.name,
                'positions_opened': positions_opened,
                'signals': signals,
                'symbols_analyzed': len(symbols),
                'message': f"Sentiment strategy executed: {positions_opened} positions opened"
            }
            
        except Exception as e:
            self.logger.error(f"Error running sentiment strategy: {str(e)}")
            raise
    
    def _run_momentum_strategy(self, db: Session, strategy: Strategy, symbols: List[str]) -> Dict:
        """Execute momentum-based trading strategy."""
        # Placeholder for momentum strategy implementation
        return {
            'strategy_name': strategy.name,
            'positions_opened': 0,
            'signals': [],
            'message': "Momentum strategy not yet implemented"
        }
    
    def _run_mean_reversion_strategy(self, db: Session, strategy: Strategy, symbols: List[str]) -> Dict:
        """Execute mean reversion trading strategy."""
        # Placeholder for mean reversion strategy implementation
        return {
            'strategy_name': strategy.name,
            'positions_opened': 0,
            'signals': [],
            'message': "Mean reversion strategy not yet implemented"
        }
    
    def _run_breakout_strategy(self, db: Session, strategy: Strategy, symbols: List[str]) -> Dict:
        """Execute breakout trading strategy."""
        # Placeholder for breakout strategy implementation
        return {
            'strategy_name': strategy.name,
            'positions_opened': 0,
            'signals': [],
            'message': "Breakout strategy not yet implemented"
        }
    
    def _can_open_position(self, db: Session, strategy: Strategy, symbol: str) -> bool:
        """Check if we can open a new position for a symbol."""
        try:
            # Check max positions limit
            open_positions = db.query(Position).filter(
                and_(
                    Position.strategy_id == strategy.id,
                    Position.status == PositionStatus.OPEN.value
                )
            ).count()
            
            if open_positions >= strategy.max_positions:
                return False
            
            # Check if we already have a position in this symbol
            existing_position = db.query(Position).filter(
                and_(
                    Position.strategy_id == strategy.id,
                    Position.symbol == symbol,
                    Position.status == PositionStatus.OPEN.value
                )
            ).first()
            
            if existing_position:
                return False
            
            # Check available capital
            available_capital = self.position_manager._get_available_capital(db, strategy.id)
            if available_capital <= 0:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking if can open position: {str(e)}")
            return False
    
    def _create_performance_record(self, db: Session, strategy_id: int) -> None:
        """Create initial performance record for a strategy."""
        try:
            perf = StrategyPerformance(
                strategy_id=strategy_id,
                date=datetime.now()
            )
            db.add(perf)
            db.commit()
            
        except Exception as e:
            self.logger.error(f"Error creating performance record: {str(e)}")
            db.rollback()