# Use a slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (ffmpeg + rubberband)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    rubberband-cli \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ ./src/

# Create necessary directories with proper permissions
RUN useradd -m appuser && \
    mkdir -p /app/src/data/final_states \
             /app/src/data/output \
             /app/src/data/cache && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set Python to run in unbuffered mode for better logging
ENV PYTHONUNBUFFERED=1

# Default environment variables (can be overridden)
ENV TOPIC="Beautiful friendship story" \
    PLAYBACK_SPEED=1.5 \
    TEST_MODE=false

# Run the application
CMD ["python", "src/main.py"]