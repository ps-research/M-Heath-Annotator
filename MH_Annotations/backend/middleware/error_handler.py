"""
Global error handling middleware for FastAPI.
"""

import traceback
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError


def handle_exception(exc: Exception) -> JSONResponse:
    """
    Handle exceptions and return standardized error responses.

    Args:
        exc: Exception to handle

    Returns:
        JSONResponse with error details
    """
    from datetime import datetime

    # Validation errors (Pydantic)
    if isinstance(exc, (ValidationError, RequestValidationError)):
        errors = []
        if isinstance(exc, RequestValidationError):
            for error in exc.errors():
                errors.append({
                    "field": " -> ".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                })
        else:
            for error in exc.errors():
                errors.append({
                    "field": " -> ".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                })

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error": "validation_error",
                "message": "Request validation failed",
                "details": {"errors": errors},
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    # File not found
    if isinstance(exc, FileNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "error": "not_found",
                "message": "Resource not found",
                "details": {"path": str(exc)},
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    # Permission errors
    if isinstance(exc, PermissionError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "error": "permission_denied",
                "message": str(exc) or "Permission denied",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    # Value errors
    if isinstance(exc, ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error": "invalid_value",
                "message": str(exc),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    # All other exceptions
    # Log full traceback (in production, use proper logging)
    print(f"ERROR: {exc.__class__.__name__}: {str(exc)}")
    print(traceback.format_exc())

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "internal_error",
            "message": "An internal server error occurred",
            "details": {
                "type": exc.__class__.__name__,
                # Don't expose internal details in production
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors."""
    return handle_exception(exc)


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    return handle_exception(exc)
