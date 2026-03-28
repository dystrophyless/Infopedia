FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# ---------- builder ----------
FROM base AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.2 /uv /uvx /bin/

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=/app/pyproject.toml,readonly \
    --mount=type=bind,source=uv.lock,target=/app/uv.lock,readonly \
    uv sync --locked --no-install-project --no-editable

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# ---------- runtime ----------
FROM base AS runtime

RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --create-home app \
    && install -d -o app -g app /home/app/.cache/huggingface \
    && install -d -o app -g app /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv

COPY --chown=app:app . /app

USER app