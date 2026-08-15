from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import AuthResponse, UserCreate, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=201,
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user and return an access token.
    """
    return auth_service.register_user(
        user_in,
        db,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Log in with an email and password to receive an access token.

    Uses OAuth2 password form fields so the OpenAPI docs expose a
    native authorize flow.
    """
    return auth_service.login_user(
        form_data.username,
        form_data.password,
        db,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user: User = Depends(get_current_user),
):
    """
    Return the profile of the authenticated user.
    """
    return current_user
