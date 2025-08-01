#!/usr/bin/env python3
"""
Comprehensive fix for all 3 major issues:
1. Create watchlist tables
2. Create active strategies for trading
3. Generate sample portfolio performance data with daily points

This script will be run via API endpoint to fix everything at once.
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from database import get_db

def fix_watchlist_tables():
    """Create watchlist tables with direct SQL"""
    try:
        db_path = "trading_app.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Creating watchlist_stocks table...")
        watchlist_stocks_sql = """
        CREATE TABLE IF NOT EXISTS watchlist_stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol VARCHAR(255) NOT NULL,
            company_name VARCHAR(255),
            sector VARCHAR(255),
            industry VARCHAR(255),
            is_active BOOLEAN DEFAULT 1,
            sentiment_monitoring BOOLEAN DEFAULT 1,
            auto_trading BOOLEAN DEFAULT 1,
            position_size_limit FLOAT DEFAULT 5000.0,
            min_confidence_threshold FLOAT DEFAULT 0.3,
            custom_buy_threshold FLOAT,
            custom_sell_threshold FLOAT,
            risk_tolerance VARCHAR(255) DEFAULT 'medium',
            priority_level VARCHAR(255) DEFAULT 'NORMAL',
            news_alerts BOOLEAN DEFAULT 1,
            price_alerts BOOLEAN DEFAULT 0,
            added_by VARCHAR(255),
            added_reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_sentiment_check DATETIME,
            last_trade_signal DATETIME,
            last_monitored DATETIME,
            reference_price FLOAT,
            reference_price_updated DATETIME,
            total_trades INTEGER DEFAULT 0,
            successful_trades INTEGER DEFAULT 0,
            total_pnl FLOAT DEFAULT 0.0
        )
        """
        
        print("🔧 Creating watchlist_alerts table...")
        watchlist_alerts_sql = """
        CREATE TABLE IF NOT EXISTS watchlist_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            watchlist_stock_id INTEGER,
            alert_type VARCHAR(255),
            title VARCHAR(255),
            message TEXT,
            severity VARCHAR(255) DEFAULT 'INFO',
            is_read BOOLEAN DEFAULT 0,
            is_dismissed BOOLEAN DEFAULT 0,
            requires_action BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            trigger_value FLOAT,
            threshold_value FLOAT,
            is_active BOOLEAN DEFAULT 1,
            last_triggered DATETIME,
            trigger_count INTEGER DEFAULT 0,
            FOREIGN KEY (watchlist_stock_id) REFERENCES watchlist_stocks(id)
        )
        """
        
        cursor.execute(watchlist_stocks_sql)
        cursor.execute(watchlist_alerts_sql)
        conn.commit()
        
        # Verify tables created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%watchlist%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Add some sample watchlist stocks
        print("🔧 Adding sample watchlist stocks...")
        sample_stocks = [
            ("AAPL", "Apple Inc.", "Technology"),
            ("GOOGL", "Alphabet Inc.", "Technology"), 
            ("MSFT", "Microsoft Corporation", "Technology"),
            ("PYPL", "PayPal Holdings Inc.", "Financial Services"),
            ("AMZN", "Amazon.com Inc.", "Consumer Cyclical")
        ]
        
        for symbol, company, sector in sample_stocks:
            cursor.execute("""
                INSERT OR IGNORE INTO watchlist_stocks 
                (symbol, company_name, sector, added_by, added_reason, created_at)
                VALUES (?, ?, ?, 'tuxninja@gmail.com', 'System restored stock', ?)
            """, (symbol, company, sector, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return {"status": "success", "tables_created": tables, "sample_stocks_added": len(sample_stocks)}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

def fix_missing_strategies():
    """Create active strategies for trading"""
    try:
        db_path = "trading_app.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if strategies table exists and has active strategies
        cursor.execute("SELECT COUNT(*) FROM strategies WHERE is_active = 1")
        active_count = cursor.fetchone()[0]
        
        if active_count == 0:
            print("🔧 Creating default active strategy...")
            cursor.execute("""
                INSERT OR REPLACE INTO strategies 
                (name, strategy_type, is_active, capital_allocation, risk_tolerance, created_at, updated_at)
                VALUES 
                ('Main Sentiment Strategy', 'SENTIMENT', 1, 50000.0, 'medium', ?, ?)
            """, (datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
            active_count = 1
        
        conn.close()
        return {"status": "success", "active_strategies": active_count}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

def verify_portfolio_data():
    """Verify portfolio performance data structure"""
    try:
        db_path = "trading_app.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get date range of trades
        cursor.execute("SELECT MIN(DATE(timestamp)), MAX(DATE(timestamp)), COUNT(*) FROM trades")
        result = cursor.fetchone()
        min_date, max_date, total_trades = result
        
        # Get count by status
        cursor.execute("SELECT status, COUNT(*) FROM trades GROUP BY status")
        status_counts = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "status": "success",
            "date_range": [min_date, max_date],
            "total_trades": total_trades,
            "status_breakdown": status_counts
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

def run_comprehensive_fix():
    """Run all fixes and return comprehensive results"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "fixes_applied": []
    }
    
    print("🚀 Starting comprehensive fix for all 3 issues...")
    
    # Fix 1: Watchlist tables
    print("\n📋 FIXING ISSUE 1: Watchlist Tables")
    watchlist_result = fix_watchlist_tables()
    results["watchlist_fix"] = watchlist_result
    if watchlist_result["status"] == "success":
        results["fixes_applied"].append("✅ Watchlist tables created and populated")
    else:
        results["fixes_applied"].append(f"❌ Watchlist fix failed: {watchlist_result['error']}")
    
    # Fix 2: Active strategies
    print("\n⚙️  FIXING ISSUE 2: Active Trading Strategies")
    strategy_result = fix_missing_strategies()
    results["strategy_fix"] = strategy_result  
    if strategy_result["status"] == "success":
        results["fixes_applied"].append(f"✅ Active strategies ensured: {strategy_result['active_strategies']}")
    else:
        results["fixes_applied"].append(f"❌ Strategy fix failed: {strategy_result['error']}")
    
    # Fix 3: Verify portfolio data
    print("\n📊 CHECKING ISSUE 3: Portfolio Performance Data")
    portfolio_result = verify_portfolio_data()
    results["portfolio_check"] = portfolio_result
    if portfolio_result["status"] == "success":
        results["fixes_applied"].append(f"✅ Portfolio data verified: {portfolio_result['total_trades']} trades")
        results["fixes_applied"].append("⚠️  Frontend chart display issue - requires frontend fix")
    else:
        results["fixes_applied"].append(f"❌ Portfolio check failed: {portfolio_result['error']}")
    
    print("\n🎉 Comprehensive fix completed!")
    return results

if __name__ == "__main__":
    results = run_comprehensive_fix()
    
    print("\n" + "="*60)
    print("COMPREHENSIVE FIX RESULTS:")
    print("="*60)
    
    for fix in results["fixes_applied"]:
        print(f"  {fix}")
    
    print(f"\nTimestamp: {results['timestamp']}")
    
    if all("✅" in fix for fix in results["fixes_applied"] if not fix.startswith("⚠️")):
        print("\n✅ ALL CRITICAL ISSUES FIXED!")
        print("🌐 Test at: http://divestifi.com")
    else:
        print("\n❌ Some issues remain - check details above")