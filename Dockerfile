FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY README.md alembic.ini ./
COPY src ./src
COPY bin ./bin
COPY frontend ./frontend
RUN uv sync --frozen --no-dev

RUN chmod +x bin/run_api \
    && (test -f bin/load_fixtures && chmod +x bin/load_fixtures || true) \
    && useradd -m appuser \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

ENTRYPOINT ["/app/bin/run_api"]