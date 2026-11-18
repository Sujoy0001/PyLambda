from typing import Annotated

from fastapi import APIRouter, Depends, Form, Header, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.githubwebhook import RepoStar
from app.services.githubWebhook import process_webhook_event

router = APIRouter()

@router.post("/github-webhook")
async def repo_star_webhook(
    payload: Annotated[str, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    x_github_event: Annotated[str | None, Header()] = None,
    x_github_delivery: Annotated[str | None, Header()] = None,
):
    try:
        return process_webhook_event(
            db=db,
            event=x_github_event,
            delivery_id=x_github_delivery,
            raw_payload=payload,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/github-star-count")
async def count_star(db: Annotated[Session, Depends(get_db)]) -> dict[str, int]:
    count = db.query(func.count(RepoStar.id)).scalar() or 0
    return {"count": count}
