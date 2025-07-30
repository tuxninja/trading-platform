#!/bin/bash
# Quick fix script for deployment issues
# Run this on your EC2 instance to fix the 502 errors

echo "🔧 Trading Platform Quick Fix"
echo "=============================="

# Ensure we're in the right directory
cd /opt/trading || { echo "❌ Cannot access /opt/trading directory"; exit 1; }

echo "📊 Current container status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🛑 Stopping all containers..."
docker-compose -f docker-compose.prod.yml down

echo ""
echo "🧹 Cleaning up any orphaned containers..."
docker container prune -f

echo ""
echo "📁 Ensuring required directories exist..."
sudo mkdir -p /opt/trading/data /opt/trading/logs
sudo chown -R ec2-user:ec2-user /opt/trading/

echo ""
echo "🔍 Checking for required files..."
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ docker-compose.prod.yml missing"
    exit 1
fi

if [ ! -f "nginx.conf" ]; then
    echo "❌ nginx.conf missing"
    exit 1
fi

echo "✅ Required files present"

echo ""
echo "🐳 Pulling latest images..."
docker-compose -f docker-compose.prod.yml pull

echo ""
echo "🚀 Starting services with health checks..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "⏳ Waiting for services to start (60 seconds)..."
sleep 60

echo ""
echo "🏥 Checking service health..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "📊 Container logs (last 20 lines each):"
echo "--- Backend logs ---"
docker logs --tail=20 trading-backend 2>&1

echo ""
echo "--- Frontend logs ---"
docker logs --tail=20 trading-frontend 2>&1

echo ""
echo "--- Nginx logs ---"
docker logs --tail=20 trading-nginx 2>&1

echo ""
echo "🔍 Testing connectivity..."
echo "Backend health check:"
curl -f http://localhost:8000/health 2>/dev/null && echo "✅ Backend healthy" || echo "❌ Backend not responding"

echo "API through nginx:"
curl -f http://localhost/api/health 2>/dev/null && echo "✅ API accessible" || echo "❌ API not accessible"

echo "Frontend through nginx:"
curl -f http://localhost/ 2>/dev/null | head -c 100 && echo "... ✅ Frontend accessible" || echo "❌ Frontend not accessible"

echo ""
echo "=============================="
echo "🔧 Quick Fix Complete"
echo "Check the logs above for any issues"
echo "If problems persist, run: docker-compose -f docker-compose.prod.yml logs -f"