"""
Advanced logging configuration with S3 integration for Agent 007 Backend
Provides structured logging, automatic log rotation, and cloud storage
"""

import logging
import logging.handlers
import os
import sys
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
import threading
import time

try:
    import structlog
    from pythonjsonlogger import json as jsonlogger
    import boto3
    from botocore.exceptions import NoCredentialsError, PartialCredentialsError
    ADVANCED_LOGGING_AVAILABLE = True
except ImportError:
    ADVANCED_LOGGING_AVAILABLE = False
    print("⚠️  Advanced logging dependencies not available. Install: pip install structlog python-json-logger boto3")


if ADVANCED_LOGGING_AVAILABLE:
    # Configure structlog for structured logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.add_log_level,
            structlog.processors.CallsiteParameterAdder(
                parameters=[structlog.processors.CallsiteParameter.FILENAME,
                           structlog.processors.CallsiteParameter.FUNC_NAME,
                           structlog.processors.CallsiteParameter.LINENO]
            ),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


class S3LogUploader:
    """Handles uploading log files to S3 bucket"""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = None
        self._initialize_s3_client()
        
    def _initialize_s3_client(self):
        """Initialize S3 client with error handling"""
        if not ADVANCED_LOGGING_AVAILABLE:
            return
            
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ S3 logging initialized - Bucket: {self.bucket_name}")
        except (NoCredentialsError, PartialCredentialsError) as e:
            print(f"⚠️  S3 credentials not found: {e}")
            self.s3_client = None
        except Exception as e:
            print(f"⚠️  S3 initialization failed: {e}")
            self.s3_client = None
    
    def upload_log_file(self, local_file_path: str, s3_key_prefix: str = "logs/agent007"):
        """Upload a log file to S3"""
        if not self.s3_client or not os.path.exists(local_file_path):
            return False
            
        try:
            file_name = os.path.basename(local_file_path)
            timestamp = datetime.now(timezone.utc).strftime("%Y/%m/%d")
            s3_key = f"{s3_key_prefix}/{timestamp}/{file_name}"
            
            self.s3_client.upload_file(local_file_path, self.bucket_name, s3_key)
            print(f"📤 Log uploaded to S3: s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            print(f"❌ S3 upload failed: {e}")
            return False


class RotatingS3Handler(logging.handlers.RotatingFileHandler):
    """Custom rotating file handler that uploads rotated logs to S3"""
    
    def __init__(self, filename, maxBytes=10*1024*1024, backupCount=5, s3_uploader=None):
        super().__init__(filename, maxBytes=maxBytes, backupCount=backupCount)
        self.s3_uploader = s3_uploader
        
    def doRollover(self):
        """Override rollover to upload old log to S3"""
        # Get the current log file before rotation
        old_log = self.baseFilename
        
        # Perform the standard rotation
        super().doRollover()
        
        # Upload the rotated log to S3 in a separate thread
        if self.s3_uploader and os.path.exists(old_log + '.1'):
            threading.Thread(
                target=self._upload_to_s3_async,
                args=(old_log + '.1',),
                daemon=True
            ).start()
    
    def _upload_to_s3_async(self, log_file_path: str):
        """Upload log file to S3 in background thread"""
        try:
            time.sleep(1)  # Brief delay to ensure file is fully written
            success = self.s3_uploader.upload_log_file(log_file_path)
            if success and os.getenv('REMOVE_UPLOADED_LOGS', 'false').lower() == 'true':
                os.remove(log_file_path)
        except Exception as e:
            print(f"Background S3 upload error: {e}")


class CustomJSONFormatter(jsonlogger.JsonFormatter if ADVANCED_LOGGING_AVAILABLE else logging.Formatter):
    """Enhanced JSON formatter with additional metadata"""
    
    def add_fields(self, log_record, record, message_dict):
        if ADVANCED_LOGGING_AVAILABLE:
            super().add_fields(log_record, record, message_dict)
        
        # Add custom fields
        log_record['app'] = 'agent007-backend'
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')
        log_record['version'] = os.getenv('APP_VERSION', '1.0.0')
        log_record['hostname'] = os.getenv('HOSTNAME', 'localhost')
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_record['session_id'] = record.session_id
        
        # Add performance metrics if available
        if hasattr(record, 'duration'):
            log_record['duration_ms'] = record.duration
        if hasattr(record, 'memory_usage'):
            log_record['memory_mb'] = record.memory_usage


class LoggingConfig:
    """Main logging configuration class"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.s3_uploader = None
        self._setup_s3_uploader()
        
    def _setup_s3_uploader(self):
        """Setup S3 uploader if credentials are available"""
        bucket_name = os.getenv('LOG_S3_BUCKET')
        if bucket_name and ADVANCED_LOGGING_AVAILABLE:
            self.s3_uploader = S3LogUploader(
                bucket_name=bucket_name,
                region=os.getenv('AWS_REGION', 'us-east-1')
            )
    
    def setup_logging(self, log_level: str = None):
        """Setup comprehensive logging configuration"""
        
        # Determine log level
        if log_level is None:
            log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Create formatters
        if ADVANCED_LOGGING_AVAILABLE:
            json_formatter = CustomJSONFormatter(
                fmt='%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d'
            )
        else:
            json_formatter = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)
        
        # Application log file
        app_log_file = self.log_dir / "agent007_app.log"
        if ADVANCED_LOGGING_AVAILABLE:
            app_handler = RotatingS3Handler(
                filename=str(app_log_file),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                s3_uploader=self.s3_uploader
            )
        else:
            app_handler = logging.handlers.RotatingFileHandler(
                filename=str(app_log_file),
                maxBytes=10*1024*1024,
                backupCount=5
            )
        app_handler.setFormatter(json_formatter)
        app_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(app_handler)
        
        # Error log file
        error_log_file = self.log_dir / "agent007_errors.log"
        if ADVANCED_LOGGING_AVAILABLE:
            error_handler = RotatingS3Handler(
                filename=str(error_log_file),
                maxBytes=5*1024*1024,
                backupCount=10,
                s3_uploader=self.s3_uploader
            )
        else:
            error_handler = logging.handlers.RotatingFileHandler(
                filename=str(error_log_file),
                maxBytes=5*1024*1024,
                backupCount=10
            )
        error_handler.setFormatter(json_formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        
        # Configure third-party loggers
        logging.getLogger("uvicorn").setLevel(logging.INFO)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("chromadb").setLevel(logging.WARNING)
        logging.getLogger("langchain").setLevel(logging.INFO)
        
        print(f"🔧 Logging configured - Level: {log_level}")
        print(f"📁 Log directory: {self.log_dir.absolute()}")
        if self.s3_uploader and self.s3_uploader.s3_client:
            print(f"☁️  S3 logging enabled - Bucket: {self.s3_uploader.bucket_name}")
        else:
            print("💾 Local logging only - S3 not configured")


# Legacy function for backward compatibility
def configure_logging():
    """Legacy configure_logging function - now uses advanced logging"""
    config = LoggingConfig()
    config.setup_logging()
    return logging.getLogger("app")


# Global logging setup function
def setup_application_logging(log_level: str = None):
    """Setup application-wide logging"""
    config = LoggingConfig()
    config.setup_logging(log_level)
    return config


# Utility functions for structured logging
def get_logger(name: str):
    """Get a structured logger instance"""
    if ADVANCED_LOGGING_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


def log_request(logger, request_data: Dict[str, Any], request_id: str = None):
    """Log HTTP request with structured data"""
    if hasattr(logger, 'info'):
        logger.info(
            "HTTP Request",
            extra={
                'request_id': request_id,
                'method': request_data.get('method'),
                'path': request_data.get('path'),
                'user_agent': request_data.get('user_agent'),
                'ip_address': request_data.get('ip_address')
            }
        )


def log_response(logger, response_data: Dict[str, Any], request_id: str = None, duration_ms: float = None):
    """Log HTTP response with structured data"""
    if hasattr(logger, 'info'):
        logger.info(
            "HTTP Response",
            extra={
                'request_id': request_id,
                'status_code': response_data.get('status_code'),
                'duration_ms': duration_ms,
                'response_size': response_data.get('size')
            }
        )


def log_error(logger, error: Exception, context: Dict[str, Any] = None):
    """Log errors with full context and stack trace"""
    if hasattr(logger, 'error'):
        logger.error(
            f"Application Error: {type(error).__name__}: {str(error)}",
            extra={
                'error_type': type(error).__name__,
                'error_message': str(error),
                'stack_trace': traceback.format_exc(),
                'context': context or {}
            }
        )


def log_performance(operation: str, duration_ms: float, metadata: Dict[str, Any] = None):
    """Log performance metrics"""
    perf_logger = logging.getLogger("performance")
    perf_logger.info(
        f"Performance: {operation}",
        extra={
            'operation': operation,
            'duration_ms': duration_ms,
            'metadata': metadata or {}
        }
    )


# Context managers for request tracking
class RequestContext:
    """Context manager for request-scoped logging"""
    
    def __init__(self, request_id: str, logger):
        self.request_id = request_id
        self.logger = logger
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.time() - self.start_time) * 1000
        if exc_type:
            self.logger.error(
                "Request completed with error",
                extra={
                    'request_id': self.request_id,
                    'duration_ms': duration,
                    'error_type': exc_type.__name__,
                    'error_message': str(exc_val)
                }
            )
        else:
            self.logger.info(
                "Request completed successfully",
                extra={
                    'request_id': self.request_id,
                    'duration_ms': duration
                }
            )
