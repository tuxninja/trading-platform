"""
Seed script to create default trading strategies.
"""
import logging
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from models import Strategy, StrategyType
from services.strategy_service import StrategyService
from schemas import StrategyCreate

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_default_strategies():
    """Create default trading strategies."""
    
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = next(get_db())
    strategy_service = StrategyService()
    
    try:
        # Check if strategies already exist
        existing_strategies = db.query(Strategy).count()
        if existing_strategies > 0:
            logger.info(f"Found {existing_strategies} existing strategies, skipping seed")
            return
        
        # Default strategies to create
        default_strategies = [
            {
                "name": "Aggressive Sentiment Strategy",
                "strategy_type": StrategyType.SENTIMENT.value,
                "description": "High-frequency sentiment-based trading with aggressive parameters",
                "parameters": {
                    "sentiment_threshold": 0.7,
                    "min_news_count": 2,
                    "stop_loss_percentage": 0.03,
                    "take_profit_percentage": 0.12,
                    "max_hold_hours": 48,
                    "position_size_percentage": 3.0,
                    "trailing_stop_percentage": 0.02
                },
                "allocation_percentage": 15.0,
                "max_positions": 8,
                "risk_level": "HIGH"
            },
            {
                "name": "Conservative Sentiment Strategy",
                "strategy_type": StrategyType.SENTIMENT.value,
                "description": "Conservative sentiment-based trading with defensive parameters",
                "parameters": {
                    "sentiment_threshold": 0.6,
                    "min_news_count": 5,
                    "stop_loss_percentage": 0.05,
                    "take_profit_percentage": 0.10,
                    "max_hold_hours": 120,
                    "position_size_percentage": 2.0,
                    "trailing_stop_percentage": 0.03
                },
                "allocation_percentage": 20.0,
                "max_positions": 5,
                "risk_level": "LOW"
            },
            {
                "name": "Balanced Sentiment Strategy",
                "strategy_type": StrategyType.SENTIMENT.value,
                "description": "Balanced approach to sentiment trading",
                "parameters": {
                    "sentiment_threshold": 0.65,
                    "min_news_count": 3,
                    "stop_loss_percentage": 0.04,
                    "take_profit_percentage": 0.15,
                    "max_hold_hours": 72,
                    "position_size_percentage": 2.5,
                    "trailing_stop_percentage": 0.025
                },
                "allocation_percentage": 25.0,
                "max_positions": 6,
                "risk_level": "MEDIUM"
            },
            {
                "name": "Momentum Breakout Strategy",
                "strategy_type": StrategyType.MOMENTUM.value,
                "description": "Captures momentum breakouts with volume confirmation",
                "parameters": {
                    "momentum_threshold": 0.04,
                    "volume_threshold": 2.0,
                    "lookback_days": 7,
                    "stop_loss_percentage": 0.035,
                    "take_profit_percentage": 0.12,
                    "max_hold_hours": 96,
                    "position_size_percentage": 3.0
                },
                "allocation_percentage": 20.0,
                "max_positions": 7,
                "risk_level": "HIGH"
            },
            {
                "name": "Mean Reversion Strategy",
                "strategy_type": StrategyType.MEAN_REVERSION.value,
                "description": "Exploits temporary price deviations from the mean",
                "parameters": {
                    "oversold_threshold": -1.5,
                    "overbought_threshold": 1.5,
                    "lookback_days": 15,
                    "stop_loss_percentage": 0.045,
                    "take_profit_percentage": 0.08,
                    "max_hold_hours": 144,
                    "position_size_percentage": 2.0
                },
                "allocation_percentage": 20.0,
                "max_positions": 4,
                "risk_level": "MEDIUM"
            }
        ]
        
        created_strategies = []
        
        for strategy_data in default_strategies:
            try:
                strategy_create = StrategyCreate(**strategy_data)
                created_strategy = strategy_service.create_strategy(db, strategy_create)
                created_strategies.append(created_strategy)
                logger.info(f"Created strategy: {created_strategy.name}")
                
            except Exception as e:
                logger.error(f"Error creating strategy {strategy_data['name']}: {str(e)}")
                continue
        
        logger.info(f"Successfully created {len(created_strategies)} default strategies")
        
        # Print summary
        print("\n" + "="*60)
        print("DEFAULT TRADING STRATEGIES CREATED")
        print("="*60)
        
        for strategy in created_strategies:
            print(f"\n{strategy.name}")
            print(f"  Type: {strategy.strategy_type}")
            print(f"  Allocation: {strategy.allocation_percentage}%")
            print(f"  Max Positions: {strategy.max_positions}")
            print(f"  Risk Level: {strategy.risk_level}")
            print(f"  Description: {strategy.description}")
        
        print(f"\nTotal Portfolio Allocation: {sum(s.allocation_percentage for s in created_strategies)}%")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Error creating default strategies: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()

if __name__ == "__main__":
    create_default_strategies()