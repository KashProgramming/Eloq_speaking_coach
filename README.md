# Eloq - AI-Powered Public Speaking & Fluency Coach

> Transform your speaking skills through AI-driven practice, real-time feedback, and immersive roleplay scenarios.

---

## Overview

**Eloq** is a comprehensive web application designed to help users improve their public speaking and English fluency through:

- **Daily adaptive prompts** tailored to your skill level
- **AI-driven speech analysis** with detailed feedback
- **Measurable progress tracking** with streak counters and improvement metrics
- **Roleplay-based scenarios** for real-world practice (interviews, debates, pitches)
- **On-demand ideal answer generation** with text-to-speech playback
- **Complete session history** with audio replay capabilities

---

## 🚨 The Problem

Many people struggle with public speaking and English fluency:

- **Students** preparing for IELTS exams or job interviews
- **Non-native English speakers** looking to improve communication skills
- **Early professionals** needing to present ideas confidently
- **Anyone** wanting to reduce filler words, improve pacing, and speak more clearly

Traditional solutions are expensive (coaching), time-consuming (classes), or lack personalized feedback (generic apps).

---

## ✨ The Solution

Eloq provides an **affordable, accessible, and intelligent** platform that:

1. **Listens** to your speech using advanced transcription (Whisper AI)
2. **Analyzes** your performance across multiple dimensions (fluency, vocabulary, grammar, structure)
3. **Provides** actionable feedback powered by large language models (Groq LLM)
4. **Tracks** your progress over time with detailed metrics
5. **Adapts** to your skill level with progressive difficulty
6. **Engages** you with realistic roleplay scenarios

All from the comfort of your browser, at your own pace.

---

## 📸 Screenshots

### Practice Mode
![Practice Mode](docs/screenshots/practice.png)

### Feedback Page
![Feedback](docs/screenshots/feedback1.png)
![Feedback](docs/screenshots/feedback2.png)

### Roleplay Mode
![Roleplay](docs/screenshots/roleplay1.png)
![Roleplay](docs/screenshots/roleplay2.png)

### Progress Dashboard
![Progress](docs/screenshots/progress1.png)
![Progress](docs/screenshots/progress2.png)

### History View
![History](docs/screenshots/history1.png)
![History](docs/screenshots/history2.png)

---

## 🌟 Key Features

### Daily Practice Mode
- **Smart Prompt Selection**: Get prompts matched to your skill level (beginner → intermediate → advanced)
- **Audio Recording**: Record your response directly in the browser (30s - 3min)
- **Real-time Transcription**: Powered by OpenAI Whisper for accurate speech-to-text
- **Comprehensive Analysis**:
  - **Metrics**: Words per minute (WPM), filler word count, awkward pauses
  - **Scores**: Fluency, vocabulary, grammar, structure (1-10 scale)
  - **Feedback**: 2-4 actionable improvement suggestions
  - **Grammar Insights**: Specific mistakes with corrections
- **Ideal Answer Generation**: See a polished version of your response with TTS audio
- **Retry System**: Practice the same prompt up to 3 times with comparison metrics

### Roleplay Mode
- **Three Scenarios**:
  - **Interview**: Practice answering common interview questions
  - **Debate**: Argue your position on controversial topics
  - **Pitch**: Present your business idea or product
- **Interactive Conversations**: 3-turn dialogues with AI that adapts to your responses
- **Comprehensive Evaluation**: Same metrics as practice mode
  - **Per-Turn Analysis**: Fluency, vocabulary, grammar, structure scores (1-10)
  - **Turn Metrics**: WPM, filler words, pauses tracked for each response
  - **Content Feedback**: Strengths and weaknesses for each turn
- **Audio Playback**: Listen to both your responses and AI questions
- **Session Summary**: 
  - Overall score with averaged comprehensive metrics
  - Performance breakdown across all 4 dimensions
  - Strengths and areas to improve

### Progress Dashboard
- **Streak Counter**: Track consecutive days of practice (includes both practice and roleplay)
- **Session Statistics**: Total sessions completed (practice + roleplay combined)
- **Improvement Metrics**: Week-over-week percentage changes in:
  - Fluency, vocabulary, grammar scores (from both practice and roleplay)
  - Filler words and pauses
- **Weekly Trends**: Visual graph combining performance from both practice and roleplay sessions
- **Level Progression**: See prompts completed and remaining in your current level

### Complete History
- **Practice Sessions**: View all past practice attempts grouped by prompt
  - See all retry attempts with expandable cards
  - Compare scores across attempts
  - Replay audio recordings
  - Review full feedback and transcripts
- **Roleplay Sessions**: Browse all roleplay conversations
  - Full dialogue history with audio
  - Comprehensive metrics display (fluency, vocabulary, grammar, structure)
  - Session summaries with performance breakdown
  - Completion status tracking

### Account Management
- **Secure Authentication**: JWT-based login with refresh tokens
- **Password Management**: Change password with validation
- **Account Deletion**: Permanently delete account and all data
- **Login Protection**: Account lockout after 3 failed attempts (1-hour cooldown)

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 19.2 with TypeScript
- **Build Tool**: Vite 8.0
- **Routing**: React Router DOM 7.14
- **Styling**: Tailwind CSS 3.4
- **Animations**: Framer Motion 12.38
- **Icons**: Lucide React 1.8
- **HTTP Client**: Axios 1.15
- **Audio**: Web Audio API with MediaRecorder

### Backend
- **Framework**: FastAPI 0.115
- **Server**: Uvicorn 0.32 (ASGI)
- **Database**: PostgreSQL with SQLAlchemy 2.0 ORM
- **Authentication**: JWT (python-jose) with bcrypt password hashing
- **AI/ML**:
  - **LLM**: Groq API with `openai/gpt-oss-120b` model
  - **Speech-to-Text**: OpenAI Whisper via `faster-whisper` (local)
  - **Text-to-Speech**: Groq API with `canopylabs/orpheus-v1-english` model
- **Storage**: Cloudinary for audio file hosting
- **Rate Limiting**: SlowAPI for endpoint protection
- **Audio Processing**: pydub, faster-whisper

### Infrastructure
- **Database**: PostgreSQL (Supabase)
- **File Storage**: Cloudinary CDN
- **Deployment**: 
  - Backend: Hugging Face Spaces (Docker)
  - Frontend: Vercel
  - Database: Supabase (free tier)

---

### Data Flow: Practice Session

```
1. User records audio → Browser MediaRecorder
2. Audio uploaded → FastAPI /practice/analyze
3. Audio stored → Cloudinary CDN
4. Audio transcribed → Whisper (local)
5. Metrics computed → Metrics Engine (WPM, fillers, pauses)
6. LLM evaluation → Groq API (scores + feedback)
7. Data stored → PostgreSQL
8. Response returned → Frontend
9. User views feedback → Feedback page
10. User requests ideal answer → LLM generates + TTS creates audio
11. User retries → Comparison with original attempt
```

---

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18 or higher
- **PostgreSQL**: 14 or higher (or Supabase account)
- **Cloudinary Account**: For audio storage
- **Groq API Keys**: For LLM and TTS access (can use same or separate keys)

**Note:** For production deployment, the backend is designed to run on Hugging Face Spaces. See the [Deployment](#-deployment) section for details.

### Environment Variables

Create `.env` files in both backend and frontend directories:

#### Backend `.env`
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/eloq

# JWT
JWT_SECRET_KEY=your-secret-key-here-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Groq API (LLM)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Groq API (Text-to-Speech)
# You can use the same key as above or a separate key for TTS
GROQ_TTS_API_KEY=gsk_your_groq_tts_api_key_here
GROQ_TTS_MODEL=canopylabs/orpheus-v1-english
GROQ_TTS_VOICE=austin  # Options: austin, autumn, diana, hannah, daniel, troy

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Whisper
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# App
APP_NAME=Eloq
DEBUG=True
```

#### Frontend `.env`
```bash
# Update with your Hugging Face Space URL
VITE_API_URL=https://username-spacename.hf.space
```

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/eloq.git
cd eloq
```

#### 2. Backend Setup
```bash
cd eloq/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python scripts/add_roleplay_metrics.py
python scripts/add_roleplay_turn_audio.py
python scripts/add_feedback_columns.py

# Seed prompts
python scripts/seed_prompts.py

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Frontend Setup
```bash
cd eloq/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### 4. Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Features Deep Dive

### 1. Smart Prompt Selection Algorithm

The system automatically selects prompts based on:
- **User's current level** (beginner/intermediate/advanced)
- **Completed prompts** (never repeats within same level)
- **Level progression** (auto-advances when all prompts exhausted)

### 2. Speech Analysis Pipeline

**Metrics Computation** (No LLM):
- **WPM**: `(word_count / duration_seconds) * 60`
- **Fillers**: Count of "um", "uh", "like", "you know", etc.
- **Pauses**: Gaps > 0.8 seconds between speech segments

**LLM Evaluation** (Groq):
- **Fluency** (1-10): Delivery smoothness, natural flow
- **Vocabulary** (1-10): Word choice variety and appropriateness
- **Grammar** (1-10): Correctness of language structure
- **Structure** (1-10): Organization and coherence

**Note**: Both practice and roleplay modes use the same comprehensive evaluation criteria for consistency.

### 3. Retry System with Comparison

Users can retry the same prompt up to 3 times per day:
- **Attempt 1**: Original session
- **Attempt 2-3**: Retry sessions linked to original
- **Comparison**: Shows improvements/regressions in:
  - WPM, fillers, pauses, fluency score
  - Visual indicators (↑ green, ↓ red, → gray)

### 4. Grouped History View

Sessions are grouped by prompt with expandable attempts:
- **Collapsed**: Shows best score and latest metrics
- **Expanded**: Lists all attempts with individual scores
- **Click any attempt**: View full details with audio replay

### 5. Text-to-Speech Integration

- **Ideal Answers**: Generated on-demand with TTS audio
- **Roleplay Questions**: AI questions have audio playback
- **Cloud-based TTS**: Uses Groq API with Orpheus model
- **Voice Options**: Multiple voices available (austin, autumn, diana, hannah, daniel, troy)
- **Separate API Key**: Optional separate key for TTS to isolate rate limits
- **Graceful Degradation**: App works without TTS configured (text-only mode)

### 6. Roleplay Comprehensive Metrics

Roleplay sessions now include the same detailed evaluation as practice mode:
- **Per-Turn Evaluation**: Each of the 3 turns is evaluated with comprehensive metrics
- **Metrics Stored**: WPM, fillers, pauses, and all 4 scores tracked per turn
- **Averaged Scores**: Final summary shows averaged fluency, vocabulary, grammar, and structure scores
- **Progress Integration**: Roleplay sessions contribute to:
  - Daily streak calculation
  - Weekly fluency trend chart
  - Overall improvement metrics
  - Total session count
- **Consistent Evaluation**: Same LLM prompts and scoring criteria as practice mode

---

## 🔒 Security

### Authentication
- **JWT Tokens**: HS256 algorithm with 256-bit secret
- **Access Token**: 15-minute expiration
- **Refresh Token**: 7-day expiration
- **Password Hashing**: bcrypt with 12 rounds

### Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 number

### Login Protection
- **Failed Attempts**: Max 3 attempts
- **Account Lockout**: 1 hour after 3 failures
- **Automatic Reset**: Counter resets on successful login

### Rate Limiting
- **Signup**: 5 requests/hour per IP
- **Analysis**: 10 requests/hour per user
- **Progress**: 100 requests/hour per user
- **Account Deletion**: 3 requests/hour per user

### API Keys
- **Separate Keys**: Use different Groq API keys for LLM and TTS to isolate rate limits
- **Optional TTS**: App functions without TTS configured (text-only mode)
- **Key Rotation**: Easy to rotate keys via environment variables

### File Upload Validation
- **Max Size**: 10MB
- **Allowed Formats**: .wav, .webm, .mp3
- **Duration**: 30 seconds - 3 minutes
- **Content Type**: Validated on server

### CORS Configuration
- **Allowed Origins**: Configurable via environment
- **Credentials**: Enabled for cookie-based auth
- **Methods**: All HTTP methods allowed
- **Headers**: All headers allowed

---

## 📈 Performance Metrics

### Expected Latency
- **Prompt Loading**: < 200ms
- **Audio Upload**: 2-5 seconds (depends on file size)
- **Whisper Transcription**: 2-5 seconds per minute of audio
- **LLM Evaluation**: 3-8 seconds
- **Total Analysis**: 15-30 seconds for 2-minute audio

### Optimization Strategies
- **Caching**: LLM responses cached for ideal answers
- **Pagination**: History endpoints paginated (50 items/page)
- **CDN**: Audio files served from Cloudinary CDN
- **Lazy Loading**: Audio files loaded on-demand
- **Database Indexing**: Indexes on user_id, created_at, level

---

## 🤝 Contributing

Contributions and feedback is welcome! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-feature`
3. **Commit your changes**: `git commit -m 'Add new feature'`
4. **Push to branch**: `git push origin feature/new-feature`
5. **Open a Pull Request**

## 🗺️ Roadmap

### Upcoming Features
- [ ] Speech analysis with audio-level feedback
- [ ] Dynamic prompts
- [ ] Gamification (badges, achievements, XP system)
- [ ] Mobile app version (React Native)
