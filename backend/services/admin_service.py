from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc, text
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import logging
import psutil
import os
from pathlib import Path

from models import Trade, SentimentData, StockData, TradeRecommendation
from models_admin import (
    User, UserActivity, SystemMetrics, SystemAlerts, 
    FeatureFlags, SystemConfiguration, DataExports
)
from database import engine

logger = logging.getLogger(__name__)

class AdminService:
    """Service for admin console functionality"""
    
    def __init__(self):
        self.logger = logger
    
    # User Management
    def get_user_stats(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        
        # Users registered in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_users = db.query(User).filter(User.created_at >= thirty_days_ago).count()
        
        # Users active in last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        weekly_active = db.query(User).filter(User.last_login >= seven_days_ago).count()
        
        # Users active in last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        daily_active = db.query(User).filter(User.last_login >= yesterday).count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "new_users_30d": new_users,
            "weekly_active_users": weekly_active,
            "daily_active_users": daily_active,
            "churn_rate": round((total_users - weekly_active) / max(total_users, 1) * 100, 2)
        }
    
    def get_users(self, db: Session, limit: int = 50, offset: int = 0, 
                  search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get paginated list of users with search"""
        query = db.query(User)
        
        if search:
            query = query.filter(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.name.ilike(f"%{search}%")
                )
            )
        
        users = query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()
        
        return [
            {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "last_login": user.last_login,
                "created_at": user.created_at,
                "picture_url": user.picture_url
            }
            for user in users
        ]
    
    def get_user_activity(self, db: Session, user_id: Optional[int] = None, 
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Get user activity logs"""
        query = db.query(UserActivity)
        
        if user_id:
            query = query.filter(UserActivity.user_id == user_id)
        
        activities = query.order_by(desc(UserActivity.timestamp)).limit(limit).all()
        
        return [
            {
                "id": activity.id,
                "user_id": activity.user_id,
                "action": activity.action,
                "endpoint": activity.endpoint,
                "ip_address": activity.ip_address,
                "timestamp": activity.timestamp,
                "metadata": activity.metadata
            }
            for activity in activities
        ]
    
    # System Health & Monitoring
    def get_system_health(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive system health metrics"""
        # Database health
        try:
            db.execute(text("SELECT 1"))
            db_status = "healthy"
            db_response_time = "< 1ms"  # Could be measured
        except Exception as e:
            db_status = "error"
            db_response_time = "timeout"
            self.logger.error(f"Database health check failed: {e}")
        
        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Recent alerts
        recent_alerts = db.query(SystemAlerts).filter(
            and_(
                SystemAlerts.created_at >= datetime.utcnow() - timedelta(hours=24),
                SystemAlerts.is_resolved == False
            )
        ).count()
        
        # API performance (last 24 hours)
        api_metrics = self.get_api_performance_summary(db)
        
        return {
            "database": {
                "status": db_status,
                "response_time": db_response_time
            },
            "system_resources": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": f"{memory.available / (1024**3):.1f} GB",
                "disk_percent": disk.percent,
                "disk_free": f"{disk.free / (1024**3):.1f} GB"
            },
            "alerts": {
                "unresolved_count": recent_alerts,
                "severity_distribution": self.get_alert_severity_distribution(db)
            },
            "api_performance": api_metrics
        }
    
    def get_api_performance_summary(self, db: Session) -> Dict[str, Any]:
        """Get API performance metrics summary"""
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        # Get recent metrics
        metrics = db.query(SystemMetrics).filter(
            and_(
                SystemMetrics.timestamp >= yesterday,
                SystemMetrics.metric_name.in_([
                    'api_requests_per_minute',
                    'api_response_time_avg',
                    'api_error_rate'
                ])
            )
        ).all()
        
        # Aggregate metrics
        summary = {
            "total_requests_24h": 0,
            "avg_response_time": 0,
            "error_rate": 0,
            "requests_per_minute": 0
        }
        
        for metric in metrics:
            if metric.metric_name == 'api_requests_per_minute':
                summary["requests_per_minute"] = metric.metric_value
                summary["total_requests_24h"] += metric.metric_value
            elif metric.metric_name == 'api_response_time_avg':
                summary["avg_response_time"] = metric.metric_value
            elif metric.metric_name == 'api_error_rate':
                summary["error_rate"] = metric.metric_value
        
        return summary
    
    def get_alert_severity_distribution(self, db: Session) -> Dict[str, int]:
        """Get distribution of alert severities"""
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        alerts = db.query(
            SystemAlerts.severity,
            func.count(SystemAlerts.id).label('count')
        ).filter(
            SystemAlerts.created_at >= yesterday
        ).group_by(SystemAlerts.severity).all()
        
        return {alert.severity: alert.count for alert in alerts}
    
    # Trading Platform Oversight
    def get_platform_metrics(self, db: Session) -> Dict[str, Any]:
        """Get platform-wide trading metrics"""
        # Total trades
        total_trades = db.query(Trade).count()
        
        # Trades in last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        daily_trades = db.query(Trade).filter(Trade.timestamp >= yesterday).count()
        
        # Open vs closed trades
        open_trades = db.query(Trade).filter(Trade.status == 'OPEN').count()
        closed_trades = db.query(Trade).filter(Trade.status == 'CLOSED').count()
        
        # Total portfolio value across all users
        total_portfolio_value = db.query(func.sum(Trade.total_value)).filter(
            Trade.status == 'OPEN'
        ).scalar() or 0
        
        # Most traded symbols
        top_symbols = db.query(
            Trade.symbol,
            func.count(Trade.id).label('trade_count'),
            func.sum(Trade.total_value).label('total_value')
        ).group_by(Trade.symbol).order_by(desc('trade_count')).limit(10).all()
        
        # Sentiment analysis stats
        sentiment_count = db.query(SentimentData).count()
        recent_sentiment = db.query(SentimentData).filter(
            SentimentData.timestamp >= yesterday
        ).count()
        
        return {
            "trades": {
                "total": total_trades,
                "daily": daily_trades,
                "open": open_trades,
                "closed": closed_trades,
                "total_portfolio_value": total_portfolio_value
            },
            "top_symbols": [
                {
                    "symbol": symbol.symbol,
                    "trade_count": symbol.trade_count,
                    "total_value": float(symbol.total_value or 0)
                }
                for symbol in top_symbols
            ],
            "sentiment": {
                "total_analyses": sentiment_count,
                "daily_analyses": recent_sentiment
            }
        }
    
    # Configuration Management
    def get_feature_flags(self, db: Session) -> List[Dict[str, Any]]:
        """Get all feature flags"""
        flags = db.query(FeatureFlags).order_by(FeatureFlags.name).all()
        
        return [
            {
                "id": flag.id,
                "name": flag.name,
                "description": flag.description,
                "is_enabled": flag.is_enabled,
                "rollout_percentage": flag.rollout_percentage,
                "target_users": flag.target_users,
                "created_at": flag.created_at,
                "updated_at": flag.updated_at
            }
            for flag in flags
        ]
    
    def update_feature_flag(self, db: Session, flag_id: int, 
                           is_enabled: bool, rollout_percentage: float) -> Dict[str, Any]:
        """Update a feature flag"""
        flag = db.query(FeatureFlags).filter(FeatureFlags.id == flag_id).first()
        if not flag:
            raise ValueError("Feature flag not found")
        
        flag.is_enabled = is_enabled
        flag.rollout_percentage = rollout_percentage
        flag.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(flag)
        
        return {"message": "Feature flag updated successfully"}
    
    def get_system_config(self, db: Session, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get system configuration"""
        query = db.query(SystemConfiguration)
        
        if category:
            query = query.filter(SystemConfiguration.category == category)
        
        configs = query.order_by(SystemConfiguration.category, SystemConfiguration.key).all()
        
        return [
            {
                "id": config.id,
                "key": config.key,
                "value": config.value if not config.is_sensitive else "***",
                "value_type": config.value_type,
                "description": config.description,
                "category": config.category,
                "updated_at": config.updated_at
            }
            for config in configs
        ]
    
    # Data Management
    def create_data_export(self, db: Session, export_type: str, 
                          filters: Dict[str, Any], requested_by: str) -> Dict[str, Any]:
        """Create a data export request"""
        export = DataExports(
            requested_by=requested_by,
            export_type=export_type,
            filters=filters,
            status="pending"
        )
        
        db.add(export)
        db.commit()
        db.refresh(export)
        
        # TODO: Implement async export processing
        # For now, return the export request
        return {
            "export_id": export.id,
            "status": export.status,
            "message": "Export request created successfully"
        }
    
    def get_data_exports(self, db: Session) -> List[Dict[str, Any]]:
        """Get all data export requests"""
        exports = db.query(DataExports).order_by(desc(DataExports.requested_at)).all()
        
        return [
            {
                "id": export.id,
                "export_type": export.export_type,
                "status": export.status,
                "requested_by": export.requested_by,
                "file_size": export.file_size,
                "record_count": export.record_count,
                "requested_at": export.requested_at,
                "completed_at": export.completed_at
            }
            for export in exports
        ]
    
    # Analytics
    def get_usage_analytics(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """Get platform usage analytics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily active users
        daily_users = db.query(
            func.date(UserActivity.timestamp).label('date'),
            func.count(func.distinct(UserActivity.user_id)).label('active_users')
        ).filter(
            UserActivity.timestamp >= start_date
        ).group_by(func.date(UserActivity.timestamp)).all()
        
        # Feature usage
        feature_usage = db.query(
            UserActivity.action,
            func.count(UserActivity.id).label('usage_count')
        ).filter(
            UserActivity.timestamp >= start_date
        ).group_by(UserActivity.action).order_by(desc('usage_count')).all()
        
        # API endpoint usage
        endpoint_usage = db.query(
            UserActivity.endpoint,
            func.count(UserActivity.id).label('request_count')
        ).filter(
            UserActivity.timestamp >= start_date
        ).group_by(UserActivity.endpoint).order_by(desc('request_count')).limit(20).all()
        
        return {
            "daily_active_users": [
                {"date": str(day.date), "active_users": day.active_users}
                for day in daily_users
            ],
            "feature_usage": [
                {"action": usage.action, "count": usage.usage_count}
                for usage in feature_usage
            ],
            "top_endpoints": [
                {"endpoint": endpoint.endpoint, "count": endpoint.request_count}
                for endpoint in endpoint_usage
            ]
        }