#!/bin/bash
# Troubleshooting script for trading platform deployment

echo "🔍 Trading Platform Troubleshooting Report"
echo "========================================="

# Basic system info
echo "📊 System Information:"
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "Uptime: $(uptime)"
echo

# Docker status
echo "🐳 Docker Status:"
echo "Docker version: $(docker --version)"
echo "Docker daemon status: $(systemctl is-active docker)"
echo

# Container status
echo "📦 Container Status:"
docker ps -a
echo

# Container logs (last 20 lines each)
echo "📋 Container Logs:"
echo "--- Backend Logs ---"
docker logs trading-backend --tail 20 2>/dev/null || echo "Backend container not found"
echo
echo "--- Frontend Logs ---"
docker logs trading-frontend --tail 20 2>/dev/null || echo "Frontend container not found"
echo
echo "--- Scheduler Logs ---"
docker logs trading-scheduler --tail 20 2>/dev/null || echo "Scheduler container not found"
echo

# Port bindings
echo "🌐 Port Bindings:"
docker port trading-frontend 2>/dev/null || echo "Frontend port binding not found"
docker port trading-backend 2>/dev/null || echo "Backend port binding not found"
echo

# Network status
echo "🔗 Network Status:"
docker network ls
echo

# Check if ports are listening
echo "👂 Listening Ports:"
netstat -tlnp | grep -E ':(80|443|8000)' || echo "No services listening on ports 80, 443, or 8000"
echo

# Docker compose status
echo "🏗️ Docker Compose Status:"
cd /opt/trading
docker-compose -f docker-compose.prod.yml ps 2>/dev/null || echo "Docker compose not running"
echo

# Check docker-compose file
echo "📄 Docker Compose Configuration:"
echo "File exists: $(test -f docker-compose.prod.yml && echo 'Yes' || echo 'No')"
if [ -f docker-compose.prod.yml ]; then
    echo "File size: $(wc -l < docker-compose.prod.yml) lines"
    echo "Services defined:"
    grep -E "^  [a-z]" docker-compose.prod.yml | sed 's/:$//'
fi
echo

# Check if nginx is running (from previous attempts)
echo "🔍 Legacy Services:"
docker ps -a | grep nginx || echo "No nginx containers found"
echo

# Disk space
echo "💾 Disk Usage:"
df -h /
echo

# Memory usage
echo "🧠 Memory Usage:"
free -h
echo

# Security group check (if we can access metadata)
echo "🔒 EC2 Metadata (if available):"
curl -s http://169.254.169.254/latest/meta-data/public-ipv4 || echo "Cannot access EC2 metadata"
echo

echo "========================================="
echo "🏁 Troubleshooting report complete!"