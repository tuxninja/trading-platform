# Configuration Guide

Comprehensive guide for configuring the Trading Sentiment Analysis Platform for different environments and use cases.

## 📋 Table of Contents

- [Overview](#overview)
- [Environment Variables](#environment-variables)
- [Configuration Files](#configuration-files)
- [Environment-Specific Setup](#environment-specific-setup)
- [API Keys & External Services](#api-keys--external-services)
- [Database Configuration](#database-configuration)
- [Scheduler Configuration](#scheduler-configuration)
- [Frontend Configuration](#frontend-configuration)
- [Production Deployment](#production-deployment)
- [Security Configuration](#security-configuration)
- [Performance Tuning](#performance-tuning)

## 🎯 Overview

The Trading Platform uses environment-based configuration with sensible defaults for rapid development setup. Configuration is managed through:

- Environment variables (`.env` files)
- Configuration classes (`config.py`)
- Runtime settings
- External service integrations

## 🌍 Environment Variables

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# =============================================================================
# TRADING PLATFORM CONFIGURATION
# =============================================================================

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
DATABASE_URL=sqlite:///trading.db
# For PostgreSQL: DATABASE_URL=postgresql://user:password@localhost:5432/trading
# For MySQL: DATABASE_URL=mysql://user:password@localhost:3306/trading

# -----------------------------------------------------------------------------
# Trading Configuration
# -----------------------------------------------------------------------------
# Initial portfolio balance (USD)
INITIAL_BALANCE=100000.0

# Maximum position size as percentage of portfolio (0.0 to 1.0)
MAX_POSITION_SIZE=0.05

# Sentiment threshold for trading signals (-1.0 to 1.0)
SENTIMENT_THRESHOLD=0.1

# Maximum trades per day
MAX_TRADES_PER_DAY=10

# Minimum confidence score for recommendations (0.0 to 1.0)
MIN_RECOMMENDATION_CONFIDENCE=0.6

# -----------------------------------------------------------------------------
# Market Hours & Scheduling
# -----------------------------------------------------------------------------
# Market hours (24-hour format HH:MM)
MARKET_OPEN_TIME=09:30
MARKET_CLOSE_TIME=16:00

# Scheduled task times
SENTIMENT_ANALYSIS_TIME=10:00
STRATEGY_EXECUTION_TIME=10:30

# Data collection intervals (minutes)
HOURLY_DATA_COLLECTION=60
REALTIME_UPDATE_INTERVAL=5

# -----------------------------------------------------------------------------
# External API Keys (Optional)
# -----------------------------------------------------------------------------
# News API (https://newsapi.org/)
NEWS_API_KEY=your_news_api_key_here

# Alpha Vantage (https://www.alphavantage.co/)
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here

# Financial Modeling Prep (https://financialmodelingprep.com/)
FMP_API_KEY=your_fmp_api_key_here

# Polygon.io (https://polygon.io/)
POLYGON_API_KEY=your_polygon_api_key_here

# -----------------------------------------------------------------------------
# CORS & Security
# -----------------------------------------------------------------------------
# Allowed origins for CORS (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://yourdomain.com

# API rate limiting
RATE_LIMIT_PER_MINUTE=100

# Session secret (for future authentication)
SECRET_KEY=your-secret-key-change-in-production

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log file path
LOG_FILE=trading.log

# Log to console (true/false)
LOG_TO_CONSOLE=true

# Log format
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# -----------------------------------------------------------------------------
# Performance & Caching
# -----------------------------------------------------------------------------
# Database connection pool size
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0

# Cache TTL (seconds)
STOCK_DATA_CACHE_TTL=300
SENTIMENT_CACHE_TTL=1800

# API request timeouts (seconds)
API_TIMEOUT=30
NEWS_API_TIMEOUT=45

# -----------------------------------------------------------------------------
# Feature Flags
# -----------------------------------------------------------------------------
# Enable/disable features
ENABLE_SCHEDULER=true
ENABLE_AUTO_TRADING=false
ENABLE_MARKET_SCANNER=true
ENABLE_RECOMMENDATIONS=true

# Mock data fallback when APIs fail
USE_MOCK_DATA_FALLBACK=true

# Debug mode (enables additional logging and endpoints)
DEBUG_MODE=false

# -----------------------------------------------------------------------------
# Environment Identifier
# -----------------------------------------------------------------------------
ENVIRONMENT=development
# Options: development, testing, staging, production
```

### Frontend Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
# =============================================================================
# FRONTEND CONFIGURATION
# =============================================================================

# API Configuration
REACT_APP_API_URL=http://localhost:8000

# App Metadata
REACT_APP_APP_NAME=Trading Platform
REACT_APP_VERSION=1.0.0

# Feature Flags
REACT_APP_ENABLE_DEBUG=true
REACT_APP_ENABLE_MOCK_DATA=false

# Chart Configuration
REACT_APP_CHART_REFRESH_INTERVAL=30000
REACT_APP_DEFAULT_CHART_DAYS=30

# UI Configuration
REACT_APP_PAGINATION_SIZE=20
REACT_APP_THEME=default

# Analytics (if using)
REACT_APP_ANALYTICS_ID=your_analytics_id

# Environment
NODE_ENV=development
```

## ⚙️ Configuration Files

### Backend Configuration Class

**File**: `backend/config.py`

```python
import os
from typing import List, Optional
from pydantic import BaseSettings, validator

class Config(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///trading.db"
    
    # Trading Settings
    INITIAL_BALANCE: float = 100000.0
    MAX_POSITION_SIZE: float = 0.05
    SENTIMENT_THRESHOLD: float = 0.1
    MAX_TRADES_PER_DAY: int = 10
    MIN_RECOMMENDATION_CONFIDENCE: float = 0.6
    
    # Market Hours
    MARKET_OPEN_TIME: str = "09:30"
    MARKET_CLOSE_TIME: str = "16:00"
    SENTIMENT_ANALYSIS_TIME: str = "10:00"
    STRATEGY_EXECUTION_TIME: str = "10:30"
    
    # API Keys
    NEWS_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_KEY: Optional[str] = None
    FMP_API_KEY: Optional[str] = None
    POLYGON_API_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "trading.log"
    LOG_TO_CONSOLE: bool = True
    
    # Performance
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 0
    STOCK_DATA_CACHE_TTL: int = 300
    API_TIMEOUT: int = 30
    
    # Feature Flags
    ENABLE_SCHEDULER: bool = True
    ENABLE_AUTO_TRADING: bool = False
    ENABLE_MARKET_SCANNER: bool = True
    USE_MOCK_DATA_FALLBACK: bool = True
    
    # Environment
    ENVIRONMENT: str = "development"
    
    @validator('CORS_ORIGINS', pre=True)
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(',')]
        return v
    
    @validator('MAX_POSITION_SIZE')
    def validate_position_size(cls, v):
        if not 0 < v <= 1:
            raise ValueError('MAX_POSITION_SIZE must be between 0 and 1')
        return v
    
    class Config:
        env_file = '.env'
        case_sensitive = True

# Global configuration instance
config = Config()
```

### Frontend Configuration

**File**: `frontend/src/config.js`

```javascript
const config = {
  // API Configuration
  API_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  
  // App Settings
  APP_NAME: process.env.REACT_APP_APP_NAME || 'Trading Platform',
  VERSION: process.env.REACT_APP_VERSION || '1.0.0',
  
  // Feature Flags
  ENABLE_DEBUG: process.env.REACT_APP_ENABLE_DEBUG === 'true',
  ENABLE_MOCK_DATA: process.env.REACT_APP_ENABLE_MOCK_DATA === 'true',
  
  // Chart Settings
  CHART_REFRESH_INTERVAL: parseInt(process.env.REACT_APP_CHART_REFRESH_INTERVAL) || 30000,
  DEFAULT_CHART_DAYS: parseInt(process.env.REACT_APP_DEFAULT_CHART_DAYS) || 30,
  
  // UI Settings
  PAGINATION_SIZE: parseInt(process.env.REACT_APP_PAGINATION_SIZE) || 20,
  THEME: process.env.REACT_APP_THEME || 'default',
  
  // Environment
  ENVIRONMENT: process.env.NODE_ENV || 'development',
  IS_DEVELOPMENT: process.env.NODE_ENV === 'development',
  IS_PRODUCTION: process.env.NODE_ENV === 'production',
};

export default config;
```

## 🏗️ Environment-Specific Setup

### Development Environment

```bash
# Backend .env
ENVIRONMENT=development
DATABASE_URL=sqlite:///trading_dev.db
DEBUG_MODE=true
LOG_LEVEL=DEBUG
ENABLE_AUTO_TRADING=false
USE_MOCK_DATA_FALLBACK=true

# Frontend .env.local  
NODE_ENV=development
REACT_APP_ENABLE_DEBUG=true
```

### Testing Environment

```bash
# Backend .env.test
ENVIRONMENT=testing
DATABASE_URL=sqlite:///trading_test.db
DEBUG_MODE=true
LOG_LEVEL=WARNING
ENABLE_SCHEDULER=false
USE_MOCK_DATA_FALLBACK=true

# Frontend .env.test
NODE_ENV=test
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENABLE_MOCK_DATA=true
```

### Staging Environment

```bash
# Backend .env.staging
ENVIRONMENT=staging
DATABASE_URL=postgresql://user:pass@staging-db:5432/trading
DEBUG_MODE=false
LOG_LEVEL=INFO
ENABLE_AUTO_TRADING=false
USE_MOCK_DATA_FALLBACK=false

# Required API keys for staging
NEWS_API_KEY=staging_news_api_key
ALPHA_VANTAGE_KEY=staging_alpha_vantage_key

# Frontend .env.staging
NODE_ENV=production
REACT_APP_API_URL=https://api-staging.trading-platform.com
REACT_APP_ENABLE_DEBUG=false
```

### Production Environment

```bash
# Backend .env.production
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@prod-db:5432/trading
DEBUG_MODE=false
LOG_LEVEL=WARNING
ENABLE_AUTO_TRADING=true
USE_MOCK_DATA_FALLBACK=false

# Production API keys
NEWS_API_KEY=prod_news_api_key
ALPHA_VANTAGE_KEY=prod_alpha_vantage_key
SECRET_KEY=super-secret-production-key

# Frontend .env.production
NODE_ENV=production
REACT_APP_API_URL=https://api.trading-platform.com
REACT_APP_ENABLE_DEBUG=false
```

## 🔑 API Keys & External Services

### News API (newsapi.org)

```bash
NEWS_API_KEY=your_api_key_here
```

**Features:**
- Real-time financial news
- Historical news articles
- News source filtering

**Usage Limits:**
- Free tier: 1,000 requests/day
- Paid tiers: Up to 250,000 requests/day

### Alpha Vantage (alphavantage.co)

```bash
ALPHA_VANTAGE_KEY=your_api_key_here
```

**Features:**
- Stock prices and technical indicators
- Economic indicators
- Forex and cryptocurrency data

**Usage Limits:**
- Free tier: 5 API requests/minute, 500 requests/day
- Premium tiers: Higher limits and real-time data

### Financial Modeling Prep

```bash
FMP_API_KEY=your_api_key_here
```

**Features:**
- Comprehensive financial data
- Company fundamentals
- Real-time quotes

### Polygon.io

```bash
POLYGON_API_KEY=your_api_key_here
```

**Features:**
- Real-time market data
- Historical data
- Options and crypto data

### API Key Security

```bash
# Use environment-specific keys
NEWS_API_KEY_DEV=dev_key
NEWS_API_KEY_PROD=prod_key

# Rotate keys regularly
API_KEY_ROTATION_DATE=2025-12-31

# Monitor usage
API_USAGE_ALERT_THRESHOLD=80
```

## 🗄️ Database Configuration

### SQLite (Development)

```bash
DATABASE_URL=sqlite:///trading.db

# SQLite-specific settings
SQLITE_TIMEOUT=30
SQLITE_JOURNAL_MODE=WAL
SQLITE_SYNCHRONOUS=NORMAL
```

### PostgreSQL (Production)

```bash
DATABASE_URL=postgresql://username:password@hostname:5432/database_name

# Connection pool settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# SSL settings (production)
DB_SSL_MODE=require
DB_SSL_CERT_PATH=/path/to/client-cert.pem
DB_SSL_KEY_PATH=/path/to/client-key.pem
DB_SSL_CA_PATH=/path/to/ca-cert.pem
```

### Database Performance Tuning

```bash
# Query optimization
DB_QUERY_TIMEOUT=30
DB_STATEMENT_TIMEOUT=60

# Connection management
DB_CONNECTION_LIFETIME=3600
DB_CONNECTION_MAX_AGE=7200

# Monitoring
DB_LOG_SLOW_QUERIES=true
DB_SLOW_QUERY_THRESHOLD=1000
```

## ⏰ Scheduler Configuration

### Basic Scheduler Settings

```bash
# Enable/disable scheduler
ENABLE_SCHEDULER=true

# Market hours for data collection
MARKET_OPEN_TIME=09:30
MARKET_CLOSE_TIME=16:00

# Daily scheduled tasks
SENTIMENT_ANALYSIS_TIME=10:00
STRATEGY_EXECUTION_TIME=10:30

# Collection intervals
HOURLY_DATA_COLLECTION=60
REALTIME_UPDATE_INTERVAL=5
```

### Advanced Scheduler Configuration

**File**: `backend/scheduler_config.py`

```python
class SchedulerConfig:
    # Task scheduling
    TASKS = {
        'market_data_collection': {
            'schedule': 'every().hour.at(":00")',
            'enabled': True,
            'timeout': 300
        },
        'sentiment_analysis': {
            'schedule': 'every().day.at("10:00")',
            'enabled': True,
            'timeout': 600
        },
        'strategy_execution': {
            'schedule': 'every().day.at("10:30")',
            'enabled': True,
            'timeout': 180
        },
        'portfolio_metrics': {
            'schedule': 'every().day.at("16:30")',
            'enabled': True,
            'timeout': 60
        }
    }
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 30  # seconds
    
    # Concurrency
    MAX_CONCURRENT_TASKS = 5
    
    # Health monitoring
    HEALTH_CHECK_INTERVAL = 300  # seconds
    TASK_TIMEOUT_THRESHOLD = 900  # 15 minutes
```

## 🎨 Frontend Configuration

### React Configuration

**File**: `frontend/src/config/app.js`

```javascript
export const appConfig = {
  // API settings
  api: {
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
    timeout: 30000,
    retries: 3,
    retryDelay: 1000,
  },
  
  // Chart configuration
  charts: {
    refreshInterval: parseInt(process.env.REACT_APP_CHART_REFRESH_INTERVAL) || 30000,
    defaultTimeframe: process.env.REACT_APP_DEFAULT_CHART_DAYS || 30,
    colors: {
      primary: '#3B82F6',
      success: '#10B981',
      danger: '#EF4444',
      warning: '#F59E0B',
    },
    animations: {
      duration: 300,
      easing: 'ease-in-out',
    },
  },
  
  // Table configuration
  tables: {
    pageSize: parseInt(process.env.REACT_APP_PAGINATION_SIZE) || 20,
    sortable: true,
    filterable: true,
  },
  
  // UI preferences
  ui: {
    theme: process.env.REACT_APP_THEME || 'light',
    sidebar: {
      collapsible: true,
      defaultExpanded: true,
    },
    notifications: {
      duration: 5000,
      position: 'top-right',
    },
  },
  
  // Feature flags
  features: {
    enableDebug: process.env.REACT_APP_ENABLE_DEBUG === 'true',
    enableMockData: process.env.REACT_APP_ENABLE_MOCK_DATA === 'true',
    enableWebSocket: process.env.REACT_APP_ENABLE_WEBSOCKET === 'true',
    enablePWA: process.env.REACT_APP_ENABLE_PWA === 'true',
  },
};
```

### Build Configuration

**File**: `frontend/.env.production`

```bash
# Build optimization
GENERATE_SOURCEMAP=false
INLINE_RUNTIME_CHUNK=false

# Bundle analysis
ANALYZE_BUNDLE=false

# Performance monitoring
REACT_APP_SENTRY_DSN=your_sentry_dsn

# CDN configuration
PUBLIC_URL=https://cdn.trading-platform.com

# Service worker
REACT_APP_SW_UPDATE_POPUP=true
```

## 🚀 Production Deployment

### Docker Configuration

**File**: `backend/Dockerfile`

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Environment variables
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Run application
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/trading
    depends_on:
      - db
    ports:
      - "8000:8000"
    volumes:
      - ./backend/.env:/app/.env

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: trading
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Environment Variables for Production

```bash
# Production .env file
DATABASE_URL=postgresql://user:pass@db-host:5432/trading_prod
SECRET_KEY=super-secret-production-key-change-me
ENVIRONMENT=production
DEBUG_MODE=false
LOG_LEVEL=WARNING
CORS_ORIGINS=https://trading-platform.com,https://app.trading-platform.com

# Performance settings
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=10
API_TIMEOUT=60

# Security settings
RATE_LIMIT_PER_MINUTE=60
SESSION_TIMEOUT=1800

# Monitoring
SENTRY_DSN=your_sentry_dsn
NEW_RELIC_LICENSE_KEY=your_new_relic_key
```

## 🔒 Security Configuration

### API Security

```bash
# CORS configuration
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
CORS_ALLOW_CREDENTIALS=true
CORS_MAX_AGE=86400

# Rate limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000

# Request size limits
MAX_REQUEST_SIZE=10485760  # 10MB
MAX_JSON_SIZE=1048576      # 1MB

# Security headers
ENABLE_SECURITY_HEADERS=true
HSTS_MAX_AGE=31536000
CONTENT_TYPE_NOSNIFF=true
X_FRAME_OPTIONS=DENY
```

### Database Security

```bash
# Connection encryption
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Connection limits
DB_MAX_CONNECTIONS=100
DB_CONNECTION_TIMEOUT=30

# Query timeouts
DB_QUERY_TIMEOUT=60
DB_STATEMENT_TIMEOUT=300
```

## ⚡ Performance Tuning

### Backend Performance

```bash
# Worker processes
GUNICORN_WORKERS=4
GUNICORN_WORKER_CLASS=uvicorn.workers.UvicornWorker
GUNICORN_MAX_REQUESTS=1000
GUNICORN_MAX_REQUESTS_JITTER=50

# Memory settings
GUNICORN_WORKER_MEMORY_LIMIT=512M
PYTHON_GC_THRESHOLD=700,10,10

# Caching
CACHE_TTL=300
CACHE_MAX_SIZE=1000
ENABLE_RESPONSE_CACHING=true

# Database optimization
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0
DB_POOL_PRE_PING=true
DB_POOL_RECYCLE=3600
```

### Frontend Performance

```bash
# Build optimization
REACT_APP_BUNDLE_ANALYZER=false
REACT_APP_SERVICE_WORKER=true
REACT_APP_CODE_SPLITTING=true

# Runtime optimization
REACT_APP_LAZY_LOADING=true
REACT_APP_IMAGE_OPTIMIZATION=true
REACT_APP_VIRTUAL_SCROLLING=true

# Caching
REACT_APP_CACHE_API_RESPONSES=true
REACT_APP_CACHE_DURATION=300000
```

## 🔧 Configuration Validation

### Validation Script

**File**: `backend/validate_config.py`

```python
#!/usr/bin/env python3
"""Configuration validation script"""

import os
import sys
from config import config

def validate_config():
    """Validate configuration settings"""
    errors = []
    warnings = []
    
    # Required settings
    if not config.DATABASE_URL:
        errors.append("DATABASE_URL is required")
    
    if not config.SECRET_KEY or config.SECRET_KEY == "dev-secret-key-change-in-production":
        if config.ENVIRONMENT == "production":
            errors.append("SECRET_KEY must be set for production")
        else:
            warnings.append("Using default SECRET_KEY (not suitable for production)")
    
    # Range validation
    if not 0 < config.MAX_POSITION_SIZE <= 1:
        errors.append("MAX_POSITION_SIZE must be between 0 and 1")
    
    if not -1 <= config.SENTIMENT_THRESHOLD <= 1:
        errors.append("SENTIMENT_THRESHOLD must be between -1 and 1")
    
    # API keys validation
    if config.ENVIRONMENT == "production":
        if not config.NEWS_API_KEY:
            warnings.append("NEWS_API_KEY not set - using free news sources")
    
    # Database validation
    if config.ENVIRONMENT == "production" and "sqlite" in config.DATABASE_URL:
        warnings.append("Using SQLite in production - consider PostgreSQL")
    
    # Print results
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    if warnings:
        print("⚠️ Configuration Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    print("✅ Configuration validation passed")
    return True

if __name__ == "__main__":
    if not validate_config():
        sys.exit(1)
```

### Usage

```bash
# Validate configuration
python validate_config.py

# Validate before deployment
./deploy.sh --validate-config
```

---

## 📚 Configuration Examples

### Complete Development Setup

```bash
# Backend .env
DATABASE_URL=sqlite:///trading_dev.db
INITIAL_BALANCE=100000.0
MAX_POSITION_SIZE=0.05
MARKET_OPEN_TIME=09:30
MARKET_CLOSE_TIME=16:00
LOG_LEVEL=DEBUG
ENABLE_AUTO_TRADING=false
USE_MOCK_DATA_FALLBACK=true
CORS_ORIGINS=http://localhost:3000

# Frontend .env.local
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENABLE_DEBUG=true
REACT_APP_CHART_REFRESH_INTERVAL=5000
```

### Complete Production Setup

```bash
# Backend .env.production
DATABASE_URL=postgresql://trading_user:secure_password@prod-db:5432/trading
SECRET_KEY=your-super-secret-production-key
INITIAL_BALANCE=100000.0
MAX_POSITION_SIZE=0.03
ENVIRONMENT=production
LOG_LEVEL=WARNING
ENABLE_AUTO_TRADING=true
USE_MOCK_DATA_FALLBACK=false
NEWS_API_KEY=your_production_news_api_key
ALPHA_VANTAGE_KEY=your_production_alpha_vantage_key
CORS_ORIGINS=https://trading-platform.com

# Frontend .env.production
REACT_APP_API_URL=https://api.trading-platform.com
REACT_APP_ENABLE_DEBUG=false
REACT_APP_CHART_REFRESH_INTERVAL=30000
NODE_ENV=production
```

---

For additional configuration help, refer to the main project documentation or open an issue on GitHub.