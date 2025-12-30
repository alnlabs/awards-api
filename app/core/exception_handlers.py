from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "failure",
            "message": "Request failed",
            "error": exc.detail,
            "data": None
        }
    )


def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "status": "failure",
            "message": "Validation error",
            "error": exc.errors(),
            "data": None
        }
    )