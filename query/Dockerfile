FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

WORKDIR /app/scripts

# Environment variables
ENV HOST=0.0.0.0
ENV PORT=3333

# Expose FastAPI port
EXPOSE 3333

# Start FastAPI server
# Replace main:app with your actual module and FastAPI instance
CMD ["uvicorn", "queryserver:app", "--host", "0.0.0.0", "--port", "3333"]