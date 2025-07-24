# API Connectivity Debugging Guide

## Problem Description
Users are getting "Network Error" when the frontend tries to call the trades API after login. The frontend should be calling `https://divestifi.com/api/trades` and this should be proxied by nginx to the backend container.

## Root Cause Analysis
The issue was in the frontend API configuration where the `REACT_APP_API_URL` was hardcoded to use `https://divestifi.com` in the Docker build, causing the frontend to make absolute URL requests instead of relative requests that should be handled by the nginx proxy.

## Fixes Applied

### 1. Frontend API Configuration (`/frontend/src/services/api.js`)
```javascript
// OLD (problematic):
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// NEW (fixed):
const API_BASE_URL = process.env.REACT_APP_API_URL || 
  (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000');
```

### 2. Docker Build Configuration (`/frontend/Dockerfile`)
```dockerfile
# OLD (problematic):
ARG REACT_APP_API_URL=https://divestifi.com

# NEW (fixed):
ARG REACT_APP_API_URL
# Leave REACT_APP_API_URL empty for production to use relative URLs via nginx proxy
ENV REACT_APP_API_URL=${REACT_APP_API_URL:-}
```

### 3. Nginx Proxy Configuration (`/frontend/nginx.conf`)
```nginx
# FIXED: Ensure proper proxy path handling
location /api/ {
    proxy_pass http://trading-backend:8000/api/;
    # ... other proxy settings
}
```

### 4. Production Environment Configuration (`/frontend/.env.production`)
```env
# Use empty API URL for production (relative requests via nginx)
REACT_APP_API_URL=
```

## Debugging Tools Created

### 1. API Debugger Component (`/frontend/src/components/ApiDebugger.js`)
- Access at: `https://divestifi.com/debug` (after login)
- Tests multiple API endpoints and connection methods
- Shows detailed configuration and network information
- Provides troubleshooting recommendations

### 2. Backend Debug Endpoint (`/backend/main.py`)
```python
@app.get("/api/debug/network")
async def network_debug():
    # Returns detailed backend connectivity information
```

### 3. Connectivity Test Script (`/test_api_connectivity.sh`)
```bash
# Run this script to test API connectivity from command line
./test_api_connectivity.sh
```

## Verification Steps

### For Development (localhost)
1. Start services: `docker-compose up`
2. Frontend calls: `http://localhost:8000/api/trades`
3. Access debug page: `http://localhost:3000/debug`

### For Production (divestifi.com)
1. Deploy with: `docker-compose -f docker-compose.prod.yml up`
2. Frontend calls: `/api/trades` (relative URL)
3. Nginx proxies to: `http://trading-backend:8000/api/trades`
4. Access debug page: `https://divestifi.com/debug`

## Testing the Fix

### 1. Manual Browser Testing
```javascript
// Open browser console on https://divestifi.com and test:
fetch('/api/health')
  .then(r => r.json())
  .then(d => console.log('Health check:', d))
  .catch(e => console.error('Error:', e));

fetch('/api/trades')
  .then(r => r.json())
  .then(d => console.log('Trades:', d))
  .catch(e => console.error('Error:', e));
```

### 2. Using the Debug Page
1. Navigate to `https://divestifi.com/debug`
2. Click "Run Network Tests"
3. Review test results and configuration

### 3. Command Line Testing
```bash
# Test external access
curl -v https://divestifi.com/api/health
curl -v https://divestifi.com/api/trades

# Check CORS headers
curl -X OPTIONS -H "Origin: https://divestifi.com" -I https://divestifi.com/api/health
```

## Common Issues and Solutions

### Issue 1: Still getting localhost URLs in production
**Solution**: Rebuild the frontend container with the updated Dockerfile
```bash
docker-compose -f docker-compose.prod.yml build frontend
docker-compose -f docker-compose.prod.yml up -d
```

### Issue 2: CORS errors
**Solution**: Check nginx CORS headers and backend CORS configuration
- Verify `CORS_ORIGINS` in backend includes your domain
- Check nginx is adding CORS headers correctly

### Issue 3: 502 Bad Gateway
**Solution**: Backend container not reachable
- Check backend container is running: `docker ps`
- Check backend logs: `docker-compose logs backend`
- Verify network connectivity between containers

### Issue 4: Authentication errors
**Solution**: Check auth token handling
- Verify `Authorization: Bearer <token>` header is being sent
- Check token is valid and not expired
- Verify backend auth middleware is working

## Environment Variables Checklist

### Development (.env.local)
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_GOOGLE_CLIENT_ID=your_client_id
```

### Production (docker-compose.prod.yml)
```yaml
frontend:
  environment:
    - NODE_ENV=production
    # REACT_APP_API_URL should NOT be set (empty = relative URLs)
    - REACT_APP_GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
```

## Network Flow

### Development
```
Frontend (localhost:3000) 
    → Direct HTTP call to localhost:8000/api/trades 
    → Backend (localhost:8000)
```

### Production
```
Browser (divestifi.com) 
    → Relative call to /api/trades 
    → Nginx (port 80) 
    → Proxy to trading-backend:8000/api/trades 
    → Backend (container port 8000)
```

## Monitoring and Logs

### Backend Logs
```bash
# View backend logs
docker-compose logs -f backend

# Look for request logs like:
# INFO: Request: GET /api/trades
# INFO: Response: 200 - 0.123s
```

### Nginx Logs
```bash
# Access nginx logs (if available)
docker exec trading-frontend cat /var/log/nginx/access.log
docker exec trading-frontend cat /var/log/nginx/error.log
```

### Browser Network Tab
1. Open DevTools → Network tab
2. Try accessing trades page
3. Look for:
   - Request URL (should be relative `/api/trades`)
   - Response status
   - CORS headers
   - Error messages

## Deployment Checklist

- [ ] Frontend Docker image rebuilt with fixed configuration
- [ ] nginx.conf has correct proxy_pass configuration
- [ ] REACT_APP_API_URL is empty in production build
- [ ] Backend CORS_ORIGINS includes production domain
- [ ] Both containers are on the same docker network
- [ ] Backend container is named `trading-backend` (matching nginx proxy)
- [ ] API debug page is accessible at `/debug`
- [ ] All API endpoints return expected responses

## Contact and Support

If issues persist:
1. Check the debug page at `/debug` for detailed diagnostics
2. Run the connectivity test script: `./test_api_connectivity.sh`
3. Review docker container logs for both frontend and backend
4. Test API endpoints directly with curl to isolate the issue