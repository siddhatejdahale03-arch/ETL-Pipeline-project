FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first (cached if requirements.txt doesn't change)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy only the source folders the pipeline needs (not tests, docs, etc.)
COPY config ./config
COPY src ./src
COPY sql ./sql
COPY data/sample ./data/sample

# Run as a non-root user for security (Docker best practice)
RUN useradd -m etluser && chown -R etluser /app
USER etluser

# Default command: run one full pipeline pass then exit
CMD ["python", "-m", "src.pipeline"]
