import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Play, Pause, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

interface ConversationTurn {
  role: string;
  content: string;
  audio_url: string | null;
}

interface RoleplaySessionDetail {
  session_id: string;
  scenario: string;
  turn_count: number;
  max_turns: number;
  overall_score: number | null;
  strengths: string[] | null;
  areas_to_improve: string[] | null;
  fluency_score: number | null;
  vocabulary_score: number | null;
  grammar_score: number | null;
  structure_score: number | null;
  created_at: string;
  completed_at: string | null;
  conversation_history: ConversationTurn[];
}

export function RoleplaySessionDetail() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<RoleplaySessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [playingTurnIndex, setPlayingTurnIndex] = useState<number | null>(null);
  const audioRefs = useRef<{ [key: number]: HTMLAudioElement }>({});

  useEffect(() => {
    loadSession();
  }, [sessionId]);

  const loadSession = async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const data = await api.roleplay.getSessionDetail(sessionId);
      setSession(data);
    } catch {
      // Error loading session
    } finally {
      setLoading(false);
    }
  };

  const toggleAudio = (turnIndex: number, audioUrl: string) => {
    if (playingTurnIndex === turnIndex) {
      // Pause current audio
      audioRefs.current[turnIndex]?.pause();
      setPlayingTurnIndex(null);
    } else {
      // Pause any currently playing audio
      if (playingTurnIndex !== null) {
        audioRefs.current[playingTurnIndex]?.pause();
      }
      
      // Play new audio
      if (!audioRefs.current[turnIndex]) {
        const audio = new Audio(audioUrl);
        audio.onended = () => setPlayingTurnIndex(null);
        audioRefs.current[turnIndex] = audio;
      }
      
      audioRefs.current[turnIndex].play();
      setPlayingTurnIndex(turnIndex);
    }
  };

  const getScenarioColor = (scenario: string) => {
    const colors: Record<string, string> = {
      interview: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
      debate: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      pitch: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
    };
    return colors[scenario] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400';
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

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          onClick={() => navigate('/app/history')}
          className="rounded-full w-10 h-10 p-0 flex items-center justify-center"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-serif font-bold text-textPrimary dark:text-white">
              {session.scenario.charAt(0).toUpperCase() + session.scenario.slice(1)} Roleplay
            </h1>
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${getScenarioColor(
                session.scenario
              )}`}
            >
              {session.scenario}
            </span>
          </div>
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

      {/* Conversation */}
      <div className="space-y-8">
        <AnimatePresence>
          {session.conversation_history.map((turn, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`flex flex-col ${turn.role === 'assistant' ? 'items-start' : 'items-end'}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl p-6 ${
                  turn.role === 'assistant'
                    ? 'bg-surface dark:bg-dark-surface rounded-tl-sm text-textPrimary dark:text-gray-200 shadow-sm border border-gray-100 dark:border-gray-800'
                    : 'bg-primary text-white rounded-tr-sm shadow-md'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-1">
                    <p className="text-xs font-semibold uppercase tracking-wide mb-2 opacity-70">
                      {turn.role === 'assistant' ? 'AI' : 'You'}
                    </p>
                    <p className="text-lg leading-relaxed">{turn.content}</p>
                  </div>
                  {turn.audio_url && (
                    <button
                      onClick={() => toggleAudio(index, turn.audio_url!)}
                      className="flex-shrink-0 w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
                    >
                      {playingTurnIndex === index ? (
                        <Pause className="w-5 h-5" />
                      ) : (
                        <Play className="w-5 h-5 ml-0.5" />
                      )}
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Summary */}
      {session.completed_at && session.overall_score !== null && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-12"
        >
          <Card className="border-none shadow-sm dark:bg-dark-surface p-8 rounded-3xl bg-gradient-to-br from-primary/5 to-accent/5">
            <div className="flex items-start justify-between mb-8">
              <div>
                <h3 className="text-2xl font-serif text-textPrimary dark:text-white mb-2">Session Summary</h3>
                <p className="text-textSecondary">
                  Completed on{' '}
                  {new Date(session.completed_at).toLocaleDateString('en-US', {
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </p>
              </div>
              <div className="text-center">
                <div className="text-5xl font-light text-primary mb-2">{session.overall_score}/10</div>
                <div className="text-xs text-textSecondary uppercase tracking-wide">Overall Score</div>
              </div>
            </div>

            {/* Comprehensive Scores */}
            {session.fluency_score !== null && (
              <div className="mb-8">
                <h4 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-4">Performance Metrics</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-white/50 dark:bg-gray-800/50 rounded-xl">
                    <div className="text-2xl font-semibold text-primary">{session.fluency_score}/10</div>
                    <div className="text-xs text-textSecondary uppercase tracking-wide mt-1">Fluency</div>
                  </div>
                  <div className="text-center p-4 bg-white/50 dark:bg-gray-800/50 rounded-xl">
                    <div className="text-2xl font-semibold text-primary">{session.vocabulary_score}/10</div>
                    <div className="text-xs text-textSecondary uppercase tracking-wide mt-1">Vocabulary</div>
                  </div>
                  <div className="text-center p-4 bg-white/50 dark:bg-gray-800/50 rounded-xl">
                    <div className="text-2xl font-semibold text-primary">{session.grammar_score}/10</div>
                    <div className="text-xs text-textSecondary uppercase tracking-wide mt-1">Grammar</div>
                  </div>
                  <div className="text-center p-4 bg-white/50 dark:bg-gray-800/50 rounded-xl">
                    <div className="text-2xl font-semibold text-primary">{session.structure_score}/10</div>
                    <div className="text-xs text-textSecondary uppercase tracking-wide mt-1">Structure</div>
                  </div>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {session.strengths && session.strengths.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-4 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-600" /> Strengths
                  </h4>
                  <ul className="space-y-3">
                    {session.strengths.map((strength, i) => (
                      <li key={i} className="flex gap-3 text-sm text-textPrimary dark:text-gray-200">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-600 mt-1.5 flex-shrink-0" />
                        {strength}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {session.areas_to_improve && session.areas_to_improve.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-4 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-accent" /> Areas to Improve
                  </h4>
                  <ul className="space-y-3">
                    {session.areas_to_improve.map((area, i) => (
                      <li key={i} className="flex gap-3 text-sm text-textPrimary dark:text-gray-200">
                        <span className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 flex-shrink-0" />
                        {area}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
