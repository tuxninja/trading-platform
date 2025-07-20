import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
import jwt
from datetime import datetime, timedelta

from auth import AuthService, get_current_user, auth_service
from schemas import GoogleLoginRequest


class TestAuthService:
    """Test the AuthService class"""
    
    def test_init_with_google_client_id(self):
        """Test AuthService initialization with Google Client ID"""
        with patch.dict('os.environ', {'GOOGLE_CLIENT_ID': 'test_client_id'}):
            service = AuthService()
            assert service.google_client_id == 'test_client_id'
    
    def test_init_without_google_client_id(self):
        """Test AuthService initialization without Google Client ID"""
        with patch.dict('os.environ', {}, clear=True):
            service = AuthService()
            assert service.google_client_id is None
    
    @patch('auth.id_token.verify_oauth2_token')
    @patch('auth.requests.Request')
    def test_verify_google_token_success(self, mock_request, mock_verify):
        """Test successful Google token verification"""
        mock_verify.return_value = {
            'iss': 'accounts.google.com',
            'sub': 'user123',
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/pic.jpg',
            'email_verified': True
        }
        
        service = AuthService()
        service.google_client_id = 'test_client_id'
        
        result = service.verify_google_token('test_token')
        
        assert result['user_id'] == 'user123'
        assert result['email'] == 'test@example.com'
        assert result['name'] == 'Test User'
        assert result['verified_email'] is True
    
    @patch('auth.id_token.verify_oauth2_token')
    def test_verify_google_token_invalid_issuer(self, mock_verify):
        """Test Google token verification with invalid issuer"""
        mock_verify.return_value = {
            'iss': 'invalid.issuer.com',
            'sub': 'user123'
        }
        
        service = AuthService()
        service.google_client_id = 'test_client_id'
        
        with pytest.raises(HTTPException) as exc_info:
            service.verify_google_token('test_token')
        
        assert exc_info.value.status_code == 401
        assert "Invalid Google token" in str(exc_info.value.detail)
    
    @patch('auth.id_token.verify_oauth2_token')
    def test_verify_google_token_exception(self, mock_verify):
        """Test Google token verification with exception"""
        mock_verify.side_effect = ValueError("Invalid token")
        
        service = AuthService()
        service.google_client_id = 'test_client_id'
        
        with pytest.raises(HTTPException) as exc_info:
            service.verify_google_token('test_token')
        
        assert exc_info.value.status_code == 401
    
    def test_create_jwt_token(self):
        """Test JWT token creation"""
        service = AuthService()
        user_data = {
            'user_id': 'user123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        token = service.create_jwt_token(user_data)
        assert isinstance(token, str)
        
        # Decode and verify token
        decoded = jwt.decode(token, service.jwt_secret, algorithms=[service.jwt_algorithm])
        assert decoded['user_id'] == 'user123'
        assert decoded['email'] == 'test@example.com'
        assert decoded['name'] == 'Test User'
        assert 'exp' in decoded
        assert 'iat' in decoded
    
    def test_verify_jwt_token_success(self):
        """Test successful JWT token verification"""
        service = AuthService()
        user_data = {
            'user_id': 'user123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        token = service.create_jwt_token(user_data)
        result = service.verify_jwt_token(token)
        
        assert result['user_id'] == 'user123'
        assert result['email'] == 'test@example.com'
    
    def test_verify_jwt_token_expired(self):
        """Test JWT token verification with expired token"""
        service = AuthService()
        
        # Create an expired token
        expired_payload = {
            'user_id': 'user123',
            'email': 'test@example.com',
            'exp': datetime.utcnow() - timedelta(hours=1),
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        
        expired_token = jwt.encode(expired_payload, service.jwt_secret, algorithm=service.jwt_algorithm)
        
        with pytest.raises(HTTPException) as exc_info:
            service.verify_jwt_token(expired_token)
        
        assert exc_info.value.status_code == 401
        assert "Token has expired" in str(exc_info.value.detail)
    
    def test_verify_jwt_token_invalid(self):
        """Test JWT token verification with invalid token"""
        service = AuthService()
        
        with pytest.raises(HTTPException) as exc_info:
            service.verify_jwt_token("invalid_token")
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in str(exc_info.value.detail)


class TestAuthEndpoints:
    """Test authentication API endpoints"""
    
    def test_google_login_success(self, client, mock_google_token):
        """Test successful Google OAuth login"""
        response = client.post(
            "/api/auth/google",
            json={"token": "valid_google_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
    
    def test_google_login_invalid_token(self, client):
        """Test Google OAuth login with invalid token"""
        with patch.object(auth_service, 'verify_google_token') as mock_verify:
            mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid Google token")
            
            response = client.post(
                "/api/auth/google",
                json={"token": "invalid_token"}
            )
            
            assert response.status_code == 401
            assert "Invalid Google token" in response.json()["detail"]
    
    def test_get_current_user_success(self, client, authenticated_headers):
        """Test getting current user info with valid token"""
        response = client.get(
            "/api/auth/me",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user info without token"""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 403  # No credentials provided
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user info with invalid token"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "google_client_id_configured" in data
        assert "cors_origins" in data