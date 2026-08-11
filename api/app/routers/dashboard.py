from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.dashboard_service import get_dashboard_overview

router = APIRouter(prefix="/dashboard")


@router.get("/overview")
def dashboard_overview(db: Session = Depends(get_db)):
    return get_dashboard_overview(db)