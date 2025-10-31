# ========= Build/runtime image =========
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8001

# Non-root user
RUN useradd -m appuser
USER appuser

EXPOSE 8001

# Uvicorn + access log opened
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001", "--access-log", "--log-level", "info"]
