#!/usr/bin/env python3
"""
System Backup Script for Trading Platform
Handles database backups, file system backups, and verification
"""

import os
import sys
import subprocess
import datetime
import json
import logging
import shutil
import gzip
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupManager:
    """Manages all backup operations for the trading platform"""
    
    def __init__(self, config_file: str = 'backup_config.json'):
        self.config = self.load_config(config_file)
        self.backup_date = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = Path(self.config['backup_dir']) / self.backup_date
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def load_config(self, config_file: str) -> Dict:
        """Load backup configuration"""
        default_config = {
            "backup_dir": "/backups/trading_platform",
            "database": {
                "type": "sqlite",  # or postgresql
                "name": "trading_app.db",
                "host": "localhost",
                "port": 5432,
                "user": "postgres",
                "password": ""
            },
            "retention": {
                "daily": 7,    # Keep 7 daily backups
                "weekly": 4,   # Keep 4 weekly backups
                "monthly": 12  # Keep 12 monthly backups
            },
            "directories": [
                "backend",
                "frontend/build",
                "docs"
            ],
            "exclude_patterns": [
                "*.log",
                "node_modules",
                "__pycache__",
                "*.pyc",
                ".git",
                "venv"
            ]
        }
        
        try:
            if Path(config_file).exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                # Create default config file
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default config file: {config_file}")
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return default_config
    
    def backup_database(self) -> bool:
        """Backup the database"""
        logger.info("Starting database backup...")
        
        try:
            db_config = self.config['database']
            backup_file = self.backup_dir / f"database_{self.backup_date}.sql"
            
            if db_config['type'] == 'sqlite':
                # SQLite backup
                source_db = Path(db_config['name'])
                if not source_db.exists():
                    source_db = Path('backend') / db_config['name']
                
                if source_db.exists():
                    shutil.copy2(source_db, backup_file.with_suffix('.db'))
                    
                    # Also create SQL dump
                    cmd = f"sqlite3 {source_db} .dump"
                    with open(backup_file, 'w') as f:
                        subprocess.run(cmd, shell=True, stdout=f, check=True)
                    
                    # Compress the backup
                    with open(backup_file, 'rb') as f_in:
                        with gzip.open(backup_file.with_suffix('.sql.gz'), 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    backup_file.unlink()  # Remove uncompressed version
                    logger.info(f"SQLite backup completed: {backup_file.with_suffix('.sql.gz')}")
                    return True
                else:
                    logger.error(f"Database file not found: {source_db}")
                    return False
                    
            elif db_config['type'] == 'postgresql':
                # PostgreSQL backup
                env = os.environ.copy()
                env['PGPASSWORD'] = db_config['password']
                
                cmd = [
                    'pg_dump',
                    '-h', db_config['host'],
                    '-p', str(db_config['port']),
                    '-U', db_config['user'],
                    '-d', db_config['name'],
                    '--no-password'
                ]
                
                with open(backup_file, 'w') as f:
                    subprocess.run(cmd, stdout=f, env=env, check=True)
                
                # Compress the backup
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(backup_file.with_suffix('.sql.gz'), 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                backup_file.unlink()  # Remove uncompressed version
                logger.info(f"PostgreSQL backup completed: {backup_file.with_suffix('.sql.gz')}")
                return True
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Database backup failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Database backup error: {e}")
            return False
    
    def backup_files(self) -> bool:
        """Backup application files"""
        logger.info("Starting file system backup...")
        
        try:
            files_backup_dir = self.backup_dir / "files"
            files_backup_dir.mkdir(exist_ok=True)
            
            for directory in self.config['directories']:
                source_path = Path(directory)
                if not source_path.exists():
                    logger.warning(f"Directory not found: {source_path}")
                    continue
                
                dest_path = files_backup_dir / directory
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Create exclude patterns for rsync
                exclude_file = self.backup_dir / "exclude_patterns.txt"
                with open(exclude_file, 'w') as f:
                    for pattern in self.config['exclude_patterns']:
                        f.write(f"{pattern}\n")
                
                # Use rsync for efficient copying
                cmd = [
                    'rsync', '-av',
                    f'--exclude-from={exclude_file}',
                    f'{source_path}/',
                    f'{dest_path}/'
                ]
                
                subprocess.run(cmd, check=True)
                logger.info(f"Backed up directory: {directory}")
            
            # Create tarball of files
            tarball_path = self.backup_dir / f"files_{self.backup_date}.tar.gz"
            cmd = ['tar', '-czf', str(tarball_path), '-C', str(files_backup_dir), '.']
            subprocess.run(cmd, check=True)
            
            # Remove uncompressed files directory
            shutil.rmtree(files_backup_dir)
            
            logger.info(f"File backup completed: {tarball_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"File backup failed: {e}")
            return False
        except Exception as e:
            logger.error(f"File backup error: {e}")
            return False
    
    def create_backup_manifest(self) -> bool:
        """Create a manifest file with backup details"""
        try:
            manifest = {
                "backup_date": self.backup_date,
                "timestamp": datetime.datetime.now().isoformat(),
                "backup_dir": str(self.backup_dir),
                "files": [],
                "database_backed_up": False,
                "files_backed_up": False,
                "total_size_bytes": 0
            }
            
            # Calculate sizes and list files
            total_size = 0
            for file_path in self.backup_dir.iterdir():
                if file_path.is_file():
                    size = file_path.stat().st_size
                    total_size += size
                    manifest["files"].append({
                        "name": file_path.name,
                        "size_bytes": size,
                        "size_human": self.format_bytes(size)
                    })
                    
                    if file_path.suffix == '.gz' and 'database' in file_path.name:
                        manifest["database_backed_up"] = True
                    elif 'files' in file_path.name:
                        manifest["files_backed_up"] = True
            
            manifest["total_size_bytes"] = total_size
            manifest["total_size_human"] = self.format_bytes(total_size)
            
            # Save manifest
            manifest_path = self.backup_dir / "backup_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Backup manifest created: {manifest_path}")
            logger.info(f"Total backup size: {manifest['total_size_human']}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating manifest: {e}")
            return False
    
    def verify_backup(self) -> bool:
        """Verify backup integrity"""
        logger.info("Verifying backup integrity...")
        
        try:
            manifest_path = self.backup_dir / "backup_manifest.json"
            if not manifest_path.exists():
                logger.error("Backup manifest not found")
                return False
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Verify all files exist and have correct sizes
            for file_info in manifest["files"]:
                file_path = self.backup_dir / file_info["name"]
                if not file_path.exists():
                    logger.error(f"Backup file missing: {file_info['name']}")
                    return False
                
                actual_size = file_path.stat().st_size
                if actual_size != file_info["size_bytes"]:
                    logger.error(f"Size mismatch for {file_info['name']}: expected {file_info['size_bytes']}, got {actual_size}")
                    return False
            
            # Test database backup if it exists
            for file_info in manifest["files"]:
                if "database" in file_info["name"] and file_info["name"].endswith(".gz"):
                    db_backup_path = self.backup_dir / file_info["name"]
                    try:
                        # Test gzip file integrity
                        with gzip.open(db_backup_path, 'rt') as f:
                            # Read first few lines to verify it's valid SQL
                            first_lines = [f.readline() for _ in range(5)]
                            if not any("CREATE" in line or "INSERT" in line or "PRAGMA" in line for line in first_lines):
                                logger.warning("Database backup may be corrupted - no SQL statements found")
                    except Exception as e:
                        logger.error(f"Database backup verification failed: {e}")
                        return False
            
            logger.info("Backup verification completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Backup verification error: {e}")
            return False
    
    def cleanup_old_backups(self) -> bool:
        """Clean up old backups according to retention policy"""
        logger.info("Cleaning up old backups...")
        
        try:
            backup_root = Path(self.config['backup_dir'])
            if not backup_root.exists():
                return True
            
            retention = self.config['retention']
            now = datetime.datetime.now()
            
            # Get all backup directories
            backup_dirs = [d for d in backup_root.iterdir() if d.is_dir() and self.is_backup_dir(d.name)]
            backup_dirs.sort(key=lambda x: x.name, reverse=True)  # Newest first
            
            # Separate into daily, weekly, monthly
            daily_backups = []
            weekly_backups = []
            monthly_backups = []
            
            for backup_dir in backup_dirs:
                try:
                    backup_date = datetime.datetime.strptime(backup_dir.name, '%Y%m%d_%H%M%S')
                    days_old = (now - backup_date).days
                    
                    if days_old == 0:  # Today's backup
                        daily_backups.append(backup_dir)
                    elif days_old < 7:  # This week
                        daily_backups.append(backup_dir)
                    elif days_old < 30:  # This month
                        weekly_backups.append(backup_dir)
                    else:  # Older
                        monthly_backups.append(backup_dir)
                        
                except ValueError:
                    # Skip directories that don't match backup format
                    continue
            
            # Keep only specified number of each type
            to_delete = []
            
            if len(daily_backups) > retention['daily']:
                to_delete.extend(daily_backups[retention['daily']:])
            
            if len(weekly_backups) > retention['weekly']:
                to_delete.extend(weekly_backups[retention['weekly']:])
            
            if len(monthly_backups) > retention['monthly']:
                to_delete.extend(monthly_backups[retention['monthly']:])
            
            # Delete old backups
            for backup_dir in to_delete:
                logger.info(f"Deleting old backup: {backup_dir.name}")
                shutil.rmtree(backup_dir)
            
            logger.info(f"Cleanup completed. Deleted {len(to_delete)} old backups")
            return True
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return False
    
    def is_backup_dir(self, dirname: str) -> bool:
        """Check if directory name matches backup format"""
        try:
            datetime.datetime.strptime(dirname, '%Y%m%d_%H%M%S')
            return True
        except ValueError:
            return False
    
    def format_bytes(self, bytes_count: int) -> str:
        """Format bytes as human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"
    
    def run_full_backup(self) -> bool:
        """Run complete backup process"""
        logger.info(f"Starting full backup process - {self.backup_date}")
        
        success = True
        
        # Database backup
        if not self.backup_database():
            success = False
        
        # File system backup
        if not self.backup_files():
            success = False
        
        # Create manifest
        if not self.create_backup_manifest():
            success = False
        
        # Verify backup
        if success and not self.verify_backup():
            success = False
        
        # Cleanup old backups
        if not self.cleanup_old_backups():
            logger.warning("Cleanup failed, but backup was successful")
        
        if success:
            logger.info(f"✅ Full backup completed successfully: {self.backup_dir}")
        else:
            logger.error(f"❌ Backup completed with errors: {self.backup_dir}")
        
        return success

def main():
    parser = argparse.ArgumentParser(description='Trading Platform Backup Manager')
    parser.add_argument('--config', default='backup_config.json', help='Backup configuration file')
    parser.add_argument('--database-only', action='store_true', help='Backup database only')
    parser.add_argument('--files-only', action='store_true', help='Backup files only')
    parser.add_argument('--verify-only', action='store_true', help='Verify existing backups only')
    parser.add_argument('--cleanup-only', action='store_true', help='Cleanup old backups only')
    
    args = parser.parse_args()
    
    backup_manager = BackupManager(args.config)
    
    if args.verify_only:
        # Find latest backup and verify
        backup_root = Path(backup_manager.config['backup_dir'])
        latest_backup = None
        for d in sorted(backup_root.iterdir(), reverse=True):
            if d.is_dir() and backup_manager.is_backup_dir(d.name):
                latest_backup = d
                break
        
        if latest_backup:
            backup_manager.backup_dir = latest_backup
            success = backup_manager.verify_backup()
        else:
            logger.error("No backups found to verify")
            success = False
            
    elif args.cleanup_only:
        success = backup_manager.cleanup_old_backups()
        
    elif args.database_only:
        success = backup_manager.backup_database() and backup_manager.create_backup_manifest()
        
    elif args.files_only:
        success = backup_manager.backup_files() and backup_manager.create_backup_manifest()
        
    else:
        success = backup_manager.run_full_backup()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()