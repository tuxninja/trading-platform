import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from database import get_db, Base
from auth import auth_service
from config import config

# Test database setup
@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine"""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with dependency override"""
    def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def mock_google_token():
    """Mock Google OAuth token verification"""
    with patch.object(auth_service, 'verify_google_token') as mock:
        mock.return_value = {
            'user_id': 'test_user_123',
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/avatar.jpg',
            'verified_email': True
        }
        yield mock

@pytest.fixture
def authenticated_headers(mock_google_token):
    """Get authentication headers for testing"""
    # Create a test JWT token
    user_data = mock_google_token.return_value
    jwt_token = auth_service.create_jwt_token(user_data)
    return {"Authorization": f"Bearer {jwt_token}"}

@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing"""
    return {
        "symbol": "AAPL",
        "trade_type": "BUY",
        "quantity": 10,
        "price": 150.0,
        "strategy": "MANUAL"
    }

@pytest.fixture
def sample_sentiment_data():
    """Sample sentiment data for testing"""
    return {
        "symbol": "AAPL",
        "news_sentiment": 0.5,
        "social_sentiment": 0.3,
        "overall_sentiment": 0.4,
        "news_count": 5,
        "social_count": 10,
        "source": "test_source"
    }