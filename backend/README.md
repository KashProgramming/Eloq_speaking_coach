# Eloq Backend - Hugging Face Spaces Deployment

This is the backend API for Eloq, an AI-powered public speaking and English fluency coach.

## Deployment on Hugging Face Spaces

This backend is designed to be deployed on Hugging Face Spaces using Docker.

### Prerequisites

1. A Hugging Face account
2. PostgreSQL database (Supabase recommended)
3. Cloudinary account for audio storage
4. Groq API keys for LLM and TTS

### Deployment Steps

1. **Create a new Space:**
   - Go to https://huggingface.co/new-space
   - Choose "Docker" as the SDK
   - Select "CPU basic" or higher (CPU is sufficient for Whisper base model)

2. **Clone and push this repository:**
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   cd YOUR_SPACE_NAME
   # Copy all files from eloq/backend to this directory
   git add .
   git commit -m "Initial commit"
   git push
   ```

3. **Configure Environment Variables:**
   In your Space settings, add the following secrets:

   **Required:**
   - `DATABASE_URL`: PostgreSQL connection string (e.g., from Supabase)
   - `JWT_SECRET_KEY`: Random 256-bit secret for JWT tokens
   - `GROQ_API_KEY`: Your Groq API key for LLM
   - `CLOUDINARY_CLOUD_NAME`: Your Cloudinary cloud name
   - `CLOUDINARY_API_KEY`: Your Cloudinary API key
   - `CLOUDINARY_API_SECRET`: Your Cloudinary API secret

   **Optional:**
   - `GROQ_TTS_API_KEY`: Separate Groq API key for TTS (defaults to GROQ_API_KEY)
   - `CORS_ORIGINS`: Comma-separated allowed origins (defaults include localhost)

4. **Wait for build:**
   The Space will automatically build the Docker image and start the service.

### Environment Variables Reference

See `.env.example` for a complete list of environment variables and their descriptions.

### Health Check

Once deployed, verify the service is running:
```
https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/health
```

### API Documentation

Interactive API documentation is available at:
```
https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/docs
```

## Local Development

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Run database migrations:**
   ```bash
   python scripts/add_roleplay_metrics.py
   python scripts/add_roleplay_turn_audio.py
   python scripts/add_feedback_columns.py
   python scripts/seed_prompts.py
   ```

5. **Start the server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Tech Stack

- **Framework**: FastAPI 0.115
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Authentication**: JWT with bcrypt
- **AI/ML**:
  - LLM: Groq API with `openai/gpt-oss-120b`
  - Speech-to-Text: OpenAI Whisper via `faster-whisper`
  - Text-to-Speech: Groq API with `canopylabs/orpheus-v1-english`
- **Storage**: Cloudinary for audio files
- **Rate Limiting**: SlowAPI

## Performance Notes

- **Whisper Model**: The `base` model (~300MB) is pre-downloaded during Docker build
- **Expected Latency**: 15-30 seconds for analyzing 2-minute audio
- **CPU Usage**: Whisper runs on CPU with int8 quantization for efficiency
- **Memory**: Approximately 2GB RAM required

## Support

For issues or questions, please refer to the main repository documentation.
