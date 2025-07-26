#!/bin/bash

# Production Database Migration Script
# This script runs the database migration on the production server after deployment

echo "🔄 Running database migration on production server..."

# Wait for deployment to complete
echo "⏳ Waiting for deployment to complete (60 seconds)..."
sleep 60

# Run the database migration via the API endpoint
echo "🔄 Triggering database migration..."
curl -X POST "https://divestifi.com/api/debug/migrate" \
     -H "Content-Type: application/json" \
     -w "\n%{http_code}\n" \
     --connect-timeout 30 \
     --retry 3 \
     --retry-delay 5

echo ""
echo "🔍 Testing trades API endpoint..."
curl -X GET "https://divestifi.com/api/trades" \
     -H "Accept: application/json" \
     -w "\n%{http_code}\n" \
     --connect-timeout 30

echo ""
echo "🔍 Testing debug endpoint..."
curl -X GET "https://divestifi.com/api/debug" \
     -H "Accept: application/json" \
     -w "\n%{http_code}\n" \
     --connect-timeout 30

echo ""
echo "✅ Migration and testing completed!"
echo "🌐 Try logging in at: https://divestifi.com"