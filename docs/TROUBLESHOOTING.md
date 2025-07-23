# Troubleshooting Guide

This guide covers common issues encountered when developing, deploying, or using the Trading Platform.

## Table of Contents

- [Development Issues](#development-issues)
- [Authentication Problems](#authentication-problems)
- [Database Issues](#database-issues)
- [Deployment Problems](#deployment-problems)
- [API and Network Issues](#api-and-network-issues)
- [Performance Issues](#performance-issues)
- [Docker Issues](#docker-issues)

## Development Issues

### Backend Won't Start

#### "ModuleNotFoundError" Errors

**Symptoms**: 
```bash
ModuleNotFoundError: No module named 'fastapi'
```

**Causes & Solutions**:

1. **Virtual Environment Not Activated**:
   ```bash
   # Activate virtual environment
   cd backend
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   ```

2. **Dependencies Not Installed**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Wrong Python Version**:
   ```bash
   python --version  # Should be 3.9+
   which python      # Should point to venv
   ```

#### "Port Already in Use" Error

**Symptoms**:
```bash
[Errno 48] Address already in use
```

**Solutions**:

1. **Find Process Using Port**:
   ```bash
   # macOS/Linux
   lsof -i :8000
   kill -9 <PID>
   
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

2. **Use Different Port**:
   ```bash
   uvicorn main:app --port 8001
   ```

### Frontend Won't Start

#### "npm start" Fails

**Symptoms**:
```bash
Error: EMFILE: too many open files
```

**Solutions**:

1. **Clear Node Cache**:
   ```bash
   npm cache clean --force
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Increase File Watchers** (Linux):
   ```bash
   echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
   sudo sysctl -p
   ```

#### Build Errors

**Symptoms**:
```bash
Module not found: Can't resolve './component'
```

**Solutions**:

1. **Check Import Paths**:
   ```javascript
   // Correct
   import Component from './components/Component';
   // Incorrect (case sensitive)
   import component from './Components/component';
   ```

2. **Clear React Cache**:
   ```bash
   rm -rf node_modules/.cache
   npm start
   ```

## Authentication Problems

### Google OAuth Issues

#### "OAuth client was not found"

**Symptoms**: Error 401 with "invalid_client" message

**Debugging Steps**:

1. **Check Client ID Configuration**:
   ```bash
   # Frontend environment
   cat frontend/.env.local | grep GOOGLE_CLIENT_ID
   
   # Backend environment  
   cat backend/.env | grep GOOGLE_CLIENT_ID
   ```

2. **Verify Google Cloud Console**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Check "APIs & Services" → "Credentials"
   - Ensure OAuth client exists and is enabled

3. **Check Authorized Origins**:
   - Must include your domain (e.g., `http://divestifi.com`)
   - Cannot use IP addresses
   - Must match exact protocol (http vs https)

#### "Disallowed CORS origin"

**Symptoms**: Network error, CORS policy blocks requests

**Solutions**:

1. **Check Backend CORS Configuration**:
   ```bash
   # Test CORS preflight
   curl -X OPTIONS http://your-domain:8000/api/auth/google \
     -H "Origin: http://your-domain" \
     -H "Access-Control-Request-Method: POST" \
     -v
   ```

2. **Update Backend CORS**:
   ```python
   # backend/config.py
   CORS_ORIGINS: list = [
       "http://localhost:3000",
       "http://your-domain.com",
       "https://your-domain.com"
   ]
   ```

3. **Restart Backend After Changes**:
   ```bash
   # Kill and restart backend
   pkill -f "python main.py"
   python main.py
   ```

#### "Missing required parameter: client_id"

**Symptoms**: Google OAuth shows client_id error

**Root Cause**: React environment variables not set at build time

**Solutions**:

1. **Check Build-Time Variables**:
   ```bash
   # Environment variables must be set when building React
   REACT_APP_GOOGLE_CLIENT_ID=your_client_id npm run build
   ```

2. **For Docker Production**:
   ```dockerfile
   # Dockerfile
   ARG REACT_APP_GOOGLE_CLIENT_ID
   ENV REACT_APP_GOOGLE_CLIENT_ID=$REACT_APP_GOOGLE_CLIENT_ID
   ```

3. **Verify in Browser**:
   ```javascript
   // Browser console
   console.log(process.env.REACT_APP_GOOGLE_CLIENT_ID);
   // Should show your client ID, not undefined
   ```

## Database Issues

### Database Connection Errors

#### "No such file or directory" (SQLite)

**Symptoms**:
```bash
sqlite3.OperationalError: unable to open database file
```

**Solutions**:

1. **Create Database Directory**:
   ```bash
   mkdir -p backend/data
   ```

2. **Initialize Database**:
   ```bash
   cd backend
   python -c "from database import init_db; init_db()"
   ```

3. **Check Permissions**:
   ```bash
   ls -la backend/data/
   chmod 664 backend/data/trading.db
   ```

#### "Database is locked"

**Symptoms**:
```bash
sqlite3.OperationalError: database is locked
```

**Solutions**:

1. **Close All Connections**:
   ```bash
   # Kill backend processes
   pkill -f "python main.py"
   pkill -f "python scheduler.py"
   ```

2. **Remove Lock File**:
   ```bash
   rm backend/data/trading.db-wal
   rm backend/data/trading.db-shm
   ```

### Database Schema Issues

#### "No such table" Errors

**Symptoms**:
```bash
sqlite3.OperationalError: no such table: stocks
```

**Solutions**:

1. **Run Database Migrations**:
   ```bash
   cd backend
   python -c "from database import init_db; init_db()"
   ```

2. **Check Database Schema**:
   ```bash
   sqlite3 backend/data/trading.db
   .tables
   .schema stocks
   ```

## Deployment Problems

### Docker Issues

#### "Build failed" Errors

**Symptoms**:
```bash
ERROR [backend 3/6] RUN pip install -r requirements.txt
```

**Solutions**:

1. **Check Docker Resources**:
   - Increase Docker memory allocation (4GB+)
   - Ensure sufficient disk space

2. **Clear Docker Cache**:
   ```bash
   docker system prune -a
   docker-compose build --no-cache
   ```

3. **Check Requirements File**:
   ```bash
   # Ensure requirements.txt exists and is valid
   cat backend/requirements.txt
   ```

#### Container Health Check Failures

**Symptoms**: Containers showing as "unhealthy"

**Solutions**:

1. **Check Container Logs**:
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   ```

2. **Test Health Endpoints**:
   ```bash
   # Backend health check
   curl http://localhost:8000/
   
   # Frontend health check
   curl http://localhost:80/
   ```

3. **Disable Health Checks Temporarily**:
   ```yaml
   # docker-compose.yml
   services:
     backend:
       # Comment out healthcheck section
       # healthcheck:
       #   test: ["CMD", "curl", "-f", "http://localhost:8000/"]
   ```

### GitHub Actions Deployment Failures

#### SSH Connection Timeouts

**Symptoms**:
```bash
ssh: connect to host xxx.xxx.xxx.xxx port 22: Connection timed out
```

**Solutions**:

1. **Check Security Group Rules**:
   ```bash
   # Allow GitHub Actions IP ranges
   aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx
   ```

2. **Update Security Group**:
   ```bash
   # Add 0.0.0.0/0 temporarily for debugging
   aws ec2 authorize-security-group-ingress \
     --group-id sg-xxxxxxxxx \
     --protocol tcp \
     --port 22 \
     --cidr 0.0.0.0/0
   ```

3. **Verify EC2 Instance**:
   ```bash
   # Check instance is running
   aws ec2 describe-instances --instance-ids i-xxxxxxxxx
   ```

#### ECR Authentication Failures

**Symptoms**:
```bash
Error response from daemon: pull access denied
```

**Solutions**:

1. **Login to ECR**:
   ```bash
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin \
     123456789012.dkr.ecr.us-east-1.amazonaws.com
   ```

2. **Check IAM Permissions**:
   - Ensure EC2 instance has ECR read permissions
   - Verify IAM role is attached to instance

3. **Manual ECR Login**:
   ```bash
   # Legacy method (fallback)
   $(aws ecr get-login --region us-east-1 --no-include-email)
   ```

## API and Network Issues

### CORS Errors

#### "Access blocked by CORS policy"

**Symptoms**: Browser blocks API requests

**Debugging**:

1. **Check Browser Dev Tools**:
   - Network tab shows failed OPTIONS requests
   - Console shows CORS error messages

2. **Test CORS Configuration**:
   ```bash
   curl -X OPTIONS http://your-api:8000/api/endpoint \
     -H "Origin: http://your-frontend-domain" \
     -H "Access-Control-Request-Method: POST" \
     -v
   ```

**Solutions**:

1. **Update Backend CORS**:
   ```python
   # backend/config.py - Add your domain
   CORS_ORIGINS = [
       "http://localhost:3000",
       "http://your-domain.com"
   ]
   ```

2. **Environment Variable Method**:
   ```bash
   # backend/.env
   CORS_ORIGINS=http://localhost:3000,http://your-domain.com
   ```

### API Connection Issues

#### "Network Error" During Requests

**Symptoms**: Frontend shows "Network Error" for API calls

**Debugging Steps**:

1. **Check API URL Configuration**:
   ```javascript
   // frontend/.env.local
   REACT_APP_API_URL=http://your-backend:8000
   ```

2. **Test Backend Directly**:
   ```bash
   curl http://your-backend:8000/api/stocks
   ```

3. **Check Port Mapping**:
   ```bash
   # Ensure backend port is exposed
   docker-compose ps
   # Should show: 0.0.0.0:8000->8000/tcp
   ```

**Solutions**:

1. **Fix API URL**:
   ```javascript
   // Correct format
   REACT_APP_API_URL=http://divestifi.com:8000
   // Not: http://api.trading-platform.local:8000
   ```

2. **Add Port Mapping**:
   ```yaml
   # docker-compose.prod.yml
   backend:
     ports:
       - "8000:8000"  # Add this line
   ```

## Performance Issues

### Slow API Responses

**Symptoms**: API endpoints taking >5 seconds

**Debugging**:

1. **Check Database Performance**:
   ```sql
   -- SQLite query performance
   EXPLAIN QUERY PLAN SELECT * FROM stocks WHERE symbol = 'AAPL';
   ```

2. **Monitor Backend Logs**:
   ```bash
   # Look for slow query warnings
   tail -f backend/logs/trading_app.log
   ```

**Solutions**:

1. **Add Database Indexes**:
   ```python
   # In database models
   class Stock(Base):
       symbol = Column(String, index=True)  # Add index
   ```

2. **Implement Caching**:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def get_stock_data(symbol):
       # Cache expensive operations
   ```

### High Memory Usage

**Symptoms**: Containers using >2GB RAM

**Solutions**:

1. **Optimize Docker Resources**:
   ```yaml
   # docker-compose.yml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 512M
   ```

2. **Profile Memory Usage**:
   ```bash
   # Install memory profiler
   pip install memory-profiler
   
   # Profile functions
   @profile
   def expensive_function():
       pass
   ```

## Docker Issues

### Image Build Failures

#### "No space left on device"

**Solutions**:

1. **Clean Docker System**:
   ```bash
   docker system prune -a
   docker volume prune
   ```

2. **Remove Unused Images**:
   ```bash
   docker images -a | grep "<none>" | awk '{print $3}' | xargs docker rmi
   ```

### Container Startup Issues

#### "Container exiting immediately"

**Debugging**:

1. **Check Container Logs**:
   ```bash
   docker-compose logs service-name
   ```

2. **Run Container Interactively**:
   ```bash
   docker run -it your-image /bin/bash
   ```

**Common Fixes**:

1. **Fix Entrypoint Script**:
   ```bash
   # Ensure script is executable
   chmod +x scripts/entrypoint.sh
   ```

2. **Check Environment Variables**:
   ```bash
   docker-compose config
   # Verify all required env vars are set
   ```

## Getting Help

### Debugging Tools

1. **Browser Developer Tools**:
   - Network tab for API calls
   - Console tab for JavaScript errors
   - Application tab for localStorage/cookies

2. **Backend Debugging**:
   ```bash
   # Enable debug logging
   LOG_LEVEL=DEBUG python main.py
   ```

3. **Database Inspection**:
   ```bash
   # SQLite browser
   sqlite3 backend/data/trading.db
   .tables
   SELECT * FROM stocks LIMIT 5;
   ```

### Log Locations

- **Backend Logs**: `backend/logs/trading_app.log`
- **Docker Logs**: `docker-compose logs service-name`
- **System Logs**: `/var/log/` (Linux/macOS)
- **Browser Logs**: Developer Tools → Console

### Support Resources

1. **Documentation**: Check `docs/` directory
2. **GitHub Issues**: Search for similar problems
3. **Stack Overflow**: Tag with specific error messages
4. **Google Cloud Console**: For OAuth-related issues

### Creating Bug Reports

When reporting issues, include:

1. **Error Messages**: Full error text and stack traces
2. **Environment**: OS, Python/Node versions, Docker version
3. **Steps to Reproduce**: Detailed reproduction steps
4. **Configuration**: Relevant environment variables (redacted)
5. **Logs**: Recent log entries from affected services

Example bug report:
```markdown
## Issue
Google OAuth fails with "invalid_client" error

## Environment
- OS: macOS 12.0
- Python: 3.9.7
- Node: 18.12.0
- Browser: Chrome 108.0

## Steps to Reproduce
1. Start development environment
2. Navigate to http://localhost:3000
3. Click "Sign in with Google"
4. See error message

## Error Message
```
Error 401: invalid_client
```

## Configuration
- REACT_APP_GOOGLE_CLIENT_ID: 123456789012-abc...
- Google Cloud Console shows correct authorized origins

## Logs
[Include relevant log entries]
```

Remember: Most issues have been encountered before, so thorough debugging and searching existing documentation often reveals solutions quickly! 🔍