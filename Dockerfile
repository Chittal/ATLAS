# Dockerfile for Render deployment
# Optimized for Render's build environment and deployment requirements

# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables for Render
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/render/project/src \
    CONTAINERIZED=true \
    RENDER=true

# Set work directory (Render's standard)
WORKDIR /opt/render/project/src

# Install system dependencies (minimal set for Render)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for databases and ensure proper permissions
RUN mkdir -p /opt/render/project/src/data /opt/render/project/src/static /opt/render/project/src/templates && \
    chmod -R 755 /opt/render/project/src

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /opt/render/project/src
USER app

# Expose the port (Render will set PORT environment variable)
EXPOSE $PORT

# Health check optimized for Render
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Run migrations first, then start the application
CMD ["sh", "-c", "./run_migrations.sh && uvicorn app:app --host 0.0.0.0 --port $PORT"]
