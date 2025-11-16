"""
Router for handling frontend logs and metrics
Receives logs from frontend and stores them with backend logs
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.logging_config import get_logger

router = APIRouter()

logger = get_logger("frontend_logs")


class FrontendLogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    category: str
    context: Optional[Dict[str, Any]] = None
    sessionId: Optional[str] = None
    userId: Optional[str] = None
    url: Optional[str] = None
    userAgent: Optional[str] = None
    stackTrace: Optional[str] = None


class FrontendLogsRequest(BaseModel):
    logs: List[FrontendLogEntry]
    sessionId: str


class PerformanceMetric(BaseModel):
    name: str
    value: float
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class PerformanceMetricsRequest(BaseModel):
    metrics: List[PerformanceMetric]
    sessionId: str


@router.post("/frontend")
async def receive_frontend_logs(
    request: Request,
    log_request: FrontendLogsRequest
):
    """Receive and process frontend logs"""
    
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.info(
        "Received frontend logs",
        extra={
            'request_id': request_id,
            'session_id': log_request.sessionId,
            'log_count': len(log_request.logs)
        }
    )
    
    # Process each log entry
    for log_entry in log_request.logs:
        # Map frontend log levels to Python logging levels
        level_mapping = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warn': logging.WARNING,
            'error': logging.ERROR
        }
        
        log_level = level_mapping.get(log_entry.level, logging.INFO)
        
        # Create structured log entry
        extra_data = {
            'frontend_session_id': log_entry.sessionId,
            'frontend_user_id': log_entry.userId,
            'category': log_entry.category,
            'url': log_entry.url,
            'user_agent': log_entry.userAgent,
            'frontend_timestamp': log_entry.timestamp,
            'context': log_entry.context,
            'source': 'frontend'
        }
        
        # Add stack trace for errors
        if log_entry.stackTrace:
            extra_data['frontend_stack_trace'] = log_entry.stackTrace
        
        # Log the frontend entry
        logger.log(
            log_level,
            f"[Frontend] {log_entry.message}",
            extra=extra_data
        )
        
        # Also log to console for development
        if log_entry.level == 'error':
            print(f"🔴 Frontend Error: {log_entry.message}")
            if log_entry.context:
                print(f"   Context: {log_entry.context}")
    
    return {"status": "success", "processed": len(log_request.logs)}


@router.post("/performance")
async def receive_performance_metrics(
    request: Request,
    metrics_request: PerformanceMetricsRequest
):
    """Receive and process frontend performance metrics"""
    
    request_id = getattr(request.state, 'request_id', 'unknown')
    perf_logger = logging.getLogger("performance")
    
    logger.info(
        "Received frontend performance metrics",
        extra={
            'request_id': request_id,
            'session_id': metrics_request.sessionId,
            'metric_count': len(metrics_request.metrics)
        }
    )
    
    # Process each metric
    for metric in metrics_request.metrics:
        perf_logger.info(
            f"Frontend Performance: {metric.name}",
            extra={
                'metric_name': metric.name,
                'metric_value': metric.value,
                'frontend_session_id': metrics_request.sessionId,
                'frontend_timestamp': metric.timestamp,
                'metadata': metric.metadata,
                'source': 'frontend'
            }
        )
        
        # Log slow operations
        if metric.name in ['page_load', 'api_call'] and metric.value > 3000:  # 3 seconds
            logger.warning(
                f"Slow frontend operation detected: {metric.name}",
                extra={
                    'metric_name': metric.name,
                    'metric_value': metric.value,
                    'session_id': metrics_request.sessionId,
                    'metadata': metric.metadata
                }
            )
    
    return {"status": "success", "processed": len(metrics_request.metrics)}


@router.get("/status")
async def logging_status():
    """Get logging system status"""
    return {
        "status": "active",
        "frontend_logs": "enabled",
        "s3_upload": "configured" if logging.getLogger().handlers else "disabled",
        "timestamp": datetime.utcnow().isoformat()
    }