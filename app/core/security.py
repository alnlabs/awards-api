from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MAX_BCRYPT_BYTES = 72


# -------------------------
# Password helpers
# -------------------------

def _normalize_password(password: str) -> str:
    """
    bcrypt supports max 72 BYTES.
    Normalize input to avoid runtime crashes.
    """
    return password.encode("utf-8")[:MAX_BCRYPT_BYTES].decode(
        "utf-8", errors="ignore"
    )


def hash_password(password: str) -> str:
    safe_password = _normalize_password(password)
    return pwd_context.hash(safe_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    safe_password = _normalize_password(plain_password)
    return pwd_context.verify(safe_password, hashed_password)


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