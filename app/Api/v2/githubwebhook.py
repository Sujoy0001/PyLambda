from typing import Annotated
from fastapi import APIRouter, Form, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
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

