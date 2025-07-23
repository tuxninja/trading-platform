# Deployment Checklist

This checklist ensures smooth deployments and prevents common issues encountered with the Trading Platform.

## Pre-Deployment Checklist

### 🔍 Code Review
- [ ] All tests pass locally (`./run_tests.sh`)
- [ ] Code linting completed (`npm run lint`, `black .`, `flake8 .`)
- [ ] No hardcoded secrets or credentials in code
- [ ] Environment variables documented and configured
- [ ] Database migrations tested (if applicable)

### 🌐 Environment Configuration
- [ ] **Google Client ID** set in GitHub secrets and production `.env`
- [ ] **API keys** (News API, Alpha Vantage) configured and valid
- [ ] **CORS origins** include production domain
- [ ] **Database URL** points to correct database
- [ ] **Secret keys** are properly generated and secure

### 🔒 Security Review
- [ ] No sensitive data in version control
- [ ] Security group rules reviewed and minimal
- [ ] SSL certificates valid (if using HTTPS)
- [ ] OAuth redirect URIs match production domain
- [ ] API rate limiting configured

## Deployment Process

### 🚀 Automated Deployment (GitHub Actions)

#### 1. Pre-Deployment
- [ ] Verify GitHub Actions secrets are current:
  ```bash
  gh secret list --repo username/trading-platform
  ```
- [ ] Check EC2 instance is running and accessible
- [ ] Ensure security group allows GitHub Actions SSH access

#### 2. Trigger Deployment
- [ ] Push to `main` branch or create release
- [ ] Monitor GitHub Actions workflow progress
- [ ] Watch for any error messages or warnings

#### 3. Monitor Deployment
- [ ] Check workflow logs for errors
- [ ] Verify Docker images were built and pushed to ECR
- [ ] Confirm SSH connection to EC2 succeeds
- [ ] Watch container startup and health checks

### 🛠️ Manual Deployment (Fallback)

#### 1. Connect to EC2
```bash
ssh -o StrictHostKeyChecking=no ec2-user@98.85.193.239
cd /opt/trading
```

#### 2. Pull Latest Images
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  907391580367.dkr.ecr.us-east-1.amazonaws.com

docker pull 907391580367.dkr.ecr.us-east-1.amazonaws.com/trading-platform-backend:latest
docker pull 907391580367.dkr.ecr.us-east-1.amazonaws.com/trading-platform-frontend:latest
```

#### 3. Update Configuration
```bash
# Update docker-compose with new image tags if needed
# Verify environment variables in .env file
cat .env | grep GOOGLE_CLIENT_ID
```

#### 4. Deploy Containers
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

## Post-Deployment Verification

### 🔍 Health Checks

#### 1. Container Status
```bash
# Check all containers are running
docker-compose -f docker-compose.prod.yml ps

# Should show:
# - backend: Up and healthy
# - frontend: Up and healthy  
# - scheduler: Up (may be unhealthy, that's normal)
```

#### 2. API Connectivity
```bash
# Test backend health endpoint
curl http://divestifi.com:8000/
# Expected: {"status":"healthy","google_client_id_configured":true}

# Test frontend accessibility
curl -I http://divestifi.com/
# Expected: 200 OK
```

#### 3. Google OAuth Test
- [ ] Navigate to production URL (http://divestifi.com)
- [ ] Click "Sign in with Google"
- [ ] Complete OAuth flow
- [ ] Verify redirect to dashboard
- [ ] Test API calls work after authentication

### 🐛 Common Issues Check

#### CORS Configuration
```bash
# Test CORS preflight
curl -X OPTIONS http://divestifi.com:8000/api/auth/google \
  -H "Origin: http://divestifi.com" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Expected: 200 OK (not 400 Bad Request)
```

#### Environment Variables
```bash
# Verify Google Client ID in containers
docker exec $(docker ps --format 'table {{.Names}}' | grep frontend | head -1) \
  sh -c 'env | grep GOOGLE_CLIENT_ID'

docker exec $(docker ps --format 'table {{.Names}}' | grep backend | head -1) \
  sh -c 'env | grep GOOGLE_CLIENT_ID'

# Both should return the same client ID
```

#### Port Mapping
```bash
# Verify backend port is externally accessible
docker-compose -f docker-compose.prod.yml ps

# Backend should show: 0.0.0.0:8000->8000/tcp
```

### 📊 Performance Verification

#### Response Times
```bash
# Test API response time
time curl -s http://divestifi.com:8000/ > /dev/null
# Should complete in < 2 seconds

# Test frontend load time
time curl -s http://divestifi.com/ > /dev/null
# Should complete in < 3 seconds
```

#### Resource Usage
```bash
# Check container resource usage
docker stats --no-stream

# Backend should use < 512MB RAM
# Frontend should use < 256MB RAM
```

## Rollback Procedures

### 🔄 Automated Rollback

#### 1. Identify Last Working Commit
```bash
# Check recent deployments
gh run list --repo username/trading-platform --limit 10

# Find last successful deployment commit hash
```

#### 2. Revert to Previous Version
```bash
# Create rollback branch
git checkout -b rollback-to-<commit-hash>
git reset --hard <last-working-commit>
git push origin rollback-to-<commit-hash>

# Create PR to merge rollback to main
```

### 🛠️ Manual Rollback

#### 1. Use Previous Docker Images
```bash
# SSH to EC2
ssh ec2-user@98.85.193.239
cd /opt/trading

# Check available images
docker images | grep trading-platform

# Update docker-compose to use previous tag
sed -i 's/:latest/:previous-working-tag/g' docker-compose.prod.yml

# Restart with previous version
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

#### 2. Restore Database (if needed)
```bash
# Restore from backup (if database changes were made)
cp /opt/trading/backups/trading_app_<date>.db /opt/trading/data/trading.db

# Restart containers to pick up restored database
docker-compose -f docker-compose.prod.yml restart
```

## Monitoring & Alerts

### 📈 Key Metrics to Monitor

#### Application Health
- [ ] HTTP response codes (should be mostly 200s)
- [ ] API response times (< 2s average)
- [ ] Container memory usage (< 80% of allocated)
- [ ] Database query performance

#### System Health
- [ ] EC2 instance CPU usage (< 80%)
- [ ] Disk space usage (< 80%)
- [ ] Network connectivity
- [ ] SSL certificate expiry (if using HTTPS)

### 🚨 Alert Conditions

#### Critical Alerts
- [ ] Application completely unavailable (HTTP 5xx errors)
- [ ] Database connection failures
- [ ] Container crashes or restart loops
- [ ] Authentication system failures

#### Warning Alerts
- [ ] High response times (> 5s)
- [ ] High error rates (> 5%)
- [ ] Resource usage approaching limits
- [ ] Failed health checks

## Documentation Updates

### 📝 Post-Deployment Tasks

#### Update Documentation
- [ ] Update API documentation if endpoints changed
- [ ] Update configuration examples if env vars changed
- [ ] Document any new deployment procedures used
- [ ] Update troubleshooting guide with any new issues

#### Communication
- [ ] Notify team of successful deployment
- [ ] Document any issues encountered and resolutions
- [ ] Update monitoring dashboards if needed
- [ ] Plan next deployment improvements

## Emergency Contacts

### 🆘 When Things Go Wrong

#### Critical Issues (Site Down)
1. **Immediate**: Check container status and restart if needed
2. **Quick Fix**: Rollback to previous working version
3. **Investigation**: Check logs and identify root cause
4. **Communication**: Notify stakeholders of issue and ETA

#### Authentication Issues
1. **Check**: Google OAuth configuration and client ID
2. **Verify**: CORS settings and authorized origins
3. **Test**: Manual authentication flow
4. **Rollback**: If configuration changes caused issue

#### Performance Issues
1. **Monitor**: Resource usage and response times
2. **Scale**: Restart containers or increase resources
3. **Optimize**: Identify performance bottlenecks
4. **Plan**: Long-term scaling strategy

## Success Criteria

### ✅ Deployment Successful When:

- [ ] All containers are running and healthy
- [ ] Frontend loads without errors at production URL
- [ ] Google OAuth login flow works completely
- [ ] API endpoints respond correctly
- [ ] No CORS or authentication errors
- [ ] Performance meets acceptable thresholds
- [ ] No errors in application logs
- [ ] Monitoring systems show green status

### 📋 Post-Deployment Review

After each deployment, review:
- What went well?
- What could be improved?
- Any new issues encountered?
- Documentation gaps identified?
- Process improvements needed?

---

**Remember**: Better to deploy slowly and correctly than quickly with issues. This checklist helps ensure consistent, reliable deployments of the Trading Platform! 🚀