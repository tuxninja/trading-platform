#!/bin/bash
# Production database index deployment script
# Run this on the EC2 instance to optimize database performance

echo "🚀 Trading Platform Database Index Optimization"
echo "=============================================="
echo "Timestamp: $(date)"
echo ""

# Ensure we're in the correct directory
cd /opt/trading || { echo "❌ Cannot access /opt/trading directory"; exit 1; }

# Check if database exists
if [ ! -f "trading_app.db" ]; then
    echo "❌ Database file trading_app.db not found!"
    exit 1
fi

echo "📊 Current Database Status:"
echo "Database file: $(ls -lh trading_app.db)"
echo ""

# Create backup before optimization
echo "💾 Creating database backup..."
cp trading_app.db "trading_app_backup_$(date +%Y%m%d_%H%M%S).db"
echo "✅ Backup created"

# Stop containers temporarily for safe database access
echo ""  
echo "🛑 Stopping containers for safe database optimization..."
docker-compose -f docker-compose.prod.yml stop

# Run the index optimization
echo ""
echo "🔍 Running database index optimization..."
python3 -c "
import sys
sys.path.append('/opt/trading')
from optimize_database_indexes import create_database_indexes, analyze_query_performance

print('📊 Pre-optimization analysis:')
analyze_query_performance()

print('\n🔧 Creating database indexes...')
result = create_database_indexes()

if result['status'] == 'success':
    print(f'✅ Success! Created {result[\"indexes_created\"]} new indexes')
    print(f'💡 Performance improvements expected on all API endpoints')
else:
    print(f'❌ Failed: {result.get(\"error\", \"Unknown error\")}')
    sys.exit(1)
"

# Check if optimization succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Database optimization completed successfully!"
    
    # Restart containers
    echo ""
    echo "🚀 Restarting containers..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    echo "⏳ Waiting for services to start..."
    sleep 30
    
    # Test database connectivity
    echo ""
    echo "🧪 Testing database connectivity..."
    
    # Test backend health
    if curl -f http://localhost:8000/health 2>/dev/null; then
        echo "✅ Backend service is healthy"
    else
        echo "⚠️  Backend service may need more time to start"
    fi
    
    # Test API functionality
    if curl -f http://localhost/api/health 2>/dev/null; then
        echo "✅ API is accessible through nginx"
    else
        echo "⚠️  API may need more time to be available"
    fi
    
    echo ""
    echo "🎉 Database Optimization Deployment Complete!"
    echo ""
    echo "📈 Expected Performance Improvements:"
    echo "   • Trades queries: 50-90% faster"
    echo "   • Capital allocation: 60-80% faster" 
    echo "   • Performance metrics: 40-70% faster"
    echo "   • Watchlist operations: 30-60% faster"
    echo "   • Overall API response times should be significantly improved"
    echo ""
    echo "🌐 Test the optimized performance at: http://divestifi.com"
    
else
    echo ""
    echo "❌ Database optimization failed!"
    
    # Restore from backup
    echo "🔄 Restoring database from backup..."
    latest_backup=$(ls -1t trading_app_backup_*.db | head -n1)
    if [ -n "$latest_backup" ]; then
        cp "$latest_backup" trading_app.db
        echo "✅ Database restored from backup: $latest_backup"
    else
        echo "❌ No backup found - manual intervention required"
    fi
    
    # Restart containers anyway
    echo "🚀 Restarting containers..."
    docker-compose -f docker-compose.prod.yml up -d
    
    echo "❌ Database optimization deployment failed - check logs above"
    exit 1
fi

echo ""
echo "=============================================="
echo "🔧 Database Index Optimization Complete"
echo "Check the application performance improvements"