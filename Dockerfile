# ------------------------------------
# Stage 1: Build Stage (Installs Dependencies)
# ------------------------------------
FROM python:3.13-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (optional, but good practice for drivers like psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt


# ------------------------------------
# Stage 2: Final Runtime Stage
# ------------------------------------
FROM python:3.13-slim

# Set the same working directory
WORKDIR /app

# Copy only the installed packages from the builder stage
# NOTE: Path updated to python3.13
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/

# Copy the application code (assuming the entry point is main.py)
# This includes all your core, models, services, and repositories directories
COPY . /app

# Expose the port Uvicorn will run on
EXPOSE 8000

# Command to run the application using Uvicorn
# We assume your FastAPI app instance is named 'app' and is in the 'main.py' file.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
