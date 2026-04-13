FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir poetry wheel

COPY pyproject.toml /app/pyproject.toml
COPY  dashboard /app/dashboard
COPY streamlit  /app/streamlit
COPY .env /app/.env

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

CMD ["poetry", "run", "streamlit", "run", "dashboard/dashboard_app.py"]
