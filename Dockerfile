# Use a slim Python image to keep size down (adjust version 3.10/3.11 as needed)
FROM python:3.11

# Set working directory
WORKDIR /app


# Install system dependencies (ffmpeg)
# We use a single RUN command to keep the image size small by cleaning up afterwards
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
# We copy the 'src' folder into '/app/src' to maintain import structure
COPY src/ ./src/

# Assuming your entry point is inside src/main.py
# We create a user to avoid running as root (optional but security best practice)
RUN useradd -m appuser

RUN mkdir -p /app/src/data/final_states/short_reddit_post && \
    chown -R appuser:appuser /app

USER appuser

# Run the application
CMD ["python", "src/main.py"]