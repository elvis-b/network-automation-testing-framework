"""
Health Check Routes

Application health and monitoring endpoints.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from app.config import settings
from app.database.mongodb import get_database

logger = logging.getLogger(__name__)
router = APIRouter()

# Track startup time
startup_time = datetime.utcnow()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Application health status including:
        - Overall status
        - Database connectivity
        - Uptime
        - Version
    """
    health_status = {
        "status": "healthy",
        "version": settings.app_version,
        "uptime_seconds": int((datetime.utcnow() - startup_time).total_seconds()),
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check MongoDB connection
    try:
        db = get_database()
        await db.command("ping")
        health_status["checks"]["database"] = {
            "status": "healthy",
            "type": "mongodb"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "type": "mongodb",
            "error": str(e)
        }
    
    return health_status


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness probe endpoint.
    
    Used by orchestrators (Kubernetes, Docker) to check
    if the application is ready to receive traffic.
    
    Returns:
        Readiness status
        
    Raises:
        HTTPException: If application is not ready
    """
    try:
        # Check database connectivity
        db = get_database()
        await db.command("ping")
        
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={"status": "not ready", "error": str(e)}
        )


@router.get("/health/live")
async def liveness_check():
    """
    Liveness probe endpoint.
    
    Used by orchestrators to check if the application
    is alive and should not be restarted.
    
    Returns:
        Liveness status
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/metrics")
async def get_metrics():
    """
    Basic metrics endpoint.
    
    Returns application metrics for monitoring.
    In production, consider using prometheus_client.
    
    Returns:
        Application metrics
    """
    try:
        db = get_database()
        
        # Get collection counts
        devices_count = await db["devices"].count_documents({})
        alerts_count = await db["alerts"].count_documents({})
        active_alerts = await db["alerts"].count_documents({"acknowledged": False})
        users_count = await db["users"].count_documents({})
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": int((datetime.utcnow() - startup_time).total_seconds()),
            "counters": {
                "devices_total": devices_count,
                "alerts_total": alerts_count,
                "alerts_active": active_alerts,
                "users_total": users_count
            }
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

