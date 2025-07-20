from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from database import get_db
from auth import get_current_user
from services.admin_service import AdminService
from models_admin import User

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])
admin_service = AdminService()

def require_admin(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Dependency to require admin privileges"""
    # Check if user is admin in database
    user = db.query(User).filter(User.google_id == current_user["user_id"]).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

# Dashboard Overview
@admin_router.get("/dashboard")
async def get_admin_dashboard(
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard overview with key metrics"""
    try:
        dashboard_data = {
            "user_stats": admin_service.get_user_stats(db),
            "system_health": admin_service.get_system_health(db),
            "platform_metrics": admin_service.get_platform_metrics(db),
            "recent_activity": admin_service.get_user_activity(db, limit=10)
        }
        
        return dashboard_data
    
    except Exception as e:
        logger.error(f"Error fetching admin dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard data")

# User Management
@admin_router.get("/users")
async def get_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get paginated list of users with optional search"""
    try:
        users = admin_service.get_users(db, limit=limit, offset=offset, search=search)
        total_count = db.query(User).count()
        
        return {
            "users": users,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")

@admin_router.get("/users/{user_id}/activity")
async def get_user_activity(
    user_id: int,
    limit: int = Query(100, ge=1, le=500),
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get activity logs for a specific user"""
    try:
        activity = admin_service.get_user_activity(db, user_id=user_id, limit=limit)
        return {"activity": activity}
    
    except Exception as e:
        logger.error(f"Error fetching user activity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch user activity")

@admin_router.post("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool = Body(..., embed=True),
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user active status"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = is_active
        user.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "User status updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update user status")

@admin_router.post("/users/{user_id}/admin")
async def update_user_admin_status(
    user_id: int,
    is_admin: bool = Body(..., embed=True),
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Grant or revoke admin privileges"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_admin = is_admin
        user.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "User admin status updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user admin status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update admin status")

# System Health & Monitoring
@admin_router.get("/health")
async def get_system_health(
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive system health metrics"""
    try:
        health_data = admin_service.get_system_health(db)
        return health_data
    
    except Exception as e:
        logger.error(f"Error fetching system health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch system health")

@admin_router.get("/metrics")
async def get_system_metrics(
    metric_name: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system metrics for specified time period"""
    try:
        # This would be implemented in admin_service
        # For now, return placeholder
        return {
            "metrics": [],
            "time_range": f"Last {hours} hours",
            "message": "Metrics endpoint placeholder"
        }
    
    except Exception as e:
        logger.error(f"Error fetching metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")

# Platform Analytics
@admin_router.get("/analytics/usage")
async def get_usage_analytics(
    days: int = Query(30, ge=1, le=365),
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get platform usage analytics"""
    try:
        analytics = admin_service.get_usage_analytics(db, days=days)
        return analytics
    
    except Exception as e:
        logger.error(f"Error fetching usage analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")

@admin_router.get("/analytics/platform")
async def get_platform_analytics(
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get platform-wide trading analytics"""
    try:
        platform_metrics = admin_service.get_platform_metrics(db)
        return platform_metrics
    
    except Exception as e:
        logger.error(f"Error fetching platform analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch platform analytics")

# Configuration Management
@admin_router.get("/config/features")
async def get_feature_flags(
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all feature flags"""
    try:
        flags = admin_service.get_feature_flags(db)
        return {"feature_flags": flags}
    
    except Exception as e:
        logger.error(f"Error fetching feature flags: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch feature flags")

@admin_router.put("/config/features/{flag_id}")
async def update_feature_flag(
    flag_id: int,
    is_enabled: bool = Body(...),
    rollout_percentage: float = Body(0.0),
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a feature flag"""
    try:
        result = admin_service.update_feature_flag(
            db, flag_id, is_enabled, rollout_percentage
        )
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating feature flag: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update feature flag")

@admin_router.get("/config/system")
async def get_system_config(
    category: Optional[str] = Query(None),
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system configuration"""
    try:
        config = admin_service.get_system_config(db, category=category)
        return {"configuration": config}
    
    except Exception as e:
        logger.error(f"Error fetching system config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch configuration")

# Data Management
@admin_router.post("/data/export")
async def create_data_export(
    export_type: str = Body(...),
    filters: Dict[str, Any] = Body({}),
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a data export request"""
    try:
        if export_type not in ["users", "trades", "sentiment", "system_metrics"]:
            raise HTTPException(status_code=400, detail="Invalid export type")
        
        result = admin_service.create_data_export(
            db, export_type, filters, admin_user["email"]
        )
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating data export: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create export")

@admin_router.get("/data/exports")
async def get_data_exports(
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all data export requests"""
    try:
        exports = admin_service.get_data_exports(db)
        return {"exports": exports}
    
    except Exception as e:
        logger.error(f"Error fetching data exports: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch exports")

# Activity Logs
@admin_router.get("/activity")
async def get_all_activity(
    limit: int = Query(100, ge=1, le=500),
    action: Optional[str] = Query(None),
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system-wide activity logs"""
    try:
        activity = admin_service.get_user_activity(db, limit=limit)
        return {"activity": activity}
    
    except Exception as e:
        logger.error(f"Error fetching activity logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch activity logs")