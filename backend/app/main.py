from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.routes import contact, health

app = FastAPI(title="Consulting")

app.include_router(health.router)
app.include_router(contact.router)

index_html = Path(__file__).resolve().parent.parent.parent / "index.html"


@app.get("/{path:path}")
async def serve_page(path: str) -> FileResponse:  # pragma: no cover
    return FileResponse(index_html)
