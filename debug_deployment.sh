#!/bin/bash
# Debug script to diagnose deployment issues
# Run this on your EC2 instance to troubleshoot the 502 errors

echo "🔍 Trading Platform Deployment Diagnostics"
echo "=========================================="
echo "Timestamp: $(date)"
echo ""

echo "📊 System Resources:"
echo "Memory usage:"
free -h
echo ""
echo "CPU usage:"
top -bn1 | head -5
echo ""
echo "Disk space:"
df -h
echo ""

echo "🐳 Docker Status:"
echo "Docker service status:"
systemctl is-active docker
echo ""
echo "Running containers:"
docker ps
echo ""
echo "All containers (including stopped):"
docker ps -a
echo ""
echo "Docker logs for backend (last 50 lines):"
docker logs --tail=50 trading-backend 2>&1 || echo "Backend container not found or not running"
echo ""
echo "Docker logs for frontend (last 20 lines):"
docker logs --tail=20 trading-frontend 2>&1 || echo "Frontend container not found or not running"
echo ""
echo "Docker logs for nginx (last 20 lines):"
docker logs --tail=20 trading-nginx 2>&1 || echo "Nginx container not found or not running"
echo ""

echo "🌐 Network Connectivity:"
echo "Container network:"
docker network ls
echo ""
echo "Testing internal connectivity:"
docker exec trading-nginx ping -c 2 trading-backend 2>/dev/null || echo "Cannot ping backend from nginx"
echo ""

echo "🔧 Configuration Files:"
echo "Docker compose status:"
cd /opt/trading
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "Nginx config (if accessible):"
docker exec trading-nginx cat /etc/nginx/nginx.conf 2>/dev/null | head -30 || echo "Cannot access nginx config"
echo ""

echo "🏥 Health Checks:"
echo "Backend health check:"
curl -f http://localhost:8000/health 2>/dev/null && echo "✅ Backend responding locally" || echo "❌ Backend not responding locally"
echo ""
echo "Frontend health check:"
curl -f http://localhost:3000 2>/dev/null && echo "✅ Frontend responding locally" || echo "❌ Frontend not responding locally"
echo ""
echo "External health check:"
curl -f http://localhost/api/health 2>/dev/null && echo "✅ API responding via nginx" || echo "❌ API not responding via nginx"
echo ""

echo "📋 Recent System Events:"
echo "Recent journal entries for docker:"
journalctl -u docker --since "10 minutes ago" --no-pager -n 10 || echo "Cannot access journal"
echo ""

echo "🔍 Process Information:"
echo "Python processes:"
ps aux | grep python | grep -v grep || echo "No python processes found"
echo ""
echo "Node processes:"
ps aux | grep node | grep -v grep || echo "No node processes found"
echo ""
echo "Nginx processes:"
ps aux | grep nginx | grep -v grep || echo "No nginx processes found"
echo ""

echo "📁 File System Check:"
echo "Trading directory contents:"
ls -la /opt/trading/
echo ""
echo "Docker compose file exists:"
ls -la /opt/trading/docker-compose.prod.yml || echo "Docker compose file missing"
echo ""

echo "🎯 Quick Fixes to Try:"
echo "1. Restart all containers:"
echo "   cd /opt/trading && docker-compose -f docker-compose.prod.yml down && docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "2. Check backend logs in real-time:"
echo "   docker logs -f trading-backend"
echo ""
echo "3. Rebuild and restart if needed:"
echo "   cd /opt/trading && docker-compose -f docker-compose.prod.yml down && docker-compose -f docker-compose.prod.yml pull && docker-compose -f docker-compose.prod.yml up -d"
echo ""

echo "=========================================="
echo "🔍 Diagnostics Complete"
echo "Save this output and share with support if needed"