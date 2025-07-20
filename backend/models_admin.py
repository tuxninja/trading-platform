from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from database import Base

class User(Base):
    """User model for tracking authenticated users"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    picture_url = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserActivity(Base):
    """Track user activity for analytics"""
    __tablename__ = "user_activity"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)  # Foreign key to users table
    action = Column(String)  # login, trade_created, sentiment_analyzed, etc.
    endpoint = Column(String)  # API endpoint accessed
    ip_address = Column(String)
    user_agent = Column(Text)
    action_metadata = Column(JSON)  # Additional action-specific data
    timestamp = Column(DateTime, default=datetime.utcnow)

class SystemMetrics(Base):
    """System-wide metrics for monitoring"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String, index=True)
    metric_value = Column(Float)
    metric_unit = Column(String)  # requests/minute, percentage, count, etc.
    tags = Column(JSON)  # Additional categorization
    timestamp = Column(DateTime, default=datetime.utcnow)

class SystemAlerts(Base):
    """System alerts and notifications for admin"""
    __tablename__ = "system_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String)  # error, warning, info
    title = Column(String)
    message = Column(Text)
    source = Column(String)  # API endpoint, service name, etc.
    severity = Column(String)  # low, medium, high, critical
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String)  # Admin user who resolved
    alert_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

class FeatureFlags(Base):
    """Feature flags for A/B testing and gradual rollouts"""
    __tablename__ = "feature_flags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    is_enabled = Column(Boolean, default=False)
    rollout_percentage = Column(Float, default=0.0)  # 0-100
    target_users = Column(JSON)  # List of user IDs for targeted rollout
    conditions = Column(JSON)  # Additional conditions
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemConfiguration(Base):
    """System configuration settings"""
    __tablename__ = "system_configuration"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)
    value_type = Column(String)  # string, integer, float, boolean, json
    description = Column(Text)
    category = Column(String)  # trading, sentiment, api, system
    is_sensitive = Column(Boolean, default=False)  # Hide from logs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DataExports(Base):
    """Track data export requests"""
    __tablename__ = "data_exports"
    
    id = Column(Integer, primary_key=True, index=True)
    requested_by = Column(String)  # Admin user
    export_type = Column(String)  # users, trades, sentiment, system_metrics
    filters = Column(JSON)  # Export filters/parameters
    status = Column(String)  # pending, processing, completed, failed
    file_path = Column(String)  # Path to generated file
    file_size = Column(Integer)  # File size in bytes
    record_count = Column(Integer)  # Number of records exported
    error_message = Column(Text)
    requested_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)