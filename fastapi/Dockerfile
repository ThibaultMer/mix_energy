FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src

COPY ../predict/pyproject.toml /app/predict/pyproject.toml
COPY ../predict/src /app/predict/src

RUN cd predict \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi\
    && cd ..


RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

EXPOSE 8888

CMD ["uvicorn", "mix_energy_api.main:app", "--host", "0.0.0.0", "--port", "8888"]
