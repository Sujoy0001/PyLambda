import json
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Form, Depends, Header, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.webhook import RepoStar

router = APIRouter(prefix="/v2", tags=["post request when someone star the repo"])


@router.post("/github-webhook")
async def repo_star_webhook(
    payload: Annotated[str, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    x_github_event: Annotated[str | None, Header()] = None,
    x_github_delivery: Annotated[str | None, Header()] = None,
):
    # 1. Only process 'star' events (ignores GitHub's initial 'ping' test)
    if x_github_event != "star":
        return {"status": "ignored", "event": x_github_event}

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 2. Only save when someone stars ('created'), ignore unstars ('deleted')
    if data.get("action") != "created":
        return {"status": "ignored", "action": data.get("action")}

    # 3. Parse timestamp and save the star record
    starred_at_raw = data.get("starred_at")
    starred_at_dt = (
        datetime.fromisoformat(starred_at_raw.replace("Z", "+00:00"))
        if starred_at_raw
        else None
    )

    new_star = RepoStar(
        delivery_id=x_github_delivery or "unknown",
        sender_id=data["sender"]["id"],
        sender_username=data["sender"]["login"],
        sender_avatar=data["sender"].get("avatar_url"),
        stargazers_count=data["repository"]["stargazers_count"],
        starred_at=starred_at_dt,
    )

    try:
        db.add(new_star)
        db.commit()
        db.refresh(new_star)
    except IntegrityError:
        db.rollback()
        return {"status": "duplicate"}

    return {
        "status": "saved",
        "starred_by": new_star.sender_username,
        "total_stars": new_star.stargazers_count,
    }
