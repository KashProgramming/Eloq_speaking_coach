import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { motion } from 'framer-motion';
import { RefreshCw, CheckCircle2, AlertTriangle, MessageSquare, Sparkles, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '../utils/cn';
import { useEffect, useState } from 'react';
import { api } from '../api';

export function Feedback() {
  const location = useLocation();
  const { id: sessionId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [result, setResult] = useState<any>(location.state?.result || null);
  const [idealAnswer, setIdealAnswer] = useState<string | null>(null);
  const [idealAnswerAudioUrl, setIdealAnswerAudioUrl] = useState<string | null>(null);
  const [loadingIdeal, setLoadingIdeal] = useState(false);
  const [loadingSession, setLoadingSession] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch session data if not available from location.state (e.g., hard refresh)
  useEffect(() => {
    if (!result && sessionId) {
      setLoadingSession(true);
      setError(null);
      api.practice.getSessionDetail(sessionId)
        .then((data) => {
          // Transform the session detail to match the expected result format
          setResult({
            session_id: data.session_id,
            transcript: data.transcript,
            metrics: {
              wpm: data.wpm,
              fillers: data.fillers,
              pauses: data.pauses,
              word_count: data.word_count,
            },
            scores: {
              fluency: data.fluency_score,
              vocabulary: data.vocabulary_score,
              grammar: data.grammar_score,
              structure: data.structure_score,
            },
            feedback: data.feedback || [],
            grammar_mistakes: data.grammar_mistakes || [],
          });
        })
        .catch((err) => {
          console.error('Failed to fetch session:', err);
          setError('Failed to load session data. Please try again.');
        })
        .finally(() => setLoadingSession(false));
    }
  }, [result, sessionId]);

  useEffect(() => {
    if (result?.session_id) {
      setLoadingIdeal(true);
      api.practice.getIdealAnswer(result.session_id)
        .then((data) => {
          setIdealAnswer(data.ideal_answer);
          setIdealAnswerAudioUrl(data.ideal_answer_audio_url);
        })
        .catch(() => {
          // Silently fail - ideal answer is optional
        })
        .finally(() => setLoadingIdeal(false));
    }
  }, [result?.session_id]);

  if (loadingSession) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-textSecondary">Loading session data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center mt-20 space-y-4">
        <p className="text-red-500">{error}</p>
        <Button onClick={() => navigate('/app/practice')} className="bg-primary hover:bg-primary/90 text-white rounded-full px-6">
          Back to Practice
        </Button>
      </div>
    );
  }

  if (!result) {
    return <div className="text-center mt-20 text-textSecondary">No feedback data available.</div>;
  }

  const { transcript, metrics, scores, feedback, grammar_mistakes, comparison } = result;
  const isRetry = !!comparison;

  const getImprovementIcon = (value: string) => {
    const numValue = parseFloat(value);
    if (numValue > 0) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (numValue < 0) return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getImprovementColor = (value: string) => {
    const numValue = parseFloat(value);
    if (numValue > 0) return 'text-green-600 dark:text-green-400';
    if (numValue < 0) return 'text-red-600 dark:text-red-400';
    return 'text-gray-500';
  };

  return (
    <div className="space-y-12">
      <div className="flex justify-between items-end">
        <div className="space-y-2">
          <h1 className="text-3xl font-serif font-bold text-textPrimary dark:text-white">
            {isRetry ? 'Retry Feedback' : 'Session Feedback'}
          </h1>
          <p className="text-textSecondary">
            {isRetry ? "Here's how you improved on your retry." : "Here's how you performed."}
          </p>
        </div>
        <Button onClick={() => navigate('/app/practice')} className="gap-2 bg-primary hover:bg-primary/90 text-white rounded-full px-6">
          <RefreshCw className="w-4 h-4" /> Try Again
        </Button>
      </div>

      {isRetry && comparison && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-primary/10 to-accent/10 dark:from-primary/20 dark:to-accent/20 border border-primary/20 rounded-2xl p-6"
        >
          <h3 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-primary" /> Improvement Comparison
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="space-y-1">
              <p className="text-xs text-textSecondary uppercase tracking-wide">WPM Change</p>
              <div className="flex items-center gap-2">
                {getImprovementIcon(comparison.improvements.wpm)}
                <span className={cn("text-2xl font-semibold", getImprovementColor(comparison.improvements.wpm))}>
                  {comparison.improvements.wpm}
                </span>
              </div>
              <p className="text-xs text-textSecondary">
                {comparison.original_attempt.wpm} → {comparison.current_attempt.wpm}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-textSecondary uppercase tracking-wide">Fillers Change</p>
              <div className="flex items-center gap-2">
                {getImprovementIcon(comparison.improvements.fillers)}
                <span className={cn("text-2xl font-semibold", getImprovementColor(comparison.improvements.fillers))}>
                  {comparison.improvements.fillers}
                </span>
              </div>
              <p className="text-xs text-textSecondary">
                {comparison.original_attempt.fillers} → {comparison.current_attempt.fillers}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-textSecondary uppercase tracking-wide">Pauses Change</p>
              <div className="flex items-center gap-2">
                {getImprovementIcon(comparison.improvements.pauses)}
                <span className={cn("text-2xl font-semibold", getImprovementColor(comparison.improvements.pauses))}>
                  {comparison.improvements.pauses}
                </span>
              </div>
              <p className="text-xs text-textSecondary">
                {comparison.original_attempt.pauses} → {comparison.current_attempt.pauses}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-textSecondary uppercase tracking-wide">Fluency Change</p>
              <div className="flex items-center gap-2">
                {getImprovementIcon(comparison.improvements.fluency_score)}
                <span className={cn("text-2xl font-semibold", getImprovementColor(comparison.improvements.fluency_score))}>
                  {comparison.improvements.fluency_score}
                </span>
              </div>
              <p className="text-xs text-textSecondary">
                {comparison.original_attempt.fluency_score} → {comparison.current_attempt.fluency_score}
              </p>
            </div>
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="col-span-1 md:col-span-2 space-y-8"
        >
          <Card className="border-none shadow-sm dark:bg-dark-surface p-6 rounded-2xl">
            <h3 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-4">Transcript</h3>
            <p className="text-lg leading-relaxed text-textPrimary dark:text-gray-200">
              {transcript}
            </p>
            {grammar_mistakes.length > 0 && (
              <div className="mt-8 border-t border-gray-100 dark:border-gray-800 pt-6">
                <h4 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-accent" /> Grammar Insights
                </h4>
                <ul className="space-y-3">
                  {grammar_mistakes.map((mistake: string, idx: number) => (
                    <li key={idx} className="flex gap-3 text-sm text-textSecondary dark:text-gray-300">
                      <span className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 flex-shrink-0" />
                      {mistake}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Card>

          <Card className="border-none shadow-sm dark:bg-dark-surface p-6 rounded-2xl bg-surface/50">
            <h3 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-4 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-primary" /> Key Takeaways
            </h3>
            <ul className="space-y-4">
              {feedback.map((point: string, idx: number) => (
                <li key={idx} className="flex gap-3 text-base text-textPrimary dark:text-gray-200">
                  <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0" />
                  {point}
                </li>
              ))}
            </ul>
          </Card>

          {(idealAnswer || loadingIdeal) && (
            <Card className="border-none shadow-sm dark:bg-dark-surface p-6 rounded-2xl bg-gradient-to-br from-primary/5 to-accent/5">
              <h3 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-4 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" /> Ideal Answer
              </h3>
              {loadingIdeal ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : (
                <>
                  <p className="text-base leading-relaxed text-textPrimary dark:text-gray-200">
                    {idealAnswer}
                  </p>
                  {idealAnswerAudioUrl && (
                    <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800">
                      <p className="text-xs text-textSecondary uppercase tracking-wide mb-2">Listen to Ideal Answer</p>
                      <audio controls className="w-full" style={{ height: '40px' }}>
                        <source src={idealAnswerAudioUrl} type="audio/wav" />
                        Your browser does not support the audio element.
                      </audio>
                    </div>
                  )}
                </>
              )}
            </Card>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="space-y-6"
        >
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
                      className={cn("bg-primary h-2 rounded-full", item.score < 6 ? 'bg-accent' : 'bg-primary')}
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
