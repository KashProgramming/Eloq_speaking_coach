import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Play, Pause, CheckCircle2, AlertTriangle, MessageSquare, Sparkles } from 'lucide-react';
import { api } from '../api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { cn } from '../utils/cn';

interface SessionDetail {
  session_id: string;
  prompt_text: string;
  prompt_category: string;
  audio_url: string;
  transcript: string;
  duration: number;
  wpm: number;
  fillers: number;
  pauses: number;
  word_count: number;
  fluency_score: number;
  vocabulary_score: number;
  grammar_score: number;
  structure_score: number;
  ideal_answer: string | null;
  ideal_answer_audio_url: string | null;
  feedback: string[] | null;
  grammar_mistakes: string[] | null;
  created_at: string;
}

export function PracticeSessionDetail() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    loadSession();
  }, [sessionId]);

  const loadSession = async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const data = await api.practice.getSessionDetail(sessionId);
      setSession(data);
    } catch {
      // Error loading session
    } finally {
      setLoading(false);
    }
  };

  const toggleAudio = () => {
    if (!audioRef.current) return;
    
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleAudioEnded = () => {
    setIsPlaying(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="text-center mt-20">
        <p className="text-textSecondary">Session not found</p>
        <Button onClick={() => navigate('/app/history')} className="mt-4 rounded-full">
          Back to History
        </Button>
      </div>
    );
  }

  const scores = {
    fluency: session.fluency_score,
    vocabulary: session.vocabulary_score,
    grammar: session.grammar_score,
    structure: session.structure_score,
  };

  const metrics = {
    wpm: session.wpm,
    fillers: session.fillers,
    pauses: session.pauses,
    word_count: session.word_count,
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          onClick={() => navigate('/app/history')}
          className="rounded-full w-10 h-10 p-0 flex items-center justify-center"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div className="space-y-1">
          <h1 className="text-3xl font-serif font-bold text-textPrimary dark:text-white">Practice Session</h1>
          <p className="text-textSecondary">
            {new Date(session.created_at).toLocaleDateString('en-US', {
              month: 'long',
              day: 'numeric',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        </div>
      </div>

      {/* Prompt */}
      <Card className="border-none shadow-sm dark:bg-dark-surface p-8 rounded-2xl bg-gradient-to-br from-primary/5 to-accent/5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <span className="text-xs font-semibold tracking-wide text-textSecondary uppercase mb-3 block">
              Prompt
            </span>
            <p className="text-2xl font-serif text-textPrimary dark:text-white leading-relaxed">
              {session.prompt_text}
            </p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide bg-primary/10 text-primary">
            {session.prompt_category}
          </span>
        </div>
      </Card>

      {/* Audio Player */}
      <Card className="border-none shadow-sm dark:bg-dark-surface p-6 rounded-2xl">
        <div className="flex items-center gap-4">
          <Button
            onClick={toggleAudio}
            variant={isPlaying ? 'default' : 'outline'}
            className="rounded-full w-14 h-14 p-0 flex items-center justify-center"
          >
            {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 ml-1" />}
          </Button>
          <div className="flex-1">
            <p className="text-sm font-medium text-textPrimary dark:text-white mb-1">Your Recording</p>
            <p className="text-xs text-textSecondary">
              {isPlaying ? 'Playing...' : 'Click to play your response'}
            </p>
          </div>
          <audio
            ref={audioRef}
            src={session.audio_url}
            onEnded={handleAudioEnded}
            onPause={() => setIsPlaying(false)}
            onPlay={() => setIsPlaying(true)}
          />
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="col-span-1 md:col-span-2 space-y-8"
        >
          {/* Transcript */}
          <Card className="border-none shadow-sm dark:bg-dark-surface p-6 rounded-2xl">
            <h3 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-4">Transcript</h3>
            <p className="text-lg leading-relaxed text-textPrimary dark:text-gray-200">{session.transcript}</p>

            {session.grammar_mistakes && session.grammar_mistakes.length > 0 && (
              <div className="mt-8 border-t border-gray-100 dark:border-gray-800 pt-6">
                <h4 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-accent" /> Grammar Insights
                </h4>
                <ul className="space-y-3">
                  {session.grammar_mistakes.map((mistake, idx) => (
                    <li key={idx} className="flex gap-3 text-sm text-textSecondary dark:text-gray-300">
                      <span className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 flex-shrink-0" />
                      {mistake}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Card>

          {/* Feedback */}
          {session.feedback && session.feedback.length > 0 && (
            <Card className="border-none shadow-sm dark:bg-dark-surface p-6 rounded-2xl bg-surface/50">
              <h3 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-4 flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-primary" /> Key Takeaways
              </h3>
              <ul className="space-y-4">
                {session.feedback.map((point, idx) => (
                  <li key={idx} className="flex gap-3 text-base text-textPrimary dark:text-gray-200">
                    <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0" />
                    {point}
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {/* Ideal Answer */}
          {session.ideal_answer && (
            <Card className="border-none shadow-sm dark:bg-dark-surface p-6 rounded-2xl bg-gradient-to-br from-primary/5 to-accent/5">
              <h3 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-4 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" /> Ideal Answer
              </h3>
              <p className="text-base leading-relaxed text-textPrimary dark:text-gray-200">
                {session.ideal_answer}
              </p>
              {session.ideal_answer_audio_url && (
                <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800">
                  <p className="text-xs text-textSecondary uppercase tracking-wide mb-2">Listen to Ideal Answer</p>
                  <audio controls className="w-full" style={{ height: '40px' }}>
                    <source src={session.ideal_answer_audio_url} type="audio/wav" />
                    Your browser does not support the audio element.
                  </audio>
                </div>
              )}
            </Card>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="space-y-6"
        >
          {/* Metrics */}
          <Card className="border-none shadow-sm dark:bg-dark-surface p-6 rounded-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-full -z-10" />
            <h3 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-6">Metrics</h3>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-3xl font-light text-textPrimary dark:text-white">{metrics.wpm}</p>
                <p className="text-xs text-textSecondary uppercase tracking-wide mt-1">Words / Min</p>
              </div>
              <div>
                <p className="text-3xl font-light text-accent">{metrics.fillers}</p>
                <p className="text-xs text-textSecondary uppercase tracking-wide mt-1">Filler Words</p>
              </div>
              <div>
                <p className="text-3xl font-light text-textPrimary dark:text-white">{metrics.pauses}</p>
                <p className="text-xs text-textSecondary uppercase tracking-wide mt-1">Pauses</p>
              </div>
              <div>
                <p className="text-3xl font-light text-textPrimary dark:text-white">{metrics.word_count}</p>
                <p className="text-xs text-textSecondary uppercase tracking-wide mt-1">Total Words</p>
              </div>
            </div>
          </Card>

          {/* Scores */}
          <Card className="border-none shadow-sm dark:bg-dark-surface p-6 rounded-2xl">
            <h3 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-6">Scores</h3>
            <div className="space-y-5">
              {[
                { label: 'Fluency', score: scores.fluency },
                { label: 'Vocabulary', score: scores.vocabulary },
                { label: 'Grammar', score: scores.grammar },
                { label: 'Structure', score: scores.structure },
              ].map((item) => (
                <div key={item.label} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-textSecondary font-medium">{item.label}</span>
                    <span className="text-textPrimary dark:text-white font-semibold">{item.score}/10</span>
                  </div>
                  <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-2">
                    <motion.div
                      className={cn('bg-primary h-2 rounded-full', item.score < 6 ? 'bg-accent' : 'bg-primary')}
                      initial={{ width: 0 }}
                      animate={{ width: `${(item.score / 10) * 100}%` }}
                      transition={{ duration: 1, ease: 'easeOut' }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
