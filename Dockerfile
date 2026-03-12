FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock* ./backend/
RUN cd backend && uv sync --no-dev

COPY backend/ ./backend/
COPY index.html ./index.html

EXPOSE 8000

CMD sh -c "cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
