import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.database import SessionLocal
from app.models import User
from app.schemas import AuthResponse, UserCreate, UserResponse

logger = logging.getLogger(__name__)

# Placeholder used for the bootstrap admin account until a real password is
# provided via the BOOTSTRAP_ADMIN_PASSWORD environment variable. It is not a
# valid bcrypt hash, so it can never authenticate a login.
BOOTSTRAP_UNSET_PASSWORD = "bootstrap-unset"


def build_auth_response(
    user: User,
) -> AuthResponse:
    """
    Create a signed access token and user payload for a user.
    """
    access_token = create_access_token(user.id)

    return AuthResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


def register_user(
    user_in: UserCreate,
    db: Session,
) -> AuthResponse:
    """
    Register a new user and return an access token.
    """
    existing = (
        db.query(User)
        .filter(User.email == user_in.email)
        .first()
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="A user with this email already exists.",
        )

    user = User(
        email=user_in.email,
        username=(
            user_in.username
            or user_in.email.split("@")[0]
        ),
        hashed_password=hash_password(
            user_in.password
        ),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(
        "Registered new user",
        extra={"user_id": user.id},
    )

    return build_auth_response(user)


def login_user(
    email: str,
    password: str,
    db: Session,
) -> AuthResponse:
    """
    Authenticate a user by email and password.
    """
    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is None or not verify_password(
        password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Inactive user",
        )

    logger.info(
        "User logged in",
        extra={"user_id": user.id},
    )

    return build_auth_response(user)


def ensure_bootstrap_admin() -> None:
    """
    Ensure the bootstrap admin account exists.

    The account is created by the repository backfill migration with an
    unusable placeholder password. If BOOTSTRAP_ADMIN_PASSWORD is set in the
    environment, the placeholder is replaced with a real bcrypt hash on the
    first application startup. The password is never stored in source code or
    migrations, and an already-set password is never overwritten.
    """
    if not settings.bootstrap_admin_password:
        return

    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.email == settings.bootstrap_admin_email)
            .first()
        )

        if user is None:
            user = User(
                email=settings.bootstrap_admin_email,
                username=settings.bootstrap_admin_username,
                hashed_password=BOOTSTRAP_UNSET_PASSWORD,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        if user.hashed_password == BOOTSTRAP_UNSET_PASSWORD:
            user.hashed_password = hash_password(
                settings.bootstrap_admin_password
            )
            db.commit()

            logger.info(
                "Set bootstrap admin password",
                extra={"email": settings.bootstrap_admin_email},
            )
    finally:
        db.close()
