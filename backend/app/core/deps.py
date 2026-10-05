from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.core.security import decode_access_token
from backend.app.database import get_db
from backend.app.models.user import User

# HTTPBearer extracts Authorization: Bearer <token>
security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Reusable FastAPI dependency that extracts Bearer JWT token,
    validates the signature and expiration, and retrieves the current User.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_raw = payload.get("sub")
    if user_id_raw is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_raw)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Optional user dependency for routes that work for both anonymous and logged-in users."""
    if credentials is None or not credentials.credentials:
        return None

    payload = decode_access_token(credentials.credentials)
    if payload is None or "sub" not in payload:
        return None

    try:
        user_id = int(payload["sub"])
        return db.query(User).filter(User.id == user_id).first()
    except (ValueError, TypeError):
        return None
