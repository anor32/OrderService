FROM python:3.11-slim

RUN addgroup --system --gid 1000 appuser && \
    adduser --system --uid 1000 --ingroup appuser appuser

WORKDIR /app
COPY --chown=appuser:appuser . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

USER appuser




CMD bash -c "python -m app.commands.manage_db -op create && \
alembic upgrade head && \
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
