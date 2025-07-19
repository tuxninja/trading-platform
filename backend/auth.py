from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.auth.transport import requests
from google.oauth2 import id_token
import jwt
from datetime import datetime, timedelta
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.jwt_secret = os.getenv("JWT_SECRET", "your-secret-key-change-this")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = 24
        
        if not self.google_client_id:
            logger.warning("GOOGLE_CLIENT_ID not set - Google OAuth will not work")
    
    def verify_google_token(self, token: str) -> dict:
        """Verify Google OAuth token and return user info"""
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), self.google_client_id)
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            return {
                'user_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo.get('name', ''),
                'picture': idinfo.get('picture', ''),
                'verified_email': idinfo.get('email_verified', False)
            }
        except ValueError as e:
            logger.error(f"Invalid Google token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token"
            )
    
    def create_jwt_token(self, user_data: dict) -> str:
        """Create JWT token for authenticated user"""
        expire = datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours)
        payload = {
            'user_id': user_data['user_id'],
            'email': user_data['email'],
            'name': user_data['name'],
            'exp': expire,
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_jwt_token(self, token: str) -> dict:
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

auth_service = AuthService()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    return auth_service.verify_jwt_token(token)

def optional_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[dict]:
    """Optional authentication dependency"""
    if credentials is None:
        return None
    
    try:
        return auth_service.verify_jwt_token(credentials.credentials)
    except HTTPException:
        return None