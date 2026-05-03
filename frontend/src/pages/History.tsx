import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, MessageSquare, Mic, Calendar, TrendingUp, ChevronDown, ChevronUp } from 'lucide-react';
import { api } from '../api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

interface AttemptSummary {
  session_id: string;
  attempt_number: number;
  created_at: string;
  fluency_score: number;
  vocabulary_score: number;
  grammar_score: number;
  structure_score: number;
  wpm: number;
  fillers: number;
  pauses: number;
}

interface GroupedPracticeSession {
  prompt_text: string;
  prompt_category: string;
  date: string;
  attempts: AttemptSummary[];
}

interface RoleplaySession {
  session_id: string;
  scenario: string;
  turn_count: number;
  max_turns: number;
  overall_score: number | null;
  created_at: string;
  completed_at: string | null;
}

export function History() {
  const [activeTab, setActiveTab] = useState<'practice' | 'roleplay'>('practice');
  const [practiceSessions, setPracticeSessions] = useState<GroupedPracticeSession[]>([]);
  const [roleplaySessions, setRoleplaySessions] = useState<RoleplaySession[]>([]);
  const [expandedSessions, setExpandedSessions] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const [practiceData, roleplayData] = await Promise.all([
        api.practice.getGroupedHistory(50, 0),
        api.roleplay.getSessions(50, 0),
      ]);
      setPracticeSessions(practiceData.sessions);
      setRoleplaySessions(roleplayData.sessions);
    } catch {
      // Error loading history
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

    if (diffInDays === 0) return 'Today';
    if (diffInDays === 1) return 'Yesterday';
    if (diffInDays < 7) return `${diffInDays} days ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
  };

  const toggleExpanded = (sessionKey: string) => {
    setExpandedSessions((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(sessionKey)) {
        newSet.delete(sessionKey);
      } else {
        newSet.add(sessionKey);
      }
      return newSet;
    });
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      opinion: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      narration: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      explanation: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      argument: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    };
    return colors[category] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400';
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

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div className="space-y-2">
          <h1 className="text-3xl font-serif font-bold text-textPrimary dark:text-white">Your History</h1>
          <p className="text-textSecondary">Review your past practice sessions and roleplays</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-gray-800">
        <button
          onClick={() => setActiveTab('practice')}
          className={`px-6 py-3 font-medium transition-colors relative ${
            activeTab === 'practice'
              ? 'text-primary'
              : 'text-textSecondary hover:text-textPrimary dark:hover:text-white'
          }`}
        >
          Practice Sessions
          {activeTab === 'practice' && (
            <motion.div
              layoutId="activeTab"
              className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
            />
          )}
        </button>
        <button
          onClick={() => setActiveTab('roleplay')}
          className={`px-6 py-3 font-medium transition-colors relative ${
            activeTab === 'roleplay'
              ? 'text-primary'
              : 'text-textSecondary hover:text-textPrimary dark:hover:text-white'
          }`}
        >
          Roleplay Sessions
          {activeTab === 'roleplay' && (
            <motion.div
              layoutId="activeTab"
              className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
            />
          )}
        </button>
      </div>

      {/* Practice Sessions */}
      {activeTab === 'practice' && (
        <div className="space-y-4">
          {practiceSessions.length === 0 ? (
            <Card className="p-12 text-center border-none shadow-sm dark:bg-dark-surface">
              <Mic className="w-12 h-12 text-textSecondary mx-auto mb-4 opacity-50" />
              <p className="text-textSecondary">No practice sessions yet. Start practicing to see your history!</p>
              <Button onClick={() => navigate('/app/practice')} className="mt-6 rounded-full">
                Start Practicing
              </Button>
            </Card>
          ) : (
            practiceSessions.map((session, idx) => {
              const sessionKey = `${session.date}-${idx}`;
              const isExpanded = expandedSessions.has(sessionKey);
              const hasMultipleAttempts = session.attempts.length > 1;
              const latestAttempt = session.attempts[session.attempts.length - 1];
              const bestFluency = Math.max(...session.attempts.map(a => a.fluency_score));

              return (
                <motion.div
                  key={sessionKey}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <Card className="border-none shadow-sm dark:bg-dark-surface overflow-hidden">
                    {/* Main Session Card */}
                    <div className="p-6">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 space-y-3">
                          <div className="flex items-center gap-3">
                            <span
                              className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${getCategoryColor(
                                session.prompt_category
                              )}`}
                            >
                              {session.prompt_category}
                            </span>
                            <span className="flex items-center gap-1.5 text-sm text-textSecondary">
                              <Calendar className="w-4 h-4" />
                              {formatDate(session.date)}
                            </span>
                            {hasMultipleAttempts && (
                              <span className="px-2 py-0.5 rounded-full text-xs bg-primary/10 text-primary dark:bg-primary/20">
                                {session.attempts.length} attempts
                              </span>
                            )}
                          </div>
                          <p className="text-lg text-textPrimary dark:text-white font-medium line-clamp-2">
                            {session.prompt_text}
                          </p>
                          {!isExpanded && (
                            <div className="flex items-center gap-6 text-sm text-textSecondary">
                              <span className="flex items-center gap-1.5">
                                <TrendingUp className="w-4 h-4" />
                                {latestAttempt.wpm} WPM
                              </span>
                              <span className="flex items-center gap-1.5">
                                <MessageSquare className="w-4 h-4" />
                                {latestAttempt.fillers} fillers
                              </span>
                              <span className="flex items-center gap-1.5">
                                <Clock className="w-4 h-4" />
                                {latestAttempt.pauses} pauses
                              </span>
                            </div>
                          )}
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <div className="text-3xl font-light text-primary">
                            {hasMultipleAttempts ? bestFluency : latestAttempt.fluency_score}/10
                          </div>
                          <div className="text-xs text-textSecondary uppercase tracking-wide">
                            {hasMultipleAttempts ? 'Best' : 'Fluency'}
                          </div>
                        </div>
                      </div>

                      {/* Expand/Collapse Button */}
                      {hasMultipleAttempts && (
                        <button
                          onClick={() => toggleExpanded(sessionKey)}
                          className="mt-4 flex items-center gap-2 text-sm text-primary hover:text-primary/80 transition-colors"
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp className="w-4 h-4" />
                              Hide attempts
                            </>
                          ) : (
                            <>
                              <ChevronDown className="w-4 h-4" />
                              Show all attempts
                            </>
                          )}
                        </button>
                      )}
                    </div>

                    {/* Expanded Attempts List */}
                    <AnimatePresence>
                      {(isExpanded || !hasMultipleAttempts) && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="border-t border-gray-100 dark:border-gray-800"
                        >
                          <div className="p-6 pt-4 space-y-3">
                            {session.attempts.map((attempt) => (
                              <div
                                key={attempt.session_id}
                                className="flex items-center justify-between p-4 rounded-lg bg-gray-50 dark:bg-gray-900/50 hover:bg-gray-100 dark:hover:bg-gray-900 transition-colors cursor-pointer"
                                onClick={() => navigate(`/app/history/practice/${attempt.session_id}`)}
                              >
                                <div className="flex-1 space-y-2">
                                  <div className="flex items-center gap-3">
                                    <span className="text-sm font-medium text-textPrimary dark:text-white">
                                      Attempt {attempt.attempt_number}
                                    </span>
                                    <span className="text-xs text-textSecondary">
                                      {formatTime(attempt.created_at)}
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-2 text-xs text-textSecondary">
                                    <span>Fluency: {attempt.fluency_score}</span>
                                    <span>•</span>
                                    <span>Vocab: {attempt.vocabulary_score}</span>
                                    <span>•</span>
                                    <span>Grammar: {attempt.grammar_score}</span>
                                    <span>•</span>
                                    <span>Structure: {attempt.structure_score}</span>
                                  </div>
                                  <div className="flex items-center gap-4 text-xs text-textSecondary">
                                    <span>{attempt.wpm} WPM</span>
                                    <span>•</span>
                                    <span>{attempt.fillers} fillers</span>
                                    <span>•</span>
                                    <span>{attempt.pauses} pauses</span>
                                  </div>
                                </div>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="text-primary hover:text-primary/80"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    navigate(`/app/history/practice/${attempt.session_id}`);
                                  }}
                                >
                                  View Details →
                                </Button>
                              </div>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </Card>
                </motion.div>
              );
            })
          )}
        </div>
      )}

      {/* Roleplay Sessions */}
      {activeTab === 'roleplay' && (
        <div className="space-y-4">
          {roleplaySessions.length === 0 ? (
            <Card className="p-12 text-center border-none shadow-sm dark:bg-dark-surface">
              <MessageSquare className="w-12 h-12 text-textSecondary mx-auto mb-4 opacity-50" />
              <p className="text-textSecondary">No roleplay sessions yet. Start a roleplay to see your history!</p>
              <Button onClick={() => navigate('/app/roleplay')} className="mt-6 rounded-full">
                Start Roleplay
              </Button>
            </Card>
          ) : (
            roleplaySessions.map((session) => (
              <motion.div
                key={session.session_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card
                  className="p-6 border-none shadow-sm dark:bg-dark-surface hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => navigate(`/app/history/roleplay/${session.session_id}`)}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-3">
                      <div className="flex items-center gap-3">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${getScenarioColor(
                            session.scenario
                          )}`}
                        >
                          {session.scenario}
                        </span>
                        <span className="flex items-center gap-1.5 text-sm text-textSecondary">
                          <Calendar className="w-4 h-4" />
                          {formatDate(session.created_at)}
                        </span>
                        {session.completed_at && (
                          <span className="px-2 py-0.5 rounded-full text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                            Completed
                          </span>
                        )}
                      </div>
                      <p className="text-lg text-textPrimary dark:text-white font-medium">
                        {session.scenario.charAt(0).toUpperCase() + session.scenario.slice(1)} Roleplay
                      </p>
                      <div className="flex items-center gap-6 text-sm text-textSecondary">
                        <span className="flex items-center gap-1.5">
                          <MessageSquare className="w-4 h-4" />
                          {session.turn_count} / {session.max_turns} turns
                        </span>
                      </div>
                    </div>
                    {session.overall_score !== null && (
                      <div className="flex flex-col items-end gap-2">
                        <div className="text-3xl font-light text-primary">{session.overall_score}/10</div>
                        <div className="text-xs text-textSecondary uppercase tracking-wide">Score</div>
                      </div>
                    )}
                  </div>
                </Card>
              </motion.div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
