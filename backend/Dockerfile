# Use a slim, secure base image
# Alpine is a good choice for its small size, but the apt package manager is not available.
# We'll use a Python slim image based on Debian instead, which is still very small
# but uses the more common apt.
FROM python:3.11-slim-bookworm

# Set the working directory
WORKDIR /app

# Create a non-root user first for better security
RUN useradd --create-home --uid 1000 appuser
USER appuser

# Install system dependencies
# We use apt-get here, as this image is Debian-based.
# We also install curl for the healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker's build cache.
# This step will only rerun if requirements.txt changes.
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY --chown=appuser:appuser . .

# Add a HEALTHCHECK instruction to ensure the application is truly running.
# It uses a dedicated HTTP endpoint to verify the service is responsive.
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

EXPOSE 8000

# The CMD command to run the Uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]