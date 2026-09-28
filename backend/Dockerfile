# syntax=docker/dockerfile:1

# Build context: ./backend
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_CACHE_DIR=/tmp/uv-cache

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential libpq-dev gettext fontconfig \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project && rm -rf /tmp/uv-cache

COPY . .

# Register bundled project fonts (Noto Sans Arabic / Inter) with fontconfig so
# WeasyPrint/Pango resolves 'Noto Sans Arabic' deterministically inside the
# container — never depend on developer-host fonts.
RUN mkdir -p /usr/local/share/fonts/sotooh \
    && cp /app/assets/fonts/*.ttf /usr/local/share/fonts/sotooh/

RUN addgroup --system django && adduser --system --ingroup django django \
    && mkdir -p /app/staticfiles /var/cache/fontconfig /home/django/.cache/fontconfig \
    && chown -R django:django /app/staticfiles /app /var/cache/fontconfig /home/django/.cache/fontconfig

USER django

# Warm the fontconfig cache as the runtime user (writable cache dir)
RUN fc-cache -f >/dev/null 2>&1 || true

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
