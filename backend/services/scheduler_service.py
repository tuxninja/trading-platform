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
            
            self.logger.info("Default scheduled tasks configured")
            
        except Exception as e:
            self.logger.error(f"Error setting up default tasks: {str(e)}")
    
    async def add_strategy_schedule(self, strategy_id: int, schedule_expression: str):
        """Add a custom schedule for a specific strategy."""
        try:
            job_id = f"strategy_{strategy_id}"\n            \n            # Parse schedule expression (simplified cron format)\n            trigger = self._parse_schedule_expression(schedule_expression)\n            \n            self.scheduler.add_job(\n                self._run_specific_strategy,\n                trigger,\n                args=[strategy_id],\n                id=job_id,\n                replace_existing=True,\n                max_instances=1\n            )\n            \n            self.logger.info(f"Added schedule for strategy {strategy_id}: {schedule_expression}")\n            \n        except Exception as e:\n            self.logger.error(f"Error adding strategy schedule: {str(e)}")\n            raise\n    \n    async def remove_strategy_schedule(self, strategy_id: int):\n        """Remove schedule for a specific strategy."""\n        try:\n            job_id = f"strategy_{strategy_id}"\n            self.scheduler.remove_job(job_id)\n            self.logger.info(f"Removed schedule for strategy {strategy_id}")\n            \n        except Exception as e:\n            self.logger.error(f"Error removing strategy schedule: {str(e)}")\n    \n    async def _check_positions(self):\n        """Check all open positions for exit conditions."""\n        try:\n            self.logger.info("Checking position exit conditions...")\n            \n            # Get database session\n            db = next(get_db())\n            \n            try:\n                # Update unrealized P&L for all positions\n                self.position_manager.update_unrealized_pnl(db)\n                \n                # Check exit conditions\n                exit_events = self.position_manager.check_exit_conditions(db)\n                \n                if exit_events:\n                    self.logger.info(f"Processed {len(exit_events)} position exits")\n                    \n                    # Update strategy performance for affected strategies\n                    strategy_ids = set(event.get('strategy_id') for event in exit_events if event.get('strategy_id'))\n                    for strategy_id in strategy_ids:\n                        self.strategy_service.update_strategy_performance(db, strategy_id)\n                \n            finally:\n                db.close()\n                \n        except Exception as e:\n            self.logger.error(f"Error checking positions: {str(e)}")\n    \n    async def _run_all_strategies(self):\n        """Run all active strategies."""\n        try:\n            self.logger.info("Running all active strategies...")\n            \n            # Get database session\n            db = next(get_db())\n            \n            try:\n                result = self.strategy_service.run_all_active_strategies(db)\n                \n                self.logger.info(\n                    f"Strategy run completed: {result.get('successful_strategies', 0)} successful, "\n                    f"{result.get('failed_strategies', 0)} failed"\n                )\n                \n            finally:\n                db.close()\n                \n        except Exception as e:\n            self.logger.error(f"Error running strategies: {str(e)}")\n    \n    async def _run_specific_strategy(self, strategy_id: int):\n        """Run a specific strategy."""\n        try:\n            self.logger.info(f"Running strategy {strategy_id}...")\n            \n            # Get database session\n            db = next(get_db())\n            \n            try:\n                from schemas import StrategyRunRequest\n                request = StrategyRunRequest(strategy_id=strategy_id)\n                result = self.strategy_service.run_strategy(db, request)\n                \n                self.logger.info(f"Strategy {strategy_id} completed: {result.get('message', 'No message')}")\n                \n            finally:\n                db.close()\n                \n        except Exception as e:\n            self.logger.error(f"Error running strategy {strategy_id}: {str(e)}")\n    \n    async def _market_scan(self):\n        """Perform market scanning for new opportunities."""\n        try:\n            self.logger.info("Performing market scan...")\n            \n            # Get database session\n            db = next(get_db())\n            \n            try:\n                # Scan for trending stocks\n                discoveries = self.market_scanner.scan_trending_stocks(db, limit=10)\n                \n                if discoveries:\n                    self.logger.info(f"Market scan found {len(discoveries)} trending stocks")\n                    \n                    # Auto-discover and analyze high-potential stocks\n                    result = self.market_scanner.auto_discover_and_analyze(db, min_trending_score=0.6)\n                    \n                    if result and 'added_stocks' in result:\n                        added_count = len(result['added_stocks'])\n                        if added_count > 0:\n                            self.logger.info(f"Auto-added {added_count} new stocks for analysis")\n                \n            finally:\n                db.close()\n                \n        except Exception as e:\n            self.logger.error(f"Error during market scan: {str(e)}")\n    \n    async def _daily_cleanup(self):\n        """Perform daily cleanup tasks."""\n        try:\n            self.logger.info("Performing daily cleanup...")\n            \n            # Get database session\n            db = next(get_db())\n            \n            try:\n                # Update all strategy performance metrics\n                strategies = db.query(Strategy).filter(Strategy.is_active == True).all()\n                \n                for strategy in strategies:\n                    self.strategy_service.update_strategy_performance(db, strategy.id)\n                \n                # Final position check\n                await self._check_positions()\n                \n                self.logger.info("Daily cleanup completed")\n                \n            finally:\n                db.close()\n                \n        except Exception as e:\n            self.logger.error(f"Error during daily cleanup: {str(e)}")\n    \n    async def _weekend_analysis(self):\n        """Perform weekend analysis and preparation."""\n        try:\n            self.logger.info("Performing weekend analysis...")\n            \n            # Get database session\n            db = next(get_db())\n            \n            try:\n                # Update all strategy performance\n                strategies = db.query(Strategy).filter(Strategy.is_active == True).all()\n                \n                for strategy in strategies:\n                    self.strategy_service.update_strategy_performance(db, strategy.id)\n                \n                # Comprehensive market scan for the week ahead\n                result = self.market_scanner.auto_discover_and_analyze(db, min_trending_score=0.4)\n                \n                if result and 'summary' in result:\n                    self.logger.info(f"Weekend analysis: {result['summary']}")\n                \n            finally:\n                db.close()\n                \n        except Exception as e:\n            self.logger.error(f"Error during weekend analysis: {str(e)}")\n    \n    def _parse_schedule_expression(self, expression: str):\n        """Parse a schedule expression into a CronTrigger."""\n        try:\n            # Simple parsing for common expressions\n            if expression == "every_15_minutes":\n                return CronTrigger(minute="*/15", hour="9-16", day_of_week="mon-fri")\n            elif expression == "every_30_minutes":\n                return CronTrigger(minute="*/30", hour="9-16", day_of_week="mon-fri")\n            elif expression == "hourly":\n                return CronTrigger(minute="0", hour="9-16", day_of_week="mon-fri")\n            elif expression == "daily_open":\n                return CronTrigger(hour="9", minute="30", day_of_week="mon-fri")\n            elif expression == "daily_close":\n                return CronTrigger(hour="15", minute="30", day_of_week="mon-fri")\n            else:\n                # Try to parse as cron expression\n                parts = expression.split()\n                if len(parts) == 5:\n                    minute, hour, day, month, day_of_week = parts\n                    return CronTrigger(\n                        minute=minute,\n                        hour=hour,\n                        day=day,\n                        month=month,\n                        day_of_week=day_of_week\n                    )\n                else:\n                    raise ValueError(f"Invalid schedule expression: {expression}")\n                    \n        except Exception as e:\n            self.logger.error(f"Error parsing schedule expression '{expression}': {str(e)}")\n            raise\n    \n    def get_scheduled_jobs(self) -> List[Dict]:\n        """Get information about all scheduled jobs."""\n        try:\n            jobs = []\n            for job in self.scheduler.get_jobs():\n                jobs.append({\n                    'id': job.id,\n                    'name': job.name or job.id,\n                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,\n                    'trigger': str(job.trigger)\n                })\n            \n            return jobs\n            \n        except Exception as e:\n            self.logger.error(f"Error getting scheduled jobs: {str(e)}")\n            return []\n    \n    def is_market_hours(self) -> bool:\n        """Check if current time is within market trading hours."""\n        now = datetime.now()\n        \n        # Simple check for US market hours (9:30 AM - 4:00 PM ET, Mon-Fri)\n        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6\n            return False\n        \n        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)\n        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)\n        \n        return market_open <= now <= market_close\n\n# Global scheduler instance\nscheduler_service = SchedulerService()