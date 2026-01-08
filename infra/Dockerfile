# STAGE 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install compilation tools (gcc)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements FIRST (Docker caching optimization)
COPY requirements.txt .

# Install dependencies to /install folder
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# STAGE 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# [CRITICAL FIX] Install curl for Healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system appgroup && adduser --system --group appuser

# Copy installed libraries from Stage 1
COPY --from=builder /install /usr/local

# Copy your code
COPY . .

# Switch user
USER appuser

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]