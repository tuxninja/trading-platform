#!/usr/bin/env python3
"""
Database Update and Migration Script for Trading Platform
Handles schema updates, data migrations, and admin user management
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

from database import Base, engine, get_db
from models import Trade, SentimentData, StockData, TradeRecommendation
from models_admin import User, UserActivity, SystemMetrics, SystemAlerts, FeatureFlags, SystemConfiguration, DataExports

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database updates and migrations"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.inspector = inspect(engine)
    
    def check_database_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def backup_before_migration(self) -> bool:
        """Create backup before running migrations"""
        logger.info("Creating backup before migration...")
        
        try:
            # Import and run backup script
            from backup_system import BackupManager
            backup_manager = BackupManager()
            success = backup_manager.backup_database()
            
            if success:
                logger.info("✅ Pre-migration backup completed")
            else:
                logger.error("❌ Pre-migration backup failed")
            
            return success
        except Exception as e:
            logger.error(f"Backup error: {e}")
            return False
    
    def get_existing_tables(self) -> list:
        """Get list of existing tables"""
        try:
            return self.inspector.get_table_names()
        except Exception as e:
            logger.error(f"Error getting table names: {e}")
            return []
    
    def create_missing_tables(self) -> bool:
        """Create any missing tables"""
        logger.info("Checking for missing tables...")
        
        try:
            existing_tables = set(self.get_existing_tables())
            
            # Get all table names from models
            Base.metadata.bind = self.engine
            all_tables = set(Base.metadata.tables.keys())
            
            missing_tables = all_tables - existing_tables
            
            if missing_tables:
                logger.info(f"Creating missing tables: {missing_tables}")
                Base.metadata.create_all(bind=self.engine)
                logger.info("✅ Missing tables created successfully")
            else:
                logger.info("✅ All tables already exist")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False
    
    def run_schema_migrations(self) -> bool:
        """Run schema migrations"""
        logger.info("Running schema migrations...")
        
        migrations = [
            self._add_admin_columns_to_users,
            self._create_admin_tables,
            self._add_indexes_for_performance,
            self._add_feature_flags_table,
            self._update_existing_data_types
        ]
        
        try:
            for migration in migrations:
                migration()
            
            logger.info("✅ All schema migrations completed")
            return True
            
        except Exception as e:
            logger.error(f"Schema migration error: {e}")
            return False
    
    def _add_admin_columns_to_users(self):
        """Add admin columns to users table if they don't exist"""
        try:
            # Check if users table exists and has admin columns
            if 'users' in self.get_existing_tables():
                columns = [col['name'] for col in self.inspector.get_columns('users')]
                
                if 'is_admin' not in columns:
                    logger.info("Adding is_admin column to users table")
                    with self.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
                        conn.commit()
                
                if 'last_login' not in columns:
                    logger.info("Adding last_login column to users table")
                    with self.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE users ADD COLUMN last_login TIMESTAMP"))
                        conn.commit()
                        
        except Exception as e:
            logger.warning(f"Could not add admin columns: {e}")
    
    def _create_admin_tables(self):
        """Create admin-related tables"""
        logger.info("Creating admin tables...")
        
        admin_tables = [
            'user_activity', 'system_metrics', 'system_alerts',
            'feature_flags', 'system_configuration', 'data_exports'
        ]
        
        existing_tables = self.get_existing_tables()
        
        for table_name in admin_tables:
            if table_name not in existing_tables:
                logger.info(f"Admin table {table_name} will be created")
    
    def _add_indexes_for_performance(self):
        """Add database indexes for better performance"""
        logger.info("Adding performance indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_trades_user_timestamp ON trades(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_sentiment_symbol_timestamp ON sentiment_data(symbol, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_user_activity_user_timestamp ON user_activity(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_name_timestamp ON system_metrics(metric_name, timestamp)"
        ]
        
        try:
            with self.engine.connect() as conn:
                for index_sql in indexes:
                    try:
                        conn.execute(text(index_sql))
                        logger.info(f"✅ Created index: {index_sql.split(' ')[-1]}")
                    except Exception as e:
                        logger.warning(f"Index creation skipped: {e}")
                conn.commit()
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def _add_feature_flags_table(self):
        """Add feature flags table"""
        if 'feature_flags' not in self.get_existing_tables():
            logger.info("Feature flags table will be created")
    
    def _update_existing_data_types(self):
        """Update any data types that need modification"""
        # This method would contain any specific data type updates
        pass
    
    def create_admin_user(self, email: str, name: str = None, google_id: str = None) -> bool:
        """Create or update admin user"""
        logger.info(f"Creating/updating admin user: {email}")
        
        try:
            db = next(get_db())
            
            # Check if user exists
            user = db.query(User).filter(User.email == email).first()
            
            if user:
                # Update existing user
                user.is_admin = True
                user.updated_at = datetime.utcnow()
                if name:
                    user.name = name
                if google_id:
                    user.google_id = google_id
                logger.info(f"✅ Updated existing user {email} to admin")
            else:
                # Create new user
                user = User(
                    email=email,
                    name=name or "Admin User",
                    google_id=google_id or f"admin_{email}",
                    is_admin=True,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(user)
                logger.info(f"✅ Created new admin user: {email}")
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error creating admin user: {e}")
            return False
    
    def seed_initial_data(self) -> bool:
        """Seed database with initial configuration data"""
        logger.info("Seeding initial data...")
        
        try:
            db = next(get_db())
            
            # Add default feature flags
            default_flags = [
                {
                    'name': 'sentiment_analysis',
                    'description': 'Enable sentiment analysis features',
                    'is_enabled': True,
                    'rollout_percentage': 100.0
                },
                {
                    'name': 'advanced_trading',
                    'description': 'Enable advanced trading features',
                    'is_enabled': True,
                    'rollout_percentage': 100.0
                },
                {
                    'name': 'admin_dashboard',
                    'description': 'Enable admin dashboard',
                    'is_enabled': True,
                    'rollout_percentage': 100.0
                },
                {
                    'name': 'data_exports',
                    'description': 'Enable data export functionality',
                    'is_enabled': True,
                    'rollout_percentage': 100.0
                }
            ]
            
            for flag_data in default_flags:
                existing_flag = db.query(FeatureFlags).filter(FeatureFlags.name == flag_data['name']).first()
                if not existing_flag:
                    flag = FeatureFlags(
                        name=flag_data['name'],
                        description=flag_data['description'],
                        is_enabled=flag_data['is_enabled'],
                        rollout_percentage=flag_data['rollout_percentage'],
                        created_by='system',
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(flag)
                    logger.info(f"✅ Added feature flag: {flag_data['name']}")
            
            # Add default system configuration
            default_configs = [
                {
                    'key': 'max_trades_per_user_daily',
                    'value': '100',
                    'value_type': 'integer',
                    'description': 'Maximum trades per user per day',
                    'category': 'trading'
                },
                {
                    'key': 'sentiment_analysis_interval_minutes',
                    'value': '60',
                    'value_type': 'integer',
                    'description': 'How often to run sentiment analysis',
                    'category': 'sentiment'
                },
                {
                    'key': 'api_rate_limit_per_minute',
                    'value': '100',
                    'value_type': 'integer',
                    'description': 'API requests per minute per user',
                    'category': 'api'
                },
                {
                    'key': 'maintenance_mode',
                    'value': 'false',
                    'value_type': 'boolean',
                    'description': 'Enable maintenance mode',
                    'category': 'system'
                }
            ]
            
            for config_data in default_configs:
                existing_config = db.query(SystemConfiguration).filter(
                    SystemConfiguration.key == config_data['key']
                ).first()
                if not existing_config:
                    config = SystemConfiguration(
                        key=config_data['key'],
                        value=config_data['value'],
                        value_type=config_data['value_type'],
                        description=config_data['description'],
                        category=config_data['category'],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(config)
                    logger.info(f"✅ Added system config: {config_data['key']}")
            
            db.commit()
            logger.info("✅ Initial data seeding completed")
            return True
            
        except Exception as e:
            logger.error(f"Error seeding initial data: {e}")
            return False
    
    def vacuum_and_analyze(self) -> bool:
        """Optimize database performance"""
        logger.info("Running database optimization...")
        
        try:
            with self.engine.connect() as conn:
                # For SQLite
                if 'sqlite' in str(self.engine.url):
                    conn.execute(text("VACUUM"))
                    conn.execute(text("ANALYZE"))
                # For PostgreSQL
                elif 'postgresql' in str(self.engine.url):
                    conn.execute(text("VACUUM ANALYZE"))
                
                logger.info("✅ Database optimization completed")
            return True
            
        except Exception as e:
            logger.error(f"Database optimization error: {e}")
            return False
    
    def run_full_update(self, create_backup: bool = True, admin_email: str = None) -> bool:
        """Run complete database update process"""
        logger.info("🚀 Starting database update process")
        
        # Check connection
        if not self.check_database_connection():
            return False
        
        # Create backup if requested
        if create_backup:
            if not self.backup_before_migration():
                logger.warning("Backup failed, continuing with migration...")
        
        # Create missing tables
        if not self.create_missing_tables():
            return False
        
        # Run schema migrations
        if not self.run_schema_migrations():
            return False
        
        # Seed initial data
        if not self.seed_initial_data():
            return False
        
        # Create admin user if email provided
        if admin_email:
            if not self.create_admin_user(admin_email):
                logger.warning("Admin user creation failed")
        
        # Optimize database
        if not self.vacuum_and_analyze():
            logger.warning("Database optimization failed")
        
        logger.info("✅ Database update process completed successfully")
        return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Trading Platform Database Manager')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup creation')
    parser.add_argument('--admin-email', type=str, help='Create admin user with this email')
    parser.add_argument('--tables-only', action='store_true', help='Only create missing tables')
    parser.add_argument('--migrations-only', action='store_true', help='Only run migrations')
    parser.add_argument('--seed-only', action='store_true', help='Only seed initial data')
    parser.add_argument('--optimize-only', action='store_true', help='Only optimize database')
    
    args = parser.parse_args()
    
    db_manager = DatabaseManager()
    
    if args.tables_only:
        success = db_manager.create_missing_tables()
    elif args.migrations_only:
        success = db_manager.run_schema_migrations()
    elif args.seed_only:
        success = db_manager.seed_initial_data()
    elif args.optimize_only:
        success = db_manager.vacuum_and_analyze()
    else:
        success = db_manager.run_full_update(
            create_backup=not args.no_backup,
            admin_email=args.admin_email
        )
    
    if success:
        print("✅ Database update completed successfully")
        sys.exit(0)
    else:
        print("❌ Database update failed")
        sys.exit(1)

if __name__ == '__main__':
    main()