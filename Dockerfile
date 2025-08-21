# LinkedIn Post Generator Discord Bot
# Multi-stage build for optimal image size

FROM python:3.11-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set the working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash --user-group linkedin

# Set the working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /home/linkedin/.local

# Copy application code
COPY --chown=linkedin:linkedin . .

# Ensure the user can access their local packages
ENV PATH="/home/linkedin/.local/bin:$PATH"

# Switch to non-root user
USER linkedin

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Expose port (if running web server in future)
EXPOSE 8000

# Default command
CMD ["python", "discord_linkedin_bot.py"]

# Metadata
LABEL maintainer="LinkedIn Post Generator Team"
LABEL version="1.0"
LABEL description="Discord bot for LinkedIn post approval workflow"