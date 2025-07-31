#!/bin/bash
# Production troubleshooting script for divestifi.com
# Run this to diagnose 502/504 errors

echo "🔍 Production Troubleshooting for divestifi.com"
echo "=============================================="
echo "Timestamp: $(date)"
echo ""

# Basic connectivity test
echo "🌐 Testing external connectivity:"
curl -I http://divestifi.com 2>&1 | head -5
echo ""

echo "📊 System Resources:"
echo "Memory:"
free -h
echo "Disk:"
df -h / | tail -1
echo "Load:"
uptime
echo ""

echo "🐳 Docker Status:"
echo "Docker service:"
systemctl is-active docker
echo ""

echo "Container status:"
docker ps -a
echo ""

echo "Docker networks:"
docker network ls
echo ""

echo "🔍 Container Logs (last 50 lines each):"
echo ""
echo "=== BACKEND LOGS ==="
docker logs --tail=50 trading-backend 2>&1 || echo "Backend container not found"
echo ""

echo "=== FRONTEND LOGS ==="
docker logs --tail=20 trading-frontend 2>&1 || echo "Frontend container not found"
echo ""

echo "=== NGINX LOGS ==="
docker logs --tail=30 trading-nginx 2>&1 || echo "Nginx container not found"
echo ""

echo "=== SCHEDULER LOGS ==="
docker logs --tail=20 trading-scheduler 2>&1 || echo "Scheduler container not found"
echo ""

echo "🔧 Network Connectivity Tests:"
echo "Testing internal container connectivity:"

# Test if nginx can reach backend
if docker exec trading-nginx ping -c 2 trading-backend 2>/dev/null; then
    echo "✅ nginx can ping backend"
else
    echo "❌ nginx cannot ping backend"
fi

# Test backend directly
echo "Testing backend directly:"
curl -f http://localhost:8000/health 2>/dev/null && echo "✅ Backend responding on port 8000" || echo "❌ Backend not responding on port 8000"

# Test through nginx
echo "Testing API through nginx:"
curl -f http://localhost/api/health 2>/dev/null && echo "✅ API accessible through nginx" || echo "❌ API not accessible through nginx"

# Test frontend
echo "Testing frontend:"
curl -f http://localhost:80 2>/dev/null | head -c 100 && echo "... ✅ Frontend responding" || echo "❌ Frontend not responding"

echo ""
echo "📋 Configuration Files:"
echo "nginx.conf exists:"
ls -la /opt/trading/nginx.conf 2>/dev/null || echo "nginx.conf missing"

echo ""
echo "docker-compose status:"
cd /opt/trading
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🏥 Health Check Tests:"
echo "Backend health (direct):"
timeout 10 curl -s http://localhost:8000/health 2>&1 | head -3

echo ""
echo "API health (via nginx):"
timeout 10 curl -s http://localhost/api/health 2>&1 | head -3

echo ""
echo "📡 Port Status:"
echo "Listening ports:"
netstat -tlnp | grep -E "(80|8000|443)" || ss -tlnp | grep -E "(80|8000|443)"

echo ""
echo "🔍 Process Status:"
echo "nginx processes:"
pgrep -f nginx | wc -l
echo "python processes:"
pgrep -f python | wc -l
echo "node processes:"
pgrep -f node | wc -l

echo ""
echo "=============================================="
echo "🔧 Quick Fix Commands:"
echo "1. Restart all containers:"
echo "   cd /opt/trading && docker-compose -f docker-compose.prod.yml restart"
echo ""
echo "2. Full restart:"
echo "   cd /opt/trading && docker-compose -f docker-compose.prod.yml down && docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "3. Check real-time logs:"
echo "   docker logs -f trading-backend"
echo "   docker logs -f trading-nginx"
echo ""
echo "=============================================="