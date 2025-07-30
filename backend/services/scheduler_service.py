"""
Scheduler Service for automated trading strategy execution.
Handles scheduled tasks like strategy runs, position monitoring, and market scans.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import get_db
from models import ScheduledTask, Strategy
from services.strategy_service import StrategyService
from services.position_manager import PositionManager
from services.market_scanner import MarketScannerService
from config import config

class SchedulerService:
    """Service for managing scheduled trading tasks."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.strategy_service = StrategyService()
        self.position_manager = PositionManager()
        self.market_scanner = MarketScannerService()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.is_running = False
    
    async def start(self):
        """Start the scheduler."""
        try:
            if not self.is_running:
                self.scheduler.start()
                self.is_running = True
                
                # Setup default scheduled tasks
                await self._setup_default_tasks()
                
                self.logger.info("Scheduler service started")
            
        except Exception as e:
            self.logger.error(f"Error starting scheduler: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the scheduler."""
        try:
            if self.is_running:
                self.scheduler.shutdown()
                self.is_running = False
                self.logger.info("Scheduler service stopped")
                
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {str(e)}")
    
    async def _setup_default_tasks(self):
        """Setup default scheduled tasks."""
        try:
            # Position monitoring (every 15 minutes during market hours)
            self.scheduler.add_job(
                self._check_positions,
                CronTrigger(minute="*/15", hour="9-16", day_of_week="mon-fri"),
                id="position_monitoring",
                replace_existing=True,
                max_instances=1
            )
            
            # Strategy execution (every 30 minutes during market hours)
            self.scheduler.add_job(
                self._run_all_strategies,
                CronTrigger(minute="*/30", hour="9-16", day_of_week="mon-fri"),
                id="strategy_execution",
                replace_existing=True,
                max_instances=1
            )
            
            # Market scanning (every hour during market hours)
            self.scheduler.add_job(
                self._market_scan,
                CronTrigger(minute="0", hour="9-16", day_of_week="mon-fri"),
                id="market_scanning",
                replace_existing=True,
                max_instances=1
            )
            
            # Daily cleanup (after market close)
            self.scheduler.add_job(
                self._daily_cleanup,
                CronTrigger(hour="17", minute="0", day_of_week="mon-fri"),
                id="daily_cleanup",
                replace_existing=True,
                max_instances=1
            )
            
            # Weekend analysis (Saturday morning)
            self.scheduler.add_job(
                self._weekend_analysis,
                CronTrigger(hour="10", minute="0", day_of_week="sat"),
                id="weekend_analysis",
                replace_existing=True,
                max_instances=1
            )
            
            # Adaptive learning analysis (daily after market close, before cleanup)
            self.scheduler.add_job(
                self._adaptive_learning_analysis,
                CronTrigger(hour="16", minute="30", day_of_week="mon-fri"),
                id="adaptive_learning",
                replace_existing=True,
                max_instances=1
            )
            
            # Auto-close stale trades (every 2 hours during market hours)
            self.scheduler.add_job(
                self._auto_close_stale_trades,
                CronTrigger(minute="0", hour="*/2", day_of_week="mon-fri"),
                id="stale_trade_cleanup",
                replace_existing=True,
                max_instances=1
            )
            
            # Continuous watchlist monitoring (every 10 minutes during market hours)
            self.scheduler.add_job(
                self._run_continuous_monitoring,
                CronTrigger(minute="*/10", hour="9-16", day_of_week="mon-fri"),
                id="continuous_monitoring",
                replace_existing=True,
                max_instances=1
            )
            
            self.logger.info("Default scheduled tasks configured")
            
        except Exception as e:
            self.logger.error(f"Error setting up default tasks: {str(e)}")
    
    async def add_strategy_schedule(self, strategy_id: int, schedule_expression: str):
        """Add a custom schedule for a specific strategy."""
        try:
            job_id = f"strategy_{strategy_id}"
            
            # Parse schedule expression (simplified cron format)
            trigger = self._parse_schedule_expression(schedule_expression)
            
            self.scheduler.add_job(
                self._run_specific_strategy,
                trigger,
                args=[strategy_id],
                id=job_id,
                replace_existing=True,
                max_instances=1
            )
            
            self.logger.info(f"Added schedule for strategy {strategy_id}: {schedule_expression}")
            
        except Exception as e:
            self.logger.error(f"Error adding strategy schedule: {str(e)}")
            raise
    
    async def remove_strategy_schedule(self, strategy_id: int):
        """Remove schedule for a specific strategy."""
        try:
            job_id = f"strategy_{strategy_id}"
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Removed schedule for strategy {strategy_id}")
            
        except Exception as e:
            self.logger.error(f"Error removing strategy schedule: {str(e)}")
    
    async def _check_positions(self):
        """Check all open positions for exit conditions."""
        try:
            self.logger.info("Checking position exit conditions...")
            
            # Get database session
            db = next(get_db())
            
            try:
                # Update unrealized P&L for all positions
                self.position_manager.update_unrealized_pnl(db)
                
                # Check exit conditions
                exit_events = self.position_manager.check_exit_conditions(db)
                
                if exit_events:
                    self.logger.info(f"Processed {len(exit_events)} position exits")
                    
                    # Update strategy performance for affected strategies
                    strategy_ids = set(event.get('strategy_id') for event in exit_events if event.get('strategy_id'))
                    for strategy_id in strategy_ids:
                        self.strategy_service.update_strategy_performance(db, strategy_id)
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error checking positions: {str(e)}")
    
    async def _run_all_strategies(self):
        """Run all active strategies."""
        try:
            self.logger.info("Running all active strategies...")
            
            # Get database session
            db = next(get_db())
            
            try:
                result = self.strategy_service.run_all_active_strategies(db)
                
                self.logger.info(
                    f"Strategy run completed: {result.get('successful_strategies', 0)} successful, "
                    f"{result.get('failed_strategies', 0)} failed"
                )
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error running strategies: {str(e)}")
    
    async def _run_specific_strategy(self, strategy_id: int):
        """Run a specific strategy."""
        try:
            self.logger.info(f"Running strategy {strategy_id}...")
            
            # Get database session
            db = next(get_db())
            
            try:
                from schemas import StrategyRunRequest
                request = StrategyRunRequest(strategy_id=strategy_id)
                result = self.strategy_service.run_strategy(db, request)
                
                self.logger.info(f"Strategy {strategy_id} completed: {result.get('message', 'No message')}")
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error running strategy {strategy_id}: {str(e)}")
    
    async def _market_scan(self):
        """Perform market scanning for new opportunities."""
        try:
            self.logger.info("Performing market scan...")
            
            # Get database session
            db = next(get_db())
            
            try:
                # Scan for trending stocks
                discoveries = self.market_scanner.scan_trending_stocks(db, limit=10)
                
                if discoveries:
                    self.logger.info(f"Market scan found {len(discoveries)} trending stocks")
                    
                    # Auto-discover and analyze high-potential stocks
                    result = self.market_scanner.auto_discover_and_analyze(db, min_trending_score=0.6)
                    
                    if result and 'added_stocks' in result:
                        added_count = len(result['added_stocks'])
                        if added_count > 0:
                            self.logger.info(f"Auto-added {added_count} new stocks for analysis")
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error during market scan: {str(e)}")
    
    async def _daily_cleanup(self):
        """Perform daily cleanup tasks."""
        try:
            self.logger.info("Performing daily cleanup...")
            
            # Get database session
            db = next(get_db())
            
            try:
                # Update all strategy performance metrics
                strategies = db.query(Strategy).filter(Strategy.is_active == True).all()
                
                for strategy in strategies:
                    self.strategy_service.update_strategy_performance(db, strategy.id)
                
                # Final position check
                await self._check_positions()
                
                self.logger.info("Daily cleanup completed")
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error during daily cleanup: {str(e)}")
    
    async def _weekend_analysis(self):
        """Perform weekend analysis and preparation."""
        try:
            self.logger.info("Performing weekend analysis...")
            
            # Get database session
            db = next(get_db())
            
            try:
                # Update all strategy performance
                strategies = db.query(Strategy).filter(Strategy.is_active == True).all()
                
                for strategy in strategies:
                    self.strategy_service.update_strategy_performance(db, strategy.id)
                
                # Comprehensive market scan for the week ahead
                result = self.market_scanner.auto_discover_and_analyze(db, min_trending_score=0.4)
                
                if result and 'summary' in result:
                    self.logger.info(f"Weekend analysis: {result['summary']}")
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error during weekend analysis: {str(e)}")
    
    async def _adaptive_learning_analysis(self):
        """Run adaptive learning analysis to improve trading strategy."""
        try:
            self.logger.info("Running adaptive learning analysis...")
            
            # Get database session
            db = next(get_db())
            
            try:
                from services.adaptive_learning_service import AdaptiveLearningService
                
                learning_service = AdaptiveLearningService()
                results = learning_service.analyze_and_learn(db)
                
                self.logger.info(f"Adaptive learning completed: {results['patterns_discovered']} patterns, "
                               f"{results['parameters_adjusted']} adjustments, {results['insights_generated']} insights")
                
                # Log any recommendations
                if results.get('recommendations'):
                    for rec in results['recommendations'][:3]:  # Log top 3 recommendations
                        self.logger.info(f"Learning recommendation: {rec}")
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error during adaptive learning analysis: {str(e)}")
    
    async def _auto_close_stale_trades(self):
        """Automatically close or cancel stale OPEN trades to free up capital"""
        try:
            self.logger.info("Running auto-close for stale trades...")
            
            # Get database session
            db = next(get_db())
            
            try:
                from services.trading_service import TradingService
                
                trading_service = TradingService()
                results = trading_service.auto_close_stale_trades(db, max_age_hours=24)
                
                if "error" not in results:
                    self.logger.info(f"Stale trade cleanup completed: {results['trades_closed']} closed, "
                                   f"{results['trades_cancelled']} cancelled, ${results['capital_freed']:.2f} freed")
                    
                    if results['errors']:
                        self.logger.warning(f"Stale trade cleanup had {len(results['errors'])} errors")
                else:
                    self.logger.error(f"Stale trade cleanup failed: {results['error']}")
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error during stale trade cleanup: {str(e)}")
    
    async def _run_continuous_monitoring(self):
        """Run continuous monitoring for watchlisted stocks"""
        try:
            self.logger.info("Running continuous monitoring cycle...")
            
            # Get database session
            db = next(get_db())
            
            try:
                from services.continuous_monitoring_service import continuous_monitoring_service
                
                results = await continuous_monitoring_service.run_continuous_monitoring(db)
                
                if "error" not in results:
                    self.logger.info(
                        f"Continuous monitoring completed: {results['monitored_count']} stocks, "
                        f"{results['sentiment_updates']} sentiment updates, "
                        f"{results['price_alerts']} alerts, {results['trading_signals']} signals"
                    )
                    
                    if results['errors']:
                        self.logger.warning(f"Monitoring had {len(results['errors'])} errors")
                else:
                    self.logger.error(f"Continuous monitoring failed: {results['error']}")
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error during continuous monitoring: {str(e)}")
    
    def _parse_schedule_expression(self, expression: str):
        """Parse a schedule expression into a CronTrigger."""
        try:
            # Simple parsing for common expressions
            if expression == "every_15_minutes":
                return CronTrigger(minute="*/15", hour="9-16", day_of_week="mon-fri")
            elif expression == "every_30_minutes":
                return CronTrigger(minute="*/30", hour="9-16", day_of_week="mon-fri")
            elif expression == "hourly":
                return CronTrigger(minute="0", hour="9-16", day_of_week="mon-fri")
            elif expression == "daily_open":
                return CronTrigger(hour="9", minute="30", day_of_week="mon-fri")
            elif expression == "daily_close":
                return CronTrigger(hour="15", minute="30", day_of_week="mon-fri")
            else:
                # Try to parse as cron expression
                parts = expression.split()
                if len(parts) == 5:
                    minute, hour, day, month, day_of_week = parts
                    return CronTrigger(
                        minute=minute,
                        hour=hour,
                        day=day,
                        month=month,
                        day_of_week=day_of_week
                    )
                else:
                    raise ValueError(f"Invalid schedule expression: {expression}")
                    
        except Exception as e:
            self.logger.error(f"Error parsing schedule expression '{expression}': {str(e)}")
            raise
    
    def get_scheduled_jobs(self) -> List[Dict]:
        """Get information about all scheduled jobs."""
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name or job.id,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error getting scheduled jobs: {str(e)}")
            return []
    
    def is_market_hours(self) -> bool:
        """Check if current time is within market trading hours."""
        now = datetime.now()
        
        # Simple check for US market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close

# Global scheduler instance
scheduler_service = SchedulerService()