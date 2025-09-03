# Use a slim, secure base image
FROM python:3.11-slim-bookworm

# Set the working directory
WORKDIR /app

# Install system dependencies
# This is done as the default root user
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd --create-home --uid 1000 appuser

# Copy requirements first for better caching
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch to the non-root user for security
USER appuser

# Copy the rest of the application code as the non-root user
COPY --chown=appuser:appuser . .

# Add a HEALTHCHECK instruction to ensure the application is truly running.
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8000/api/v1/health/ || exit 1

EXPOSE 8000

# The CMD command to run the Uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]