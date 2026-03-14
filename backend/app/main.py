from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.routes import contact, health

app = FastAPI(title="Consulting")

app.include_router(health.router)
app.include_router(contact.router)

root_dir = Path(__file__).resolve().parent.parent.parent
index_html = root_dir / "index.html"

STATIC_FILES = {
    "privacy-policy.pdf": "application/pdf",
    "terms-and-conditions.pdf": "application/pdf",
}


@app.get("/{path:path}")
async def serve_page(path: str) -> FileResponse:  # pragma: no cover
    if path in STATIC_FILES:
        return FileResponse(root_dir / path, media_type=STATIC_FILES[path])
    return FileResponse(index_html)
