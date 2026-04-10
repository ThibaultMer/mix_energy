FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir poetry wheel

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src

COPY *.whl /app/

RUN pip --no-cache-dir install *.whl

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

EXPOSE 8888

CMD ["uvicorn", "mix_energy_api.main:app", "--host", "0.0.0.0", "--port", "8888"]
