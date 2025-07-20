import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from models import Trade, SentimentData, StockData
from services.trading_service import TradingService


class TestTradingAPI:
    """Test trading-related API endpoints"""
    
    def test_get_trades_empty(self, client, test_db):
        """Test getting trades when none exist"""
        response = client.get("/api/trades")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_create_trade_success(self, client, test_db, sample_trade_data):
        """Test successful trade creation"""
        with patch('services.trading_service.TradingService.get_current_price') as mock_price:
            mock_price.return_value = 150.0
            
            response = client.post("/api/trades", json=sample_trade_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "AAPL"
            assert data["trade_type"] == "BUY"
            assert data["quantity"] == 10
            assert data["status"] == "OPEN"
    
    def test_create_trade_invalid_symbol(self, client, test_db):
        """Test trade creation with invalid symbol"""
        invalid_trade = {
            "symbol": "",
            "trade_type": "BUY", 
            "quantity": 10,
            "price": 150.0
        }
        
        response = client.post("/api/trades", json=invalid_trade)
        assert response.status_code == 422  # Validation error
    
    def test_create_trade_insufficient_balance(self, client, test_db):
        """Test trade creation with insufficient balance"""
        large_trade = {
            "symbol": "AAPL",
            "trade_type": "BUY",
            "quantity": 1000000,  # Very large quantity
            "price": 150.0
        }
        
        with patch('services.trading_service.TradingService.get_current_price') as mock_price:
            mock_price.return_value = 150.0
            
            response = client.post("/api/trades", json=large_trade)
            assert response.status_code == 400
            assert "insufficient balance" in response.json()["detail"].lower()
    
    def test_get_trade_by_id(self, client, test_db, sample_trade_data):
        """Test getting a specific trade by ID"""
        # First create a trade
        with patch('services.trading_service.TradingService.get_current_price') as mock_price:
            mock_price.return_value = 150.0
            
            create_response = client.post("/api/trades", json=sample_trade_data)
            trade_id = create_response.json()["id"]
            
            # Then get it by ID
            response = client.get(f"/api/trades/{trade_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == trade_id
            assert data["symbol"] == "AAPL"
    
    def test_get_trade_by_id_not_found(self, client, test_db):
        """Test getting a trade with non-existent ID"""
        response = client.get("/api/trades/999")
        assert response.status_code == 404
    
    def test_close_trade_success(self, client, test_db, sample_trade_data):
        """Test successfully closing a trade"""
        # First create a trade
        with patch('services.trading_service.TradingService.get_current_price') as mock_price:
            mock_price.return_value = 150.0
            
            create_response = client.post("/api/trades", json=sample_trade_data)
            trade_id = create_response.json()["id"]
            
            # Then close it
            mock_price.return_value = 155.0  # Higher price for profit
            response = client.post(f"/api/trades/{trade_id}/close")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "CLOSED"
            assert data["close_price"] == 155.0
            assert data["profit_loss"] > 0  # Should be profitable
    
    def test_close_trade_with_custom_price(self, client, test_db, sample_trade_data):
        """Test closing a trade with custom price"""
        # First create a trade
        with patch('services.trading_service.TradingService.get_current_price') as mock_price:
            mock_price.return_value = 150.0
            
            create_response = client.post("/api/trades", json=sample_trade_data)
            trade_id = create_response.json()["id"]
            
            # Close with custom price
            response = client.post(
                f"/api/trades/{trade_id}/close",
                json={"close_price": 160.0}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["close_price"] == 160.0
    
    def test_close_trade_not_found(self, client, test_db):
        """Test closing a non-existent trade"""
        response = client.post("/api/trades/999/close")
        assert response.status_code == 400
    
    def test_delete_trade_success(self, client, test_db, sample_trade_data):
        """Test successfully deleting a trade"""
        # First create a trade
        with patch('services.trading_service.TradingService.get_current_price') as mock_price:
            mock_price.return_value = 150.0
            
            create_response = client.post("/api/trades", json=sample_trade_data)
            trade_id = create_response.json()["id"]
            
            # Then delete it
            response = client.delete(f"/api/trades/{trade_id}")
            assert response.status_code == 200
            
            # Verify it's deleted
            get_response = client.get(f"/api/trades/{trade_id}")
            assert get_response.status_code == 404
    
    def test_delete_trade_not_found(self, client, test_db):
        """Test deleting a non-existent trade"""
        response = client.delete("/api/trades/999")
        assert response.status_code == 400


class TestPerformanceAPI:
    """Test performance-related API endpoints"""
    
    def test_get_performance_no_trades(self, client, test_db):
        """Test getting performance metrics with no trades"""
        response = client.get("/api/performance")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_trades"] == 0
        assert data["winning_trades"] == 0
        assert data["losing_trades"] == 0
        assert data["total_profit_loss"] == 0
        assert data["win_rate"] == 0
    
    def test_get_performance_with_trades(self, client, test_db, sample_trade_data):
        """Test getting performance metrics with trades"""
        # Create and close a profitable trade
        with patch('services.trading_service.TradingService.get_current_price') as mock_price:
            mock_price.return_value = 150.0
            
            create_response = client.post("/api/trades", json=sample_trade_data)
            trade_id = create_response.json()["id"]
            
            # Close at higher price for profit
            mock_price.return_value = 155.0
            client.post(f"/api/trades/{trade_id}/close")
            
            # Check performance
            response = client.get("/api/performance")
            assert response.status_code == 200
            
            data = response.json()
            assert data["total_trades"] > 0
            assert data["winning_trades"] >= 1
            assert data["total_profit_loss"] > 0
            assert data["win_rate"] > 0
    
    def test_get_portfolio_history(self, client, test_db):
        """Test getting portfolio history"""
        response = client.get("/api/portfolio-history?days=7")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_recalculate_balance(self, client, test_db):
        """Test balance recalculation endpoint"""
        response = client.post("/api/recalculate-balance")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "current_balance" in data


class TestSentimentAPI:
    """Test sentiment-related API endpoints"""
    
    def test_get_sentiment_empty(self, client, test_db):
        """Test getting sentiment when none exists"""
        response = client.get("/api/sentiment")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_sentiment_by_symbol_not_found(self, client, test_db):
        """Test getting sentiment for non-existent symbol"""
        response = client.get("/api/sentiment/NONEXISTENT")
        assert response.status_code == 200
        assert response.json() == []
    
    @patch('services.sentiment_service.SentimentService.analyze_stock_sentiment')
    def test_analyze_sentiment_success(self, mock_analyze, client, test_db):
        """Test successful sentiment analysis"""
        mock_analyze.return_value = {
            "symbol": "AAPL",
            "overall_sentiment": 0.5,
            "news_sentiment": 0.6,
            "social_sentiment": 0.4,
            "news_count": 5,
            "social_count": 3,
            "source": "test"
        }
        
        response = client.post("/api/analyze-sentiment", json={"symbol": "AAPL"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["overall_sentiment"] == 0.5
    
    @patch('services.sentiment_service.SentimentService.analyze_stock_sentiment')
    def test_analyze_bulk_sentiment(self, mock_analyze, client, test_db):
        """Test bulk sentiment analysis"""
        mock_analyze.return_value = {
            "symbol": "AAPL",
            "overall_sentiment": 0.5,
            "news_sentiment": 0.6,
            "social_sentiment": 0.4,
            "news_count": 5,
            "social_count": 3,
            "source": "test"
        }
        
        response = client.post(
            "/api/analyze-bulk-sentiment",
            json={"symbols": ["AAPL", "GOOGL"], "force_refresh": True}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "total_processed" in data
        assert "successful" in data
        assert "failed" in data


class TestStocksAPI:
    """Test stocks management API endpoints"""
    
    def test_get_stocks_empty(self, client, test_db):
        """Test getting stocks when none are tracked"""
        response = client.get("/api/stocks")
        assert response.status_code == 200
        # Should return empty list or basic stocks
    
    def test_add_stock_success(self, client, test_db):
        """Test successfully adding a stock"""
        response = client.post("/api/stocks", json={"symbol": "AAPL"})
        assert response.status_code == 200
        
        data = response.json()
        assert "symbol" in data
        assert data["symbol"] == "AAPL"
    
    def test_add_stock_invalid_format(self, client, test_db):
        """Test adding stock with invalid format"""
        response = client.post("/api/stocks", json={"symbol": ""})
        assert response.status_code == 400
        assert "Invalid stock symbol format" in response.json()["detail"]
    
    def test_add_stock_too_long(self, client, test_db):
        """Test adding stock with symbol too long"""
        response = client.post("/api/stocks", json={"symbol": "VERYLONGSYMBOL"})
        assert response.status_code == 400
    
    @patch('services.data_service.DataService.get_market_data')
    def test_get_market_data(self, mock_market_data, client, test_db):
        """Test getting market data for a symbol"""
        mock_market_data.return_value = [
            {"date": "2023-01-01", "close": 150.0, "volume": 1000000}
        ]
        
        response = client.get("/api/market-data/AAPL?days=30")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestStrategyAPI:
    """Test strategy execution API endpoints"""
    
    @patch('services.trading_service.TradingService.run_sentiment_strategy')
    def test_run_strategy_success(self, mock_strategy, client, test_db):
        """Test successful strategy execution"""
        mock_strategy.return_value = {
            "trades_executed": 2,
            "total_value": 5000.0,
            "message": "Strategy executed successfully"
        }
        
        response = client.post("/api/run-strategy")
        assert response.status_code == 200
        
        data = response.json()
        assert "trades_executed" in data
        assert "message" in data