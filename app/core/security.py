from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pre-initialize bcrypt to avoid initialization errors
# This is a workaround for bcrypt library compatibility issues with passlib
try:
    # Initialize by hashing a simple password
    pwd_context.hash("init")
except (ValueError, AttributeError):
    # Ignore initialization errors - they're library compatibility issues
    pass


# -------------------------
# Password helpers
# -------------------------

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# -------------------------
# JWT helpers
# -------------------------

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        return None