import re
import time

import resend
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.config import settings

router = APIRouter(prefix="/api")

# In-memory rate limiter: IP -> (count, reset_time)
_rate_limits: dict[str, dict] = {}
_WINDOW = 3600  # 1 hour
_MAX_REQUESTS = 2

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class ContactRequest(BaseModel):
    name: str = Field(max_length=100)
    email: str = Field(max_length=100)
    message: str = Field(max_length=2000)
    company: str = Field(default="", max_length=100)


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    entry = _rate_limits.get(ip)
    if entry is None:
        _rate_limits[ip] = {"count": 1, "reset": now + _WINDOW}
        return True
    if now > entry["reset"]:
        entry["count"] = 1
        entry["reset"] = now + _WINDOW
        return True
    if entry["count"] >= _MAX_REQUESTS:
        return False
    entry["count"] += 1
    return True


@router.post("/contact")
def contact(body: ContactRequest, request: Request):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    if not EMAIL_RE.match(body.email):
        raise HTTPException(status_code=400, detail="Invalid email address")
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    ip = _get_client_ip(request)
    if not _check_rate_limit(ip):
        raise HTTPException(
            status_code=429, detail="Too many requests. Try again later."
        )

    company = body.company.strip()
    company_line = f"<p><strong>Company:</strong> {company}</p>" if company else ""

    name = body.name.strip()
    message = body.message.strip()

    resend.api_key = settings.resend_api_key
    resend.Emails.send(
        {
            "from": settings.from_email,
            "to": settings.contact_email_to,
            "reply_to": body.email,
            "subject": f"Consulting inquiry from {name}",
            "html": (
                '<div style="font-family: sans-serif;'
                " max-width: 560px; margin: 0 auto;"
                ' padding: 20px;">'
                "<h2>New consulting inquiry</h2>"
                f"<p><strong>Name:</strong> {name}</p>"
                f"<p><strong>Email:</strong> {body.email}</p>"
                f"{company_line}"
                '<hr style="border: none;'
                " border-top: 1px solid #eee;"
                ' margin: 16px 0;" />'
                f'<p style="white-space: pre-wrap;">'
                f"{message}</p>"
                "</div>"
            ),
        }
    )

    return {"message": "Message sent. I'll be in touch."}
