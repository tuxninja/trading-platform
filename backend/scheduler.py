import schedule
import time
import threading
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from database import SessionLocal
from services.sentiment_service import SentimentService
from services.data_service import DataService
from services.trading_service import TradingService
from config import config, setup_logging

class DataScheduler:
    def __init__(self):
        self.sentiment_service = SentimentService()
        self.data_service = DataService()
        self.trading_service = TradingService()
        self.running = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_db_session(self) -> Session:
        """Get a database session"""
        return SessionLocal()
    
    def collect_market_data(self):
        """Collect daily market data for all tracked stocks"""
        self.logger.info("Starting daily market data collection...")
        
        db = self.get_db_session()
        try:
            results = self.data_service.run_daily_data_collection(db)
            self.logger.info(f"Collected data for {len(results)} stocks")
        except Exception as e:
            self.logger.error(f"Error collecting market data: {str(e)}")
        finally:
            db.close()
    
    def analyze_sentiment(self):
        """Run daily sentiment analysis for all tracked stocks"""
        self.logger.info("Starting daily sentiment analysis...")
        
        db = self.get_db_session()
        try:
            results = self.sentiment_service.run_daily_sentiment_analysis(db)
            self.logger.info(f"Analyzed sentiment for {len(results)} stocks")
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {str(e)}")
        finally:
            db.close()
    
    def run_trading_strategy(self):
        """Run the sentiment-based trading strategy"""
        self.logger.info("Running trading strategy...")
        
        db = self.get_db_session()
        try:
            result = self.trading_service.run_sentiment_strategy(db)
            if "error" not in result:
                self.logger.info(f"Strategy executed: {result['trades_executed']} trades")
            else:
                self.logger.error(f"Strategy error: {result['error']}")
        except Exception as e:
            self.logger.error(f"Error running trading strategy: {str(e)}")
        finally:
            db.close()
    
    def setup_schedule(self):
        """Setup the daily schedule using configuration values"""
        # Market data collection at market open
        schedule.every().day.at(config.MARKET_OPEN_TIME).do(self.collect_market_data)
        
        # Sentiment analysis
        schedule.every().day.at(config.SENTIMENT_ANALYSIS_TIME).do(self.analyze_sentiment)
        
        # Trading strategy execution
        schedule.every().day.at(config.STRATEGY_EXECUTION_TIME).do(self.run_trading_strategy)
        
        # Additional data collection throughout the day
        schedule.every().hour.do(self.collect_market_data)
        
        # End of day summary at market close
        schedule.every().day.at(config.MARKET_CLOSE_TIME).do(self.collect_market_data)
        
        self.logger.info(f"Scheduler configured with market open: {config.MARKET_OPEN_TIME}, close: {config.MARKET_CLOSE_TIME}")
    
    def run_scheduler(self):
        """Run the scheduler in a loop"""
        self.running = True
        self.logger.info("Scheduler started")
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start(self):
        """Start the scheduler in a separate thread"""
        self.setup_schedule()
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        self.logger.info("Scheduler started in background thread")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        self.logger.info("Scheduler stopped")

# Global scheduler instance
scheduler = DataScheduler()

def start_scheduler():
    """Start the data collection scheduler"""
    scheduler.start()

def stop_scheduler():
    """Stop the data collection scheduler"""
    scheduler.stop()

if __name__ == "__main__":
    # Setup logging for standalone execution
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # For testing - run once immediately
    logger.info("Running initial data collection...")
    
    db = SessionLocal()
    try:
        # Collect initial data
        scheduler.collect_market_data()
        scheduler.analyze_sentiment()
        scheduler.run_trading_strategy()
    finally:
        db.close()
    
    # Start the scheduler
    start_scheduler()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        stop_scheduler() 