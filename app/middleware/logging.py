"""
FastAPI middleware for comprehensive request/response logging
Tracks all HTTP requests with timing, errors, and context
"""

import time
import uuid
import json
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.logging_config import (
    log_request,
    log_response,
    log_error,
    RequestContext,
    get_logger,
)
from app.constants import LoggingConstants


class LoggingMiddleware(BaseHTTPMiddleware):
    """Comprehensive logging middleware for FastAPI"""

    def __init__(self, app, logger_name: str = "access"):
        super().__init__(app)
        self.logger = get_logger(logger_name)
        self.access_logger = logging.getLogger("access")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with comprehensive logging"""

        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Extract request information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        request_data = {
            'method': request.method,
            'path': str(request.url.path),
            'query_params': str(request.url.query) if request.url.query else None,
            'user_agent': user_agent,
            'ip_address': client_ip,
            'content_type': request.headers.get("content-type"),
            'content_length': request.headers.get("content-length"),
        }

        # Add request ID to state for use in route handlers
        request.state.request_id = request_id

        # Log incoming request
        log_request(self.logger, request_data, request_id)

        start_time = time.time()
        response = None

        try:
            # Process request within context
            with RequestContext(request_id, self.logger):
                response = await call_next(request)

            # Calculate response time
            process_time = (time.time() - start_time) * 1000

            # Get response size if possible
            response_size = None
            if hasattr(response, 'headers') and 'content-length' in response.headers:
                response_size = int(response.headers['content-length'])

            response_data = {
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type'),
                'size': response_size,
            }

            # Log successful response
            log_response(self.logger, response_data, request_id, process_time)

            # Add performance logging for slow requests
            if process_time > 1000:  # Log requests taking more than 1 second
                self.logger.warning(
                    "Slow request detected",
                    extra={
                        'request_id': request_id,
                        'duration_ms': process_time,
                        'path': request_data['path'],
                        'method': request_data['method'],
                    },
                )

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

            return response

        except Exception as e:
            # Calculate error response time
            process_time = (time.time() - start_time) * 1000

            # Log error with context
            error_context = {
                'request_id': request_id,
                'method': request_data['method'],
                'path': request_data['path'],
                'ip_address': client_ip,
                'duration_ms': process_time,
            }

            log_error(self.logger, e, error_context)

            # Re-raise the exception
            raise e

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address considering proxies"""
        # Check for forwarded IP headers (common in production)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Specialized middleware for error tracking and alerting"""

    def __init__(self, app):
        super().__init__(app)
        self.error_logger = get_logger("errors")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track and log application errors"""

        try:
            response = await call_next(request)

            # Log 4xx and 5xx responses as warnings/errors
            if response.status_code >= 400:
                severity = "error" if response.status_code >= 500 else "warning"

                if hasattr(self.error_logger, severity):
                    getattr(self.error_logger, severity)(
                        f"HTTP {response.status_code} Response",
                        extra={
                            'status_code': response.status_code,
                            'path': str(request.url.path),
                            'method': request.method,
                            'client_ip': (
                                request.client.host if request.client else "unknown"
                            ),
                        },
                    )

            return response

        except Exception as e:
            # Log unhandled exceptions
            log_error(
                self.error_logger,
                e,
                {
                    'path': str(request.url.path),
                    'method': request.method,
                    'client_ip': request.client.host if request.client else "unknown",
                },
            )
            raise


def setup_logging_middleware(app):
    """Setup all logging middleware for the FastAPI app"""

    # Add error logging middleware first (outer layer)
    app.add_middleware(ErrorLoggingMiddleware)

    # Add request/response logging middleware
    app.add_middleware(LoggingMiddleware)

    print("🔍 Logging middleware configured")
