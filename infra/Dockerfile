# STAGE 1: Builder (Install dependencies)
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies (gcc required for some python packages)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies to a virtual env (keeps image clean)
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# STAGE 2: Runtime (Final Image)
FROM python:3.11-slim

WORKDIR /app

# Create a non-root user (Security Best Practice)
RUN addgroup --system appgroup && adduser --system --group appuser

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Switch to non-root user
USER appuser

# Expose port (Documentation only)
EXPOSE 8000

# Healthcheck (Checks if API is responding)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]