from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.deps import get_current_user
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Creates a new user account with hashed password and returns an access token."""
    normalized_email = request.email.strip().lower()

    # Check for duplicate email registration
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    # Hash password securely
    hashed_pwd = hash_password(request.password)

    new_user = User(
        name=request.name.strip(),
        email=normalized_email,
        password_hash=hashed_pwd,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create JWT access token
    access_token = create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and obtain JWT token",
)
def login(request: UserLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticates credentials and returns a signed JWT access token."""
    normalized_email = request.email.strip().lower()

    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get authenticated user profile",
)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Protected endpoint returning the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)
