# ========= Build/runtime image =========
FROM python:3.11-slim AS base

# System deps (build tools, DB drivers, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \   
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Application Code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8002 \
    SERVICE_NAME=task

# Create a non-root user
RUN useradd -m appuser
USER appuser

# Expose port (for Uvicorn)
EXPOSE 8002

# Use Uvicorn to serve the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002", "--access-log", "--log-level", "info"]
