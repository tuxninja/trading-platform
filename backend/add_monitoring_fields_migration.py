#!/usr/bin/env python3
"""
Database migration script to add continuous monitoring fields to WatchlistStock and WatchlistAlert models.

This script adds:
- risk_tolerance, last_monitored, reference_price, reference_price_updated to watchlist_stocks
- is_active, last_triggered, trigger_count to watchlist_alerts

Run this script once to update the database schema.
"""

import sqlite3
import sys
import os
from datetime import datetime

def run_migration():
    """Apply database migrations for continuous monitoring fields."""
    
    try:
        # Connect to database
        db_path = "trading_app.db"
        if not os.path.exists(db_path):
            print(f"Database file {db_path} not found. Creating new database...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        migrations_applied = []
        
        # Check if watchlist_stocks table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='watchlist_stocks'")
        if not cursor.fetchone():
            print("Warning: watchlist_stocks table does not exist yet. Skipping watchlist migrations.")
        else:
            print("Adding fields to watchlist_stocks table...")
            
            # Add risk_tolerance column
            try:
                cursor.execute("ALTER TABLE watchlist_stocks ADD COLUMN risk_tolerance TEXT DEFAULT 'medium'")
                migrations_applied.append("Added risk_tolerance column to watchlist_stocks")
                print("✓ Added risk_tolerance column")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("✓ risk_tolerance column already exists")
                else:
                    print(f"✗ Error adding risk_tolerance: {e}")
            
            # Add last_monitored column
            try:
                cursor.execute("ALTER TABLE watchlist_stocks ADD COLUMN last_monitored DATETIME")
                migrations_applied.append("Added last_monitored column to watchlist_stocks")
                print("✓ Added last_monitored column")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("✓ last_monitored column already exists")
                else:
                    print(f"✗ Error adding last_monitored: {e}")
            
            # Add reference_price column
            try:
                cursor.execute("ALTER TABLE watchlist_stocks ADD COLUMN reference_price REAL")
                migrations_applied.append("Added reference_price column to watchlist_stocks")
                print("✓ Added reference_price column")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("✓ reference_price column already exists")
                else:
                    print(f"✗ Error adding reference_price: {e}")
            
            # Add reference_price_updated column
            try:
                cursor.execute("ALTER TABLE watchlist_stocks ADD COLUMN reference_price_updated DATETIME")
                migrations_applied.append("Added reference_price_updated column to watchlist_stocks")
                print("✓ Added reference_price_updated column")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("✓ reference_price_updated column already exists")
                else:
                    print(f"✗ Error adding reference_price_updated: {e}")
        
        # Check if watchlist_alerts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='watchlist_alerts'")
        if not cursor.fetchone():
            print("Warning: watchlist_alerts table does not exist yet. Skipping alerts migrations.")
        else:
            print("\nAdding fields to watchlist_alerts table...")
            
            # Add is_active column
            try:
                cursor.execute("ALTER TABLE watchlist_alerts ADD COLUMN is_active BOOLEAN DEFAULT 1")
                migrations_applied.append("Added is_active column to watchlist_alerts")
                print("✓ Added is_active column")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("✓ is_active column already exists")
                else:
                    print(f"✗ Error adding is_active: {e}")
            
            # Add last_triggered column
            try:
                cursor.execute("ALTER TABLE watchlist_alerts ADD COLUMN last_triggered DATETIME")
                migrations_applied.append("Added last_triggered column to watchlist_alerts")
                print("✓ Added last_triggered column")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("✓ last_triggered column already exists")
                else:
                    print(f"✗ Error adding last_triggered: {e}")
            
            # Add trigger_count column
            try:
                cursor.execute("ALTER TABLE watchlist_alerts ADD COLUMN trigger_count INTEGER DEFAULT 0")
                migrations_applied.append("Added trigger_count column to watchlist_alerts")
                print("✓ Added trigger_count column")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("✓ trigger_count column already exists")
                else:
                    print(f"✗ Error adding trigger_count: {e}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"\n✅ Migration completed successfully!")
        print(f"Applied {len(migrations_applied)} database changes:")
        for migration in migrations_applied:
            print(f"  - {migration}")
        
        if not migrations_applied:
            print("No new migrations were needed - all fields already exist.")
        
        return {
            "status": "success",
            "migrations_applied": migrations_applied,
            "message": f"Applied {len(migrations_applied)} continuous monitoring field migrations"
        }
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return {
            "status": "error", 
            "error": str(e),
            "message": "Continuous monitoring fields migration failed"
        }

if __name__ == "__main__":
    print("🔄 Starting continuous monitoring fields migration...")
    print(f"Timestamp: {datetime.now()}")
    print("=" * 60)
    
    result = run_migration()
    
    print("\n" + "=" * 60)
    print(f"Migration result: {result['status'].upper()}")
    
    if result["status"] == "error":
        sys.exit(1)
    else:
        print("✅ Ready for continuous monitoring!")
        sys.exit(0)