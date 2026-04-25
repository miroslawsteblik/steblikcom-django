FROM python:3.12-slim AS builder
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project

FROM python:3.12-slim
WORKDIR /app
RUN useradd --system --no-create-home --shell /usr/sbin/nologin appuser
COPY --from=builder /app/.venv /app/.venv
COPY . .
RUN mkdir -p data \
    && chmod +x entrypoint.sh \
    && chown -R appuser:appuser /app
USER appuser
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
