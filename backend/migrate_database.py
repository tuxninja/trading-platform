"""
Database migration script to add new columns for the multi-strategy trading system.
This script safely adds missing columns to existing tables.
"""
import sqlite3
import logging
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Migrate database to add new columns for multi-strategy system."""
    
    # Database path
    db_path = os.getenv("DATABASE_URL", "sqlite:///./trading_app.db").replace("sqlite:///", "")
    
    logger.info(f"Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if database exists and has tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        logger.info(f"Found tables: {[t[0] for t in tables]}")
        
        migrations_applied = []
        
        # Migration 1: Add position_id to trades table
        try:
            cursor.execute("ALTER TABLE trades ADD COLUMN position_id INTEGER NULL;")
            migrations_applied.append("Added position_id to trades table")
            logger.info("✅ Added position_id column to trades table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logger.info("ℹ️ position_id column already exists in trades table")
            else:
                logger.error(f"❌ Error adding position_id to trades: {e}")
        
        # Migration 2: Create strategies table if it doesn't exist
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategies (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    strategy_type VARCHAR NOT NULL,
                    description TEXT,
                    parameters JSON,
                    is_active BOOLEAN DEFAULT 1,
                    allocation_percentage FLOAT DEFAULT 10.0,
                    max_positions INTEGER DEFAULT 5,
                    risk_level VARCHAR DEFAULT 'MEDIUM',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            migrations_applied.append("Created strategies table")
            logger.info("✅ Created strategies table")
        except Exception as e:
            logger.error(f"❌ Error creating strategies table: {e}")
        
        # Migration 3: Create positions table if it doesn't exist
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    strategy_id INTEGER REFERENCES strategies(id),
                    symbol VARCHAR NOT NULL,
                    entry_price FLOAT NOT NULL,
                    quantity INTEGER NOT NULL,
                    position_size FLOAT NOT NULL,
                    status VARCHAR DEFAULT 'OPEN',
                    entry_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    exit_timestamp TIMESTAMP NULL,
                    exit_price FLOAT NULL,
                    realized_pnl FLOAT NULL,
                    unrealized_pnl FLOAT NULL,
                    stop_loss_price FLOAT NULL,
                    take_profit_price FLOAT NULL,
                    max_hold_time INTEGER NULL,
                    trailing_stop_percentage FLOAT NULL,
                    entry_signal JSON NULL,
                    sentiment_at_entry FLOAT NULL,
                    market_conditions JSON NULL
                );
            """)
            migrations_applied.append("Created positions table")
            logger.info("✅ Created positions table")
        except Exception as e:
            logger.error(f"❌ Error creating positions table: {e}")
        
        # Migration 4: Create position_exit_events table if it doesn't exist
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS position_exit_events (
                    id INTEGER PRIMARY KEY,
                    position_id INTEGER REFERENCES positions(id),
                    exit_type VARCHAR NOT NULL,
                    trigger_price FLOAT NOT NULL,
                    quantity_closed INTEGER NOT NULL,
                    exit_price FLOAT NOT NULL,
                    realized_pnl FLOAT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT
                );
            """)
            migrations_applied.append("Created position_exit_events table")
            logger.info("✅ Created position_exit_events table")
        except Exception as e:
            logger.error(f"❌ Error creating position_exit_events table: {e}")
        
        # Migration 5: Create strategy_performance table if it doesn't exist
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_performance (
                    id INTEGER PRIMARY KEY,
                    strategy_id INTEGER REFERENCES strategies(id),
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_positions INTEGER DEFAULT 0,
                    open_positions INTEGER DEFAULT 0,
                    closed_positions INTEGER DEFAULT 0,
                    winning_positions INTEGER DEFAULT 0,
                    losing_positions INTEGER DEFAULT 0,
                    total_pnl FLOAT DEFAULT 0.0,
                    unrealized_pnl FLOAT DEFAULT 0.0,
                    realized_pnl FLOAT DEFAULT 0.0,
                    win_rate FLOAT DEFAULT 0.0,
                    average_win FLOAT DEFAULT 0.0,
                    average_loss FLOAT DEFAULT 0.0,
                    profit_factor FLOAT DEFAULT 0.0,
                    max_drawdown FLOAT DEFAULT 0.0,
                    sharpe_ratio FLOAT NULL,
                    allocated_capital FLOAT DEFAULT 0.0,
                    utilized_capital FLOAT DEFAULT 0.0,
                    available_capital FLOAT DEFAULT 0.0
                );
            """)
            migrations_applied.append("Created strategy_performance table")
            logger.info("✅ Created strategy_performance table")
        except Exception as e:
            logger.error(f"❌ Error creating strategy_performance table: {e}")
        
        # Migration 6: Create scheduled_tasks table if it doesn't exist
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id INTEGER PRIMARY KEY,
                    task_type VARCHAR NOT NULL,
                    strategy_id INTEGER REFERENCES strategies(id),
                    schedule_expression VARCHAR NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    last_run TIMESTAMP NULL,
                    next_run TIMESTAMP NULL,
                    run_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    last_error TEXT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            migrations_applied.append("Created scheduled_tasks table")
            logger.info("✅ Created scheduled_tasks table")
        except Exception as e:
            logger.error(f"❌ Error creating scheduled_tasks table: {e}")
        
        # Commit all changes
        conn.commit()
        
        # Verify tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        final_tables = [t[0] for t in cursor.fetchall()]
        logger.info(f"Final tables: {final_tables}")
        
        # Record migration in a migrations table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY,
                    migration_name VARCHAR NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            for migration in migrations_applied:
                cursor.execute(
                    "INSERT INTO migrations (migration_name) VALUES (?)",
                    (migration,)
                )
            
            conn.commit()
            logger.info("✅ Recorded migrations in migrations table")
        except Exception as e:
            logger.error(f"❌ Error recording migrations: {e}")
        
        logger.info(f"🎉 Database migration completed successfully!")
        logger.info(f"Applied {len(migrations_applied)} migrations:")
        for migration in migrations_applied:
            logger.info(f"  - {migration}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("✅ Database migration completed successfully")
        exit(0)
    else:
        print("❌ Database migration failed")
        exit(1)