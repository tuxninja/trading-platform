# Claude AI Assistant Reference

This file contains important context and guidelines for Claude AI to provide optimal assistance with the Trading Platform project.

## Project Overview

The Trading Platform is a comprehensive web application that combines:
- **React Frontend** with Google OAuth authentication
- **FastAPI Backend** with SQLite database
- **AWS Infrastructure** managed by Terraform
- **Docker Containerization** for deployment
- **GitHub Actions** for CI/CD

## Critical System Context

### Architecture
```
Frontend (React) → Backend (FastAPI) → Database (SQLite)
     ↓
Google OAuth → AWS EC2 → Docker Containers
```

### Key Technologies
- **Frontend**: React 18, Tailwind CSS, @react-oauth/google
- **Backend**: FastAPI, SQLAlchemy, Uvicorn, Gunicorn
- **Database**: SQLite (development), PostgreSQL-ready
- **Infrastructure**: AWS EC2, ECR, Route53, Security Groups
- **Deployment**: Docker Compose, GitHub Actions, Terraform

### Environment Setup
- **Development**: Local with virtual environments
- **Production**: AWS EC2 with Docker containers
- **Domain**: divestifi.com (HTTP, no HTTPS currently)

## Common Issues & Solutions

### 1. Google OAuth Problems
**Most Common**: CORS configuration issues

**Key Points**:
- Frontend needs `REACT_APP_GOOGLE_CLIENT_ID` at **build time**
- Backend CORS must include exact domain (no IP addresses)
- Google Console must have authorized JavaScript origins
- Environment variables must match between frontend/backend

**Debug Commands**:
```bash
# Test CORS
curl -X OPTIONS http://domain:8000/api/auth/google -H "Origin: http://domain"

# Check client ID in container
docker exec container env | grep GOOGLE_CLIENT_ID
```

### 2. Deployment Issues
**Most Common**: GitHub Actions SSH connectivity

**Key Points**:
- GitHub Actions uses dynamic IP ranges
- Security group needs broad CIDR blocks or 0.0.0.0/0
- ECR authentication can fail, use legacy method as fallback
- Container port mapping: backend needs `"8000:8000"`

**Recovery Commands**:
```bash
# Manual deployment
ssh ec2-user@ip "cd /opt/trading && docker-compose -f docker-compose.prod.yml up -d"

# Fix security group
aws ec2 authorize-security-group-ingress --group-id sg-xxx --protocol tcp --port 22 --cidr 0.0.0.0/0
```

### 3. CORS Configuration
**Most Common**: Backend hardcoded CORS origins

**Key Points**:
- Backend `config.py` may have hardcoded CORS_ORIGINS list
- Must read from environment variable for flexibility
- Needs both HTTP and HTTPS versions of domain
- Localhost variants for development

**Fix Pattern**:
```python
# backend/config.py
CORS_ORIGINS: list = [
    origin.strip() 
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
```

## File Structure Reference

### Critical Files
```
├── backend/
│   ├── config.py          # Environment & CORS configuration
│   ├── main.py            # FastAPI app & routes
│   ├── auth.py            # Google OAuth handling
│   └── .env               # Backend environment variables
├── frontend/
│   ├── Dockerfile         # React build with env vars
│   ├── .env.local         # Frontend environment variables
│   └── src/
│       └── components/GoogleLogin.js  # OAuth component
├── terraform/
│   ├── main.tf            # AWS infrastructure
│   ├── variables.tf       # Terraform variables
│   └── terraform.tfvars   # Configuration values
├── docker-compose.prod.yml # Production container config
└── .github/workflows/
    ├── deploy.yml         # Main deployment workflow
    └── infrastructure.yml # Terraform deployment (disabled)
```

### Environment Variables
**Frontend (.env.local)**:
```bash
REACT_APP_GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
REACT_APP_API_URL=http://divestifi.com:8000
```

**Backend (.env)**:
```bash
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
CORS_ORIGINS=http://localhost:3000,http://divestifi.com,https://divestifi.com
DATABASE_URL=sqlite:///data/trading.db
NEWS_API_KEY=xxx
ALPHA_VANTAGE_KEY=xxx
SECRET_KEY=xxx
```

**Production (.env on EC2)**:
```bash
DOMAIN_NAME=divestifi.com
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
# Same as backend .env but for production
```

## Development Workflow

### Starting Development
```bash
# Backend
cd backend && source venv/bin/activate && python main.py

# Frontend  
cd frontend && npm start
```

### Testing OAuth Flow
1. Ensure Google Cloud Console has `http://localhost:3000` authorized
2. Both frontend and backend have same GOOGLE_CLIENT_ID
3. Backend includes `http://localhost:3000` in CORS_ORIGINS
4. Test: click "Sign in with Google" → should redirect to dashboard

### Deployment Process
1. **Code changes** → Push to main branch
2. **GitHub Actions** → Builds Docker images, pushes to ECR
3. **SSH to EC2** → Pulls images, updates containers
4. **Health checks** → Verifies deployment success

## Troubleshooting Guidelines

### When User Reports "Login Failed"
1. **Check CORS first**: Most common issue
2. **Verify client ID**: Check environment variables in containers
3. **Test API connectivity**: curl the backend from frontend domain
4. **Check Google Console**: Authorized origins must match exactly

### When Deployment Fails
1. **SSH connectivity**: Check security group allows GitHub Actions
2. **ECR authentication**: Try legacy method if modern fails  
3. **Container health**: Check logs for startup issues
4. **Port mapping**: Ensure backend exposes port 8000 externally

### When "Network Error" Occurs
1. **Frontend API URL**: Must match backend location
2. **CORS preflight**: Should return 200, not 400
3. **Port accessibility**: Backend must be reachable on port 8000
4. **Container networking**: Check docker-compose port mappings

## Code Patterns

### Adding Environment Variables
```python
# backend/config.py
NEW_VAR: str = os.getenv("NEW_VAR", "default_value")
```

```javascript
// frontend - must start with REACT_APP_
const newVar = process.env.REACT_APP_NEW_VAR;
```

### CORS Updates
```python
# Always include localhost for development
CORS_ORIGINS = [
    "http://localhost:3000",      # Development
    "http://domain.com",          # Production HTTP
    "https://domain.com"          # Production HTTPS (future)
]
```

### Docker Environment Passing
```yaml
# docker-compose.prod.yml
services:
  backend:
    environment:
      - NEW_VAR=${NEW_VAR:-default}
  frontend:
    environment:  
      - REACT_APP_NEW_VAR=${NEW_VAR:-default}
```

## Infrastructure Context

### AWS Resources
- **EC2 Instance**: t3.small in us-east-1
- **Security Group**: Allows 22 (SSH), 80 (HTTP), 8000 (API), 443 (HTTPS)
- **Elastic IP**: 98.85.193.239 → divestifi.com
- **ECR Repositories**: trading-platform-frontend, trading-platform-backend
- **Route53**: DNS management for divestifi.com

### GitHub Secrets
```
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
EC2_HOST=98.85.193.239
EC2_SSH_PRIVATE_KEY=xxx
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
# ... other secrets
```

## Communication Guidelines

### When Helping with Issues
1. **Ask for specific error messages** rather than "it doesn't work"
2. **Check logs first**: docker-compose logs, browser dev tools
3. **Test systematically**: Start with simple connectivity tests
4. **Provide debug commands**: Give exact curl/docker commands to run
5. **Explain root cause**: Help user understand why issue occurred

### When Making Changes
1. **Explain impact**: What will this change affect?
2. **Provide rollback**: How to undo if something breaks?
3. **Test instructions**: How to verify the fix worked?
4. **Update documentation**: Keep this file and docs/ current

### Code Suggestions
1. **Follow existing patterns**: Match current code style
2. **Consider environment**: Development vs production differences  
3. **Include error handling**: Anticipate failure modes
4. **Add logging**: Help with future debugging

## Success Patterns

### What Works Well
- **Systematic debugging**: Check CORS → environment → connectivity
- **Manual deployment**: When GitHub Actions fails, deploy directly
- **Legacy fallbacks**: Keep older methods for ECR/SSH as backup
- **Comprehensive logging**: Detailed logs help identify issues quickly

### Best Practices
- **Test locally first**: Verify changes work in development
- **One change at a time**: Easier to isolate issues
- **Document weird fixes**: Add to troubleshooting guide
- **Keep backups**: Important configs and database dumps

## Recent Issues & Resolutions

### Google OAuth "invalid_client" (Resolved)
- **Cause**: GOOGLE_CLIENT_ID not reaching frontend build
- **Solution**: Fixed environment variable passing in Dockerfile and docker-compose
- **Prevention**: Always verify env vars in running containers

### CORS "Disallowed origin" (Resolved)  
- **Cause**: Backend config.py had hardcoded CORS origins
- **Solution**: Updated to read from environment variable
- **Prevention**: Use environment variables for all configuration

### GitHub Actions SSH timeout (Ongoing)
- **Cause**: Dynamic GitHub Actions IP ranges not in security group
- **Workaround**: Manual deployment process works
- **Future**: Consider GitHub-hosted runners or VPN solution

## Future Improvements

### Documentation
- Add visual architecture diagrams
- Create video setup walkthroughs  
- Interactive troubleshooting guide
- API testing playground

### Development Experience
- Docker development environment
- Automated testing in CI/CD
- Development seed data
- Local HTTPS setup guide

### Production
- HTTPS configuration
- Database backups automation
- Monitoring and alerting
- Auto-scaling considerations

---

**Remember**: The Trading Platform is complex but well-documented. Most issues have been encountered before. Start with the basics (CORS, environment variables, connectivity) and work systematically through the troubleshooting guide.

**Golden Rule**: When in doubt, check the logs and test the simplest thing first! 🚀

---

# Development & Coding Guidelines

## Core Development Principles

### 1. File Management & Safety
- **NEVER** create files unless absolutely necessary - always prefer editing existing files
- **ALWAYS** read files before editing to understand context, patterns, and existing architecture
- **FOLLOW** existing code conventions, naming patterns, and architectural decisions
- **PRESERVE** existing functionality while making targeted improvements
- **BACKUP** critical configurations and database state before major changes

### 2. Task Management & Focus
- **USE** TodoWrite tool for all complex multi-step tasks to track progress systematically
- **FOCUS** on one task at a time - mark as in_progress when starting, completed when finished
- **PRIORITIZE** critical user-reported bugs over feature development
- **VERIFY** fixes work end-to-end before moving to next task
- **DOCUMENT** solutions for future reference

### 3. API & Data Integrity
- **ELIMINATE** all mock data - only use real market data with proper fallbacks
- **IMPLEMENT** robust rate limiting (3.0s for market APIs, 2.0s for news APIs)
- **CACHE** market data appropriately (4 hours normal, 24 hours during API issues)
- **PRECISION** format all financial data to exactly 2 decimal places
- **FALLBACK** gracefully to alternative data sources when primary APIs fail
- **VALIDATE** all inputs and provide meaningful error messages

### 4. Database Best Practices  
- **MIGRATIONS** always create and test database schema changes
- **RELATIONSHIPS** properly define foreign keys and maintain referential integrity
- **TRANSACTIONS** use database transactions for multi-step operations
- **CLEANUP** implement automatic cleanup for stale data (OPEN trades > 24 hours)
- **INDEXES** ensure proper indexing on frequently queried columns

### 5. Frontend UX Excellence
- **GRANULAR LOADING** implement per-item loading states, not global ones
- **VISUAL FEEDBACK** provide clear indication of which specific items are being processed
- **ERROR CLARITY** show specific, actionable error messages with context
- **CACHE INVALIDATION** properly invalidate React Query cache after mutations
- **CONSISTENCY** maintain uniform styling and interaction patterns across components

## Recent Critical Fixes & Patterns

### Market Data API Fix
```python
# WRONG - Missing database session
@app.get("/api/market-data/{symbol}")
async def get_market_data(symbol: str, days: int = 30):
    return data_service.get_market_data(symbol, days)

# CORRECT - Include database dependency
@app.get("/api/market-data/{symbol}")  
async def get_market_data(symbol: str, days: int = 30, db: Session = Depends(get_db)):
    return data_service.get_market_data(symbol, days, db)
```

### Sentiment Analysis Rate Limiting
```python
# WRONG - Hard failure on rate limits
if response.status_code == 429:
    raise APIRateLimitError("News API rate limit exceeded")

# CORRECT - Automatic fallback
if response.status_code == 429:
    self.logger.warning(f"News API rate limited for {symbol}, switching to alternative")
    return self._get_alternative_news_sentiment(symbol)
```

### Per-Item Loading States  
```javascript
// WRONG - Global loading affects all items
disabled={analyzeSentimentMutation.isLoading}
{analyzeSentimentMutation.isLoading ? 'Analyzing...' : 'Refresh Analysis'}

// CORRECT - Per-item loading state
const [analyzingStock, setAnalyzingStock] = useState(null);
disabled={analyzingStock === item.symbol}
{analyzingStock === item.symbol ? 'Analyzing...' : 'Refresh Analysis'}
```

### Price Display Precision
```javascript
// WRONG - Shows long floating point decimals
${stock.current_price}

// CORRECT - Exactly 2 decimal places
${parseFloat(stock.current_price || 0).toFixed(2)}
```

## Error Handling Patterns

### Backend Service Layer
```python
def service_method(self, db: Session, symbol: str) -> Dict:
    try:
        # Rate limiting for external APIs
        self._rate_limit()
        
        # Primary data source
        result = primary_api_call(symbol)
        
        if "error" in result:
            # Fallback to alternative source
            result = alternative_api_call(symbol)
            
        return result
        
    except SpecificAPIError as e:
        self.logger.warning(f"API error for {symbol}: {str(e)}")
        return self._fallback_method(symbol)
    except Exception as e:  
        self.logger.error(f"Unexpected error for {symbol}: {str(e)}")
        raise ServiceException(f"Service failed for {symbol}")
```

### Frontend Mutation Pattern
```javascript
const mutation = useMutation(
  (data) => api.post('/endpoint', data),
  {
    onSuccess: (result, variables) => {
      // Clear local loading state
      setLoadingItem(null);
      // Invalidate relevant queries  
      queryClient.invalidateQueries('relevant-data');
      // Show success with context
      toast.success(`Operation completed for ${variables.symbol}!`);
    },
    onError: (error, variables) => {
      // Clear local loading state
      setLoadingItem(null);
      // Show specific error
      toast.error(error.response?.data?.detail || `Operation failed for ${variables.symbol}`);
    }
  }
);
```

## Testing & Verification Patterns

### API Testing
```bash
# Test endpoint with authentication
curl -X GET "http://localhost:8000/api/endpoint" \
  -H "Authorization: Bearer test-token" 2>/dev/null | jq '.'

# Test bulk operations
curl -X POST "http://localhost:8000/api/bulk-endpoint" \
  -H "Content-Type: application/json" \
  -d '{"items": ["AAPL", "GOOGL"]}' 2>/dev/null | jq '.successful, .failed'

# Test with rate limiting  
curl -X POST "http://localhost:8000/api/sentiment" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL"], "force_refresh": true}'
```

### Database Verification
```python
# Check data consistency
python -c "
import sqlite3
conn = sqlite3.connect('trading_app.db')
cursor = conn.cursor()
cursor.execute('SELECT symbol, COUNT(*) FROM table_name GROUP BY symbol')
print(cursor.fetchall())
conn.close()
"
```

## System Architecture Patterns

### Service Dependencies
```
Frontend (React) 
    ↓ API calls
Backend (FastAPI)
    ↓ Service layer
Data Services → External APIs (Yahoo Finance, News API)
    ↓ Caching
Database (SQLite) ← Scheduled cleanup tasks
```

### Data Flow Pattern
1. **User Action** → Frontend component  
2. **API Call** → Backend endpoint with authentication
3. **Service Method** → Business logic with error handling
4. **External API** → Data fetching with rate limiting & fallbacks
5. **Database Cache** → Store results with TTL
6. **Response** → Frontend with loading states & error handling

## Performance & Reliability

### Caching Strategy
- **Market Data**: 4-hour cache, 24-hour during API issues
- **Sentiment Data**: Fresh analysis on demand, cached results
- **User Data**: Cache with React Query, invalidate on mutations
- **Static Data**: Long-term cache with version invalidation

### Rate Limiting Implementation
```python
def _rate_limit(self, api_type: str = "default") -> None:
    rate_limit = config.API_RATE_LIMIT if api_type == "default" else config.NEWS_API_RATE_LIMIT
    elapsed = time.time() - self.last_api_call
    if elapsed < rate_limit:
        sleep_time = rate_limit - elapsed
        time.sleep(sleep_time)
    self.last_api_call = time.time()
```

### Automatic Cleanup
```python
# Scheduled task runs every 2 hours on weekdays
@scheduler.scheduled_job(CronTrigger(minute="0", hour="*/2", day_of_week="mon-fri"))
def cleanup_stale_trades():
    # Auto-close OPEN trades older than 24 hours
    # Free up capital for new trading opportunities
    # Log results for monitoring
```

## Monitoring & Debugging

### Key Metrics to Track
- **API Response Times** - Keep under 2 seconds
- **Market Data Accuracy** - All prices current and precise (2 decimals)
- **Sentiment Analysis Success Rate** - Monitor fallback usage
- **Trade Execution Success** - Track OPEN → CLOSED transitions
- **System Health** - Automated cleanup effectiveness

### Debug Commands
```bash
# Check service health
curl -X GET "http://localhost:8000/docs" 

# Monitor API performance
tail -f backend_logs.log | grep -E "Response:|ERROR:"

# Check database state  
sqlite3 trading_app.db ".tables" ".schema trades"

# Test rate limiting
time curl -X POST "http://localhost:8000/api/test-endpoint"
```

## Success Metrics

### Code Quality Indicators
- ✅ **No Mock Data** - All displayed data comes from real sources
- ✅ **Graceful Failures** - APIs fallback instead of breaking
- ✅ **Consistent UX** - Loading states and errors are clear and specific
- ✅ **Data Integrity** - Financial data always shows proper precision
- ✅ **Performance** - Response times under 2 seconds, automatic cleanup working

### User Experience Indicators  
- ✅ **Accurate Data** - Market prices match real-world values
- ✅ **Reliable Features** - Sentiment analysis and trade management work consistently
- ✅ **Clear Feedback** - Users understand what's happening and why
- ✅ **Capital Efficiency** - No stuck trades preventing new operations
- ✅ **System Trust** - Transparent operation with visible results

---

**Development Golden Rules**:
1. **Read First, Code Second** - Understand existing patterns before changing them
2. **Test Locally, Deploy Safely** - Verify fixes work before deployment
3. **One Task, Complete** - Finish current work before starting new features
4. **Real Data Only** - Eliminate mock data and approximations
5. **User-Centric UX** - Every interaction should be clear and predictable

**Remember**: This trading platform handles real financial data and user capital. Precision, reliability, and clear communication are paramount. When in doubt, err on the side of caution and thorough testing! 🎯