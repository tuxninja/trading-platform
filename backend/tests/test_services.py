import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from services.trading_service import TradingService
from services.sentiment_service import SentimentService
from services.data_service import DataService
from services.recommendation_service import RecommendationService
from models import Trade, SentimentData, StockData, TradeRecommendation
from exceptions import TradingAppException


class TestTradingService:
    """Test TradingService business logic"""
    
    @pytest.fixture
    def trading_service(self):
        return TradingService()
    
    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=Session)
    
    def test_calculate_position_size(self, trading_service):
        """Test position size calculation"""
        # Test with valid inputs
        size = trading_service.calculate_position_size(100000, 150.0)
        expected = int((100000 * 0.05) / 150.0)  # 5% max position
        assert size == expected
        
        # Test with zero balance
        size = trading_service.calculate_position_size(0, 150.0)
        assert size == 0
        
        # Test with zero price
        size = trading_service.calculate_position_size(100000, 0)
        assert size == 0
    
    @patch('services.trading_service.yfinance.Ticker')
    def test_get_current_price_success(self, mock_ticker, trading_service):
        """Test successful price retrieval"""
        mock_info = MagicMock()
        mock_info.info = {'regularMarketPrice': 150.0}
        mock_ticker.return_value = mock_info
        
        price = trading_service.get_current_price('AAPL')
        assert price == 150.0
    
    @patch('services.trading_service.yfinance.Ticker')
    def test_get_current_price_fallback(self, mock_ticker, trading_service):
        """Test price retrieval with fallback to history"""
        # Mock ticker with no regularMarketPrice
        mock_info = MagicMock()
        mock_info.info = {}
        mock_history = MagicMock()
        mock_history.history.return_value = MagicMock(
            empty=False,
            iloc=[-1, {'Close': 145.0}]
        )
        mock_ticker.return_value = mock_info
        mock_ticker.return_value.history = mock_history.history
        
        with patch.object(trading_service, 'get_current_price_fallback', return_value=145.0):
            price = trading_service.get_current_price('AAPL')
            assert price == 145.0
    
    def test_create_trade_success(self, trading_service, mock_session):
        """Test successful trade creation"""
        with patch.object(trading_service, 'get_current_price', return_value=150.0), \
             patch.object(trading_service, 'recalculate_current_balance'), \
             patch.object(mock_session, 'add'), \
             patch.object(mock_session, 'commit'), \
             patch.object(mock_session, 'refresh'):
            
            trade_data = MagicMock()
            trade_data.symbol = 'AAPL'
            trade_data.trade_type = 'BUY'
            trade_data.quantity = 10
            trade_data.price = 150.0
            trade_data.strategy = 'MANUAL'
            
            result = trading_service.create_trade(mock_session, trade_data)
            
            assert mock_session.add.called
            assert mock_session.commit.called
    
    def test_create_trade_insufficient_balance(self, trading_service, mock_session):
        """Test trade creation with insufficient balance"""
        trading_service.current_balance = 1000.0  # Low balance
        
        with patch.object(trading_service, 'get_current_price', return_value=150.0):
            trade_data = MagicMock()
            trade_data.symbol = 'AAPL'
            trade_data.trade_type = 'BUY'
            trade_data.quantity = 100  # Expensive trade
            trade_data.price = 150.0
            
            with pytest.raises(TradingAppException) as exc_info:
                trading_service.create_trade(mock_session, trade_data)
            
            assert "Insufficient balance" in str(exc_info.value)
    
    def test_close_trade_success(self, trading_service, mock_session):
        """Test successful trade closure"""
        # Mock an open trade
        mock_trade = MagicMock()
        mock_trade.status = 'OPEN'
        mock_trade.trade_type = 'BUY'
        mock_trade.quantity = 10
        mock_trade.price = 150.0
        mock_trade.total_value = 1500.0
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_trade
        
        with patch.object(trading_service, 'get_current_price', return_value=155.0), \
             patch.object(trading_service, 'recalculate_current_balance'), \
             patch.object(mock_session, 'commit'):
            
            result = trading_service.close_trade(mock_session, 1, None)
            
            assert mock_trade.status == 'CLOSED'
            assert mock_trade.close_price == 155.0
            assert mock_trade.profit_loss == 50.0  # (155-150) * 10
    
    def test_calculate_performance_metrics(self, trading_service, mock_session):
        """Test performance metrics calculation"""
        # Mock trades data
        mock_trades = [
            MagicMock(status='CLOSED', profit_loss=100.0),
            MagicMock(status='CLOSED', profit_loss=-50.0),
            MagicMock(status='CLOSED', profit_loss=75.0),
        ]
        
        mock_session.query.return_value.all.return_value = mock_trades
        
        with patch.object(trading_service, 'current_balance', 110000.0):
            metrics = trading_service.get_performance_metrics(mock_session)
            
            assert metrics['total_trades'] == 3
            assert metrics['winning_trades'] == 2
            assert metrics['losing_trades'] == 1
            assert metrics['total_profit_loss'] == 125.0
            assert metrics['win_rate'] == pytest.approx(66.67, rel=1e-2)


class TestSentimentService:
    """Test SentimentService business logic"""
    
    @pytest.fixture
    def sentiment_service(self):
        return SentimentService()
    
    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=Session)
    
    @patch('services.sentiment_service.requests.get')
    def test_fetch_news_success(self, mock_get, sentiment_service):
        """Test successful news fetching"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'articles': [
                {
                    'title': 'Apple reports strong earnings',
                    'description': 'Apple Inc. reported better than expected earnings',
                    'publishedAt': '2023-01-01T12:00:00Z',
                    'url': 'https://example.com/article'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        articles = sentiment_service.fetch_news('AAPL')
        assert len(articles) == 1
        assert articles[0]['title'] == 'Apple reports strong earnings'
    
    def test_calculate_sentiment_positive(self, sentiment_service):
        """Test sentiment calculation for positive text"""
        positive_text = "Apple stock is performing excellently with strong growth"
        
        with patch('services.sentiment_service.SentimentIntensityAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.polarity_scores.return_value = {
                'compound': 0.8, 'pos': 0.7, 'neu': 0.2, 'neg': 0.1
            }
            
            sentiment = sentiment_service.calculate_sentiment(positive_text)
            assert sentiment > 0.5
    
    def test_calculate_sentiment_negative(self, sentiment_service):
        """Test sentiment calculation for negative text"""
        negative_text = "Apple stock crashes amid terrible earnings report"
        
        with patch('services.sentiment_service.SentimentIntensityAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.polarity_scores.return_value = {
                'compound': -0.8, 'pos': 0.1, 'neu': 0.2, 'neg': 0.7
            }
            
            sentiment = sentiment_service.calculate_sentiment(negative_text)
            assert sentiment < -0.5
    
    def test_analyze_stock_sentiment_success(self, sentiment_service, mock_session):
        """Test complete stock sentiment analysis"""
        with patch.object(sentiment_service, 'fetch_news') as mock_fetch, \
             patch.object(sentiment_service, 'calculate_sentiment') as mock_calc, \
             patch.object(mock_session, 'add'), \
             patch.object(mock_session, 'commit'), \
             patch.object(mock_session, 'refresh'):
            
            mock_fetch.return_value = [
                {'title': 'Good news', 'description': 'Positive article'},
                {'title': 'Bad news', 'description': 'Negative article'}
            ]
            mock_calc.side_effect = [0.6, -0.4]  # Mixed sentiment
            
            result = sentiment_service.analyze_stock_sentiment(mock_session, 'AAPL')
            
            assert mock_session.add.called
            assert mock_session.commit.called


class TestDataService:
    """Test DataService business logic"""
    
    @pytest.fixture
    def data_service(self):
        return DataService()
    
    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=Session)
    
    def test_add_stock_success(self, data_service, mock_session):
        """Test successful stock addition"""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        with patch.object(mock_session, 'add'), \
             patch.object(mock_session, 'commit'), \
             patch.object(mock_session, 'refresh'):
            
            result = data_service.add_stock(mock_session, 'AAPL')
            
            assert mock_session.add.called
            assert mock_session.commit.called
    
    def test_add_stock_already_exists(self, data_service, mock_session):
        """Test adding stock that already exists"""
        existing_stock = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = existing_stock
        
        with pytest.raises(TradingAppException) as exc_info:
            data_service.add_stock(mock_session, 'AAPL')
        
        assert "already being tracked" in str(exc_info.value)
    
    @patch('services.data_service.yfinance.Ticker')
    def test_get_market_data_success(self, mock_ticker, data_service):
        """Test successful market data retrieval"""
        mock_history = MagicMock()
        mock_history.index = [datetime.now() - timedelta(days=1)]
        mock_history.to_dict.return_value = {
            'Open': {mock_history.index[0]: 148.0},
            'High': {mock_history.index[0]: 152.0},
            'Low': {mock_history.index[0]: 147.0},
            'Close': {mock_history.index[0]: 150.0},
            'Volume': {mock_history.index[0]: 1000000}
        }
        
        mock_ticker.return_value.history.return_value = mock_history
        
        result = data_service.get_market_data('AAPL', 30)
        
        assert len(result) == 1
        assert result[0]['symbol'] == 'AAPL'
        assert result[0]['close'] == 150.0


class TestRecommendationService:
    """Test RecommendationService business logic"""
    
    @pytest.fixture
    def recommendation_service(self):
        return RecommendationService()
    
    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=Session)
    
    def test_generate_recommendation_strong_buy(self, recommendation_service, mock_session):
        """Test recommendation generation for strong buy signal"""
        # Mock sentiment data
        mock_sentiment = MagicMock()
        mock_sentiment.symbol = 'AAPL'
        mock_sentiment.overall_sentiment = 0.8  # Very positive
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_sentiment
        
        with patch.object(recommendation_service, 'get_current_price', return_value=150.0), \
             patch.object(mock_session, 'add'), \
             patch.object(mock_session, 'commit'):
            
            recommendations = recommendation_service.generate_recommendations(mock_session, ['AAPL'])
            
            assert len(recommendations) == 1
            assert recommendations[0]['action'] == 'BUY'
            assert recommendations[0]['confidence'] > 0.7
    
    def test_generate_recommendation_strong_sell(self, recommendation_service, mock_session):
        """Test recommendation generation for strong sell signal"""
        # Mock sentiment data
        mock_sentiment = MagicMock()
        mock_sentiment.symbol = 'AAPL'
        mock_sentiment.overall_sentiment = -0.8  # Very negative
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_sentiment
        
        with patch.object(recommendation_service, 'get_current_price', return_value=150.0), \
             patch.object(mock_session, 'add'), \
             patch.object(mock_session, 'commit'):
            
            recommendations = recommendation_service.generate_recommendations(mock_session, ['AAPL'])
            
            assert len(recommendations) == 1
            assert recommendations[0]['action'] == 'SELL'
            assert recommendations[0]['confidence'] > 0.7
    
    def test_generate_recommendation_hold(self, recommendation_service, mock_session):
        """Test recommendation generation for hold signal"""
        # Mock sentiment data
        mock_sentiment = MagicMock()
        mock_sentiment.symbol = 'AAPL'
        mock_sentiment.overall_sentiment = 0.1  # Neutral
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_sentiment
        
        recommendations = recommendation_service.generate_recommendations(mock_session, ['AAPL'])
        
        # Should not generate recommendation for neutral sentiment
        assert len(recommendations) == 0
    
    def test_approve_recommendation_success(self, recommendation_service, mock_session):
        """Test successful recommendation approval"""
        mock_recommendation = MagicMock()
        mock_recommendation.status = 'PENDING'
        mock_recommendation.action = 'BUY'
        mock_recommendation.symbol = 'AAPL'
        mock_recommendation.recommended_quantity = 10
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_recommendation
        
        with patch('services.recommendation_service.TradingService') as mock_trading:
            mock_trading.return_value.create_trade.return_value = MagicMock(id=1)
            
            result = recommendation_service.approve_recommendation(mock_session, 1)
            
            assert mock_recommendation.status == 'APPROVED'
            assert mock_trading.return_value.create_trade.called
    
    def test_reject_recommendation_success(self, recommendation_service, mock_session):
        """Test successful recommendation rejection"""
        mock_recommendation = MagicMock()
        mock_recommendation.status = 'PENDING'
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_recommendation
        
        with patch.object(mock_session, 'commit'):
            result = recommendation_service.reject_recommendation(mock_session, 1, "Not suitable")
            
            assert mock_recommendation.status == 'REJECTED'
            assert mock_session.commit.called