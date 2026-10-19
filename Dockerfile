# syntax=docker/dockerfile:1

# ---------- Stage 1: builder ----------
# Installs Python dependencies into an isolated virtualenv.
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Copy only the dependency manifest first, so this layer stays cached
# until requirements.txt changes (editing app.py does not reinstall deps).
COPY requirements.txt .
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install -r requirements.txt

# ---------- Stage 2: runtime ----------
# Slim image with only the virtualenv and the app code.
FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Unprivileged user with no login shell and no home directory.
RUN groupadd --system app \
 && useradd --system --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app app.py .

USER app

EXPOSE 8000

# python:slim has no curl, so the check uses Python's standard library.
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"]

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app:app"]
