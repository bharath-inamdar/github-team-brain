from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.services.dashboard_service import get_dashboard_overview

router = APIRouter(prefix="/dashboard")


@router.get("/overview")
def dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_dashboard_overview(
        db,
        user_id=current_user.id,
    )
