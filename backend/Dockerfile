# Use Python 3.10 slim image
FROM python:3.10-slim

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download Whisper model at build time to avoid cold start delays
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

# Copy application code
COPY . .

# Expose port 7860 (Hugging Face Spaces default port)
EXPOSE 7860

# Run the application
CMD uvicorn app.main:app --host 0.0.0.0 --port 7860
