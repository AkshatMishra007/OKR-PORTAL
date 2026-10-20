from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.leaderboard.schemas import LeaderboardResponse
from app.leaderboard.service import get_leaderboard_service
from app.users.models import User


router = APIRouter(
    prefix="/leaderboard",
    tags=["Leaderboard"],
)


@router.get(
    "/",
    response_model=LeaderboardResponse,
)
def get_leaderboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the leaderboard for the current user's organization.
    """

    return get_leaderboard_service(
        db=db,
        current_user_id=current_user.id,
    )