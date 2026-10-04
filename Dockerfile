FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY config ./config
COPY src ./src
COPY sql ./sql
COPY data/sample ./data/sample

RUN useradd -m etluser && chown -R etluser /app
USER etluser

CMD ["python", "-m", "src.pipeline"]
