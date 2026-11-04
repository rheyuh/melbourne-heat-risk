FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12.13 /uv /uvx /bin/

# Compile .pyc files at build time for faster startup; copy instead of hardlinking
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Mirrors the repo layout so config.py's PROJECT_ROOT resolves to /app
WORKDIR /app/backend

# Dependencies first, so code changes reuse this cached layer
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY . .
RUN uv sync --locked --no-dev

ENV PATH="/app/backend/.venv/bin:$PATH"

EXPOSE 8000

CMD ["fastapi", "run", "api.py", "--port", "8000"]
