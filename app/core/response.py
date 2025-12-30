from fastapi import HTTPException
from typing import Any, Optional


def success_response(
    message: str,
    data: Optional[Any] = None
) -> dict:
    return {
        "status": "success",
        "message": message,
        "error": None,
        "data": data
    }


def failure_response(
    message: str,
    error: str,
    status_code: int = 400
):
    raise HTTPException(
        status_code=status_code,
        detail={
            "status": "failure",
            "message": message,
            "error": error,
            "data": None
        }
    )