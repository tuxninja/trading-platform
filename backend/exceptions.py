"""
Custom exception classes for the Trading application.
"""

class TradingAppException(Exception):
    """Base exception class for Trading application."""
    pass

class InsufficientBalanceError(TradingAppException):
    """Raised when there's insufficient balance for a trade."""
    pass

class InsufficientSharesError(TradingAppException):
    """Raised when there are insufficient shares to sell."""
    pass

class InvalidTradeError(TradingAppException):
    """Raised when a trade is invalid."""
    pass

class TradeNotFoundError(TradingAppException):
    """Raised when a trade is not found."""
    pass

class StockDataError(TradingAppException):
    """Raised when there's an error with stock data."""
    pass

class SentimentAnalysisError(TradingAppException):
    """Raised when there's an error with sentiment analysis."""
    pass

class APIRateLimitError(TradingAppException):
    """Raised when API rate limit is exceeded."""
    pass

class ConfigurationError(TradingAppException):
    """Raised when there's a configuration error."""
    pass

class DatabaseError(TradingAppException):
    """Raised when there's a database error."""
    pass