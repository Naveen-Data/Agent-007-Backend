"""
Middleware package for Agent 007 Backend
"""

from .logging import setup_logging_middleware

__all__ = ["setup_logging_middleware"]