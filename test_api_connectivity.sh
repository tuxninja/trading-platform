#!/bin/bash

# API Connectivity Test Script
# This script tests various API endpoints to debug connectivity issues

echo "=== API Connectivity Test ==="
echo "Testing API connectivity from different endpoints..."
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test URLs
LOCALHOST_URL="http://localhost:8000"
PRODUCTION_URL="https://divestifi.com"
NGINX_INTERNAL="http://trading-backend:8000"

echo "1. Testing localhost backend (development)..."
if curl -s -f "$LOCALHOST_URL/api/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Localhost backend reachable${NC}"
    echo "Response:"
    curl -s "$LOCALHOST_URL/api/health" | jq '.' 2>/dev/null || curl -s "$LOCALHOST_URL/api/health"
else
    echo -e "${RED}✗ Localhost backend not reachable${NC}"
fi
echo

echo "2. Testing production health endpoint..."
if curl -s -f "$PRODUCTION_URL/api/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Production health endpoint reachable${NC}"
    echo "Response:"
    curl -s "$PRODUCTION_URL/api/health" | jq '.' 2>/dev/null || curl -s "$PRODUCTION_URL/api/health"
else
    echo -e "${RED}✗ Production health endpoint not reachable${NC}"
    echo "Error details:"
    curl -v "$PRODUCTION_URL/api/health" 2>&1 | head -20
fi
echo

echo "3. Testing production trades endpoint..."
if curl -s -f "$PRODUCTION_URL/api/trades" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Production trades endpoint reachable${NC}"
    echo "Response (first few lines):"
    curl -s "$PRODUCTION_URL/api/trades" | head -5
else
    echo -e "${RED}✗ Production trades endpoint not reachable${NC}"
    echo "HTTP status:"
    curl -s -o /dev/null -w "%{http_code}" "$PRODUCTION_URL/api/trades"
    echo
fi
echo

echo "4. Testing CORS headers..."
echo "OPTIONS request to check CORS:"
curl -s -X OPTIONS -H "Origin: https://divestifi.com" -I "$PRODUCTION_URL/api/health" | grep -i "access-control" || echo "No CORS headers found"
echo

echo "5. Testing nginx proxy path..."
echo "Checking if nginx is correctly proxying /api/ requests..."
curl -s -I "$PRODUCTION_URL/api/debug/network" | head -5
echo

echo "6. Testing SSL certificate..."
echo "SSL certificate check:"
echo | openssl s_client -connect divestifi.com:443 -servername divestifi.com 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "SSL check failed"
echo

echo "=== Docker Network Test (run from inside container) ==="
echo "If running inside docker, test internal network:"
if command -v docker &> /dev/null; then
    echo "Testing internal docker network connectivity..."
    # This would need to be run from inside the frontend container
    echo "Run this inside the frontend container:"
    echo "curl -s http://trading-backend:8000/api/health"
else
    echo "Docker not available for network test"
fi
echo

echo "=== Summary & Recommendations ==="
echo -e "${YELLOW}Common Issues:${NC}"
echo "1. REACT_APP_API_URL pointing to localhost in production"
echo "2. nginx not properly proxying /api/ requests"
echo "3. CORS headers not configured correctly"
echo "4. Backend container not accessible from frontend container"
echo "5. SSL/TLS issues with the domain"
echo
echo -e "${YELLOW}Debug Steps:${NC}"
echo "1. Check docker-compose logs: docker-compose logs backend"
echo "2. Access the debug page: https://divestifi.com/debug"
echo "3. Check nginx config is being used correctly"
echo "4. Verify environment variables in production build"
echo "5. Test API endpoints directly with curl/postman"