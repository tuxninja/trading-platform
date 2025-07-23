"""
Configuration management for the Trading application.
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class."""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./trading_app.db")
    
    # API Keys
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "demo")
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    # Trading Parameters
    INITIAL_BALANCE: float = float(os.getenv("INITIAL_BALANCE", "100000"))
    MAX_POSITION_SIZE: float = float(os.getenv("MAX_POSITION_SIZE", "0.05"))  # 5% of portfolio
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
    
    # Sentiment Analysis Thresholds
    BUY_SENTIMENT_THRESHOLD: float = float(os.getenv("BUY_SENTIMENT_THRESHOLD", "0.2"))
    SELL_SENTIMENT_THRESHOLD: float = float(os.getenv("SELL_SENTIMENT_THRESHOLD", "-0.2"))
    
    # Rate Limiting
    API_RATE_LIMIT: float = float(os.getenv("API_RATE_LIMIT", "1.0"))  # seconds between API calls
    NEWS_API_RATE_LIMIT: float = float(os.getenv("NEWS_API_RATE_LIMIT", "0.2"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # CORS
    CORS_ORIGINS: list = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if origin.strip()
    ]
    
    # Scheduler
    MARKET_OPEN_TIME: str = os.getenv("MARKET_OPEN_TIME", "09:30")
    SENTIMENT_ANALYSIS_TIME: str = os.getenv("SENTIMENT_ANALYSIS_TIME", "10:00")
    STRATEGY_EXECUTION_TIME: str = os.getenv("STRATEGY_EXECUTION_TIME", "10:30")
    MARKET_CLOSE_TIME: str = os.getenv("MARKET_CLOSE_TIME", "16:00")
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate critical configuration values."""
        if cls.NEWS_API_KEY == "demo":
            logging.warning("Using demo NEWS_API_KEY. Limited functionality available.")
        
        if cls.INITIAL_BALANCE <= 0:
            raise ValueError("INITIAL_BALANCE must be greater than 0")
        
        if not (0 < cls.MAX_POSITION_SIZE <= 1):
            raise ValueError("MAX_POSITION_SIZE must be between 0 and 1")
        
        if not (0 <= cls.CONFIDENCE_THRESHOLD <= 1):
            raise ValueError("CONFIDENCE_THRESHOLD must be between 0 and 1")
        
        return True

def setup_logging() -> logging.Logger:
    """Setup application logging."""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL.upper()),
        format=Config.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("trading_app.log")
        ]
    )
    
    logger = logging.getLogger("trading_app")
    logger.info("Logging configured successfully")
    return logger

# Global configuration instance
config = Config()

# Validate configuration on import
config.validate_config()