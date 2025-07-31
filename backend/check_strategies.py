#!/usr/bin/env python3
"""
Quick script to check if there are active strategies in the database
and create a basic trading strategy if none exist.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Strategy, StrategyType
from datetime import datetime

def check_and_create_strategies():
    """Check for active strategies and create basic ones if needed."""
    db = SessionLocal()
    
    try:
        # Check for active strategies
        active_strategies = db.query(Strategy).filter(Strategy.is_active == True).all()
        
        print(f"Found {len(active_strategies)} active strategies:")
        for strategy in active_strategies:
            print(f"  - {strategy.name} (ID: {strategy.id}, Type: {strategy.strategy_type})")
        
        if not active_strategies:
            print("\nNo active strategies found! Creating basic sentiment-based strategy...")
            
            # Create a basic sentiment-based trading strategy
            sentiment_strategy = Strategy(
                name="Basic Sentiment Trading",
                description="Automated trading based on sentiment analysis",
                strategy_type=StrategyType.SENTIMENT_BASED,
                parameters={
                    "min_sentiment_score": 0.6,
                    "max_position_size": 5000,
                    "stop_loss_percent": 8.0,
                    "take_profit_percent": 15.0,
                    "max_positions": 5
                },
                is_active=True,
                created_at=datetime.now()
            )
            
            db.add(sentiment_strategy)
            db.commit()
            
            print(f"✅ Created basic sentiment strategy (ID: {sentiment_strategy.id})")
            
            # Create a momentum-based strategy as well
            momentum_strategy = Strategy(
                name="Basic Momentum Trading",
                description="Automated trading based on price momentum",
                strategy_type=StrategyType.MOMENTUM,
                parameters={
                    "rsi_oversold": 30,
                    "rsi_overbought": 70,
                    "volume_threshold": 1.5,
                    "max_position_size": 3000,
                    "stop_loss_percent": 5.0,
                    "take_profit_percent": 10.0,
                    "max_positions": 3
                },
                is_active=True,
                created_at=datetime.now()
            )
            
            db.add(momentum_strategy)
            db.commit()
            
            print(f"✅ Created basic momentum strategy (ID: {momentum_strategy.id})")
            
        else:
            print("\n✅ Active strategies found - trading should be working")
        
        # Check recent trades
        from models import Trade
        recent_trades = db.query(Trade).filter(
            Trade.timestamp >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        print(f"\n📊 Trades created today: {recent_trades}")
        
        if recent_trades == 0:
            print("⚠️  No trades today - this could indicate:")
            print("   1. Market conditions don't meet strategy criteria")
            print("   2. Scheduler is not running properly")
            print("   3. Strategy execution is failing")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    check_and_create_strategies()