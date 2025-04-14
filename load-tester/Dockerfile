# load-tester/Dockerfile
FROM python:3.10-slim

# Install ffmpeg and libsndfile1 (needed by soundfile library)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements from context root
COPY load-tester/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy client script and audio from context root
COPY load_test_client.py .
COPY test_audio ./test_audio

# Command will be provided by docker-compose
CMD ["sleep", "infinity"] 