FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.1.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_NO_ANSI=1

WORKDIR /app
RUN pip install --no-cache-dir "poetry>=2.0.0,<3.0.0"
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root
COPY src ./src

EXPOSE 8000

CMD ["uvicorn", "src.adguard_auditor.main:app", "--host", "0.0.0.0", "--port", "8000"]
