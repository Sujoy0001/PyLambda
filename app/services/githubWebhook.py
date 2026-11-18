import json
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.githubwebhook import RepoStar


def process_webhook_event(
    db: Session,
    event: str | None,
    delivery_id: str | None,
    raw_payload: str,
) -> dict:
    # 1. Ignore non-star events (like GitHub's 'ping')
    if event != "star":
        return {"status": "ignored", "event": event}

    try:
        data = json.loads(raw_payload)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON payload")

    action = data.get("action")
    sender_id = data["sender"]["id"]

    # 2. Handle "+" (Add record when action is 'created')
    if action == "created":
        starred_at_raw = data.get("starred_at")
        starred_at_dt = (
            datetime.fromisoformat(starred_at_raw.replace("Z", "+00:00"))
            if starred_at_raw
            else None
        )
        
        uid = uuid.uuid4()

        new_star = RepoStar(
            id=uid,
            stargazers_count=data["repository"]["stargazers_count"],
            delivery_id=delivery_id or "unknown",
            sender_id=sender_id,
            sender_username=data["sender"]["login"],
            starred_at=starred_at_dt,
        )

        try:
            db.add(new_star)
            db.commit()
            db.refresh(new_star)
            return {
                "status": "added",
                "user": new_star.sender_username,
            }
        except IntegrityError:
            db.rollback()
            return {"status": "duplicate"}

    # 3. Handle "-" (Remove record when action is 'deleted')
    elif action == "deleted":
        existing_record = (
            db.query(RepoStar).filter(RepoStar.sender_id == sender_id).first()
        )
        if existing_record:
            db.delete(existing_record)
            db.commit()
            return {
                "status": "removed",
                "user": data["sender"]["login"],
            }
        return {"status": "not_found"}

    return {"status": "ignored", "action": action}

def get_latest_repo_star(db: Session):
    return (
        db.query(RepoStar.sender_username, RepoStar.stargazers_count)
        .order_by(RepoStar.starred_at.desc())
        .first()
    )