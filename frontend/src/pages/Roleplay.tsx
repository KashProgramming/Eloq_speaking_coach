import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Mic, Square, RefreshCcw, Handshake } from 'lucide-react';
import { api } from '../api';
import { AudioVisualizer } from '../components/AudioVisualizer';
import { Button } from '../components/ui/Button';

export function Roleplay() {
  const [scenario, setScenario] = useState('');
  const [session, setSession] = useState<any>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [messages, setMessages] = useState<{role: string, content: string}[]>([]);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const playAudio = (audioUrl: string) => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    audioRef.current = new Audio(audioUrl);
    audioRef.current.play().catch(() => {
      // Audio playback failed
    });
  };

  const startSession = async () => {
    if (!scenario) return;
    setIsProcessing(true);
    setError('');
    try {
      const res = await api.roleplay.start({ scenario });
      setSession(res);
      setMessages([{ role: 'ai', content: res.opening_question }]);
      
      // Play opening question audio immediately
      if (res.audio_url) {
        playAudio(res.audio_url);
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to start roleplay session';
      setError(errorMessage);
    }
    setIsProcessing(false);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = handleStopRecording;
      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch {
      // Microphone access denied
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const handleStopRecording = async () => {
    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'response.webm');
    formData.append('session_id', session.session_id);

    try {
      const res = await api.roleplay.respond(formData);
      setMessages(prev => [
        ...prev,
        { role: 'user', content: res.transcript },
        ...(res.follow_up_question ? [{ role: 'ai', content: res.follow_up_question }] : [])
      ]);
      setSession((prev: any) => ({
        ...prev,
        turn_count: res.turn_count,
        ...(res.is_final_turn && res.overall_summary ? { summary: res.overall_summary } : {})
      }));
      
      // Play follow-up question audio immediately
      if (res.follow_up_audio_url) {
        playAudio(res.follow_up_audio_url);
      }
      
      setError('');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to process response';
      setError(errorMessage);
    }
    setIsProcessing(false);
  };

  const scenarios = [
    { value: 'interview', label: 'Job Interview', description: 'Practice answering interview questions' },
    { value: 'debate', label: 'Debate', description: 'Argue your position on a topic' },
    { value: 'pitch', label: 'Business Pitch', description: 'Present your idea or product' }
  ];

  if (!session) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] max-w-2xl mx-auto space-y-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-4"
        >
          <Handshake className="w-12 h-12 text-primary mx-auto mb-4" />
          <h2 className="text-4xl font-serif text-textPrimary dark:text-white">Roleplay Mode</h2>
          <p className="text-textSecondary text-lg">Defy the generic chat interface. Practice real-world scenarios naturally.</p>
        </motion.div>

        <div className="w-full space-y-6">
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {scenarios.map((s) => (
              <button
                key={s.value}
                onClick={() => setScenario(s.value)}
                className={`p-6 rounded-2xl border-2 transition-all text-left ${
                  scenario === s.value
                    ? 'border-primary bg-primary/5 dark:bg-primary/10'
                    : 'border-gray-200 dark:border-gray-800 hover:border-primary/50'
                }`}
              >
                <h3 className="text-lg font-semibold text-textPrimary dark:text-white mb-2">{s.label}</h3>
                <p className="text-sm text-textSecondary">{s.description}</p>
              </button>
            ))}
          </div>
          <div className="flex justify-center">
            <Button
              size="lg"
              className="rounded-full px-8 py-6 text-lg hover:scale-105 transition-transform"
              onClick={startSession}
              disabled={!scenario || isProcessing}
            >
              Start Roleplay <Play className="ml-2 w-5 h-5 fill-current" />
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto flex flex-col h-[85vh]">
      <div className="flex-1 overflow-y-auto py-8 space-y-12 no-scrollbar">
        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex flex-col ${msg.role === 'ai' ? 'items-start' : 'items-end'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl p-6 ${
                  msg.role === 'ai'
                    ? 'bg-surface dark:bg-dark-surface rounded-tl-sm text-textPrimary dark:text-gray-200 shadow-sm border border-gray-100 dark:border-gray-800'
                    : 'bg-primary text-white rounded-tr-sm shadow-md'
                }`}
              >
                <p className="text-lg leading-relaxed">{msg.content}</p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {session.summary && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-accent/10 p-8 rounded-3xl border border-accent/20 space-y-6"
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="text-xl font-serif text-textPrimary dark:text-white">Session Summary</h3>
              <div className="text-center">
                <div className="text-5xl font-light text-primary mb-2">{session.summary.overall_score}/10</div>
                <div className="text-xs text-textSecondary uppercase tracking-wide">Overall Score</div>
              </div>
            </div>
            
            {/* Comprehensive Scores */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-white/50 dark:bg-gray-800/50 rounded-xl">
                <div className="text-2xl font-semibold text-primary">{session.summary.avg_fluency}/10</div>
                <div className="text-xs text-textSecondary uppercase tracking-wide mt-1">Fluency</div>
              </div>
              <div className="text-center p-4 bg-white/50 dark:bg-gray-800/50 rounded-xl">
                <div className="text-2xl font-semibold text-primary">{session.summary.avg_vocabulary}/10</div>
                <div className="text-xs text-textSecondary uppercase tracking-wide mt-1">Vocabulary</div>
              </div>
              <div className="text-center p-4 bg-white/50 dark:bg-gray-800/50 rounded-xl">
                <div className="text-2xl font-semibold text-primary">{session.summary.avg_grammar}/10</div>
                <div className="text-xs text-textSecondary uppercase tracking-wide mt-1">Grammar</div>
              </div>
              <div className="text-center p-4 bg-white/50 dark:bg-gray-800/50 rounded-xl">
                <div className="text-2xl font-semibold text-primary">{session.summary.avg_structure}/10</div>
                <div className="text-xs text-textSecondary uppercase tracking-wide mt-1">Structure</div>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-8">
              <div>
                <h4 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-4">Strengths</h4>
                <ul className="space-y-2">
                  {session.summary.strengths.map((s: string, i: number) => <li key={i} className="text-sm">✓ {s}</li>)}
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-4">Focus Areas</h4>
                <ul className="space-y-2">
                  {session.summary.areas_to_improve.map((s: string, i: number) => <li key={i} className="text-sm text-accent">• {s}</li>)}
                </ul>
              </div>
            </div>
            <Button
              variant="outline"
              className="mt-6 rounded-full"
              onClick={() => { setSession(null); setScenario(''); }}
            >
              <RefreshCcw className="mr-2 w-4 h-4" /> Start New Session
            </Button>
          </motion.div>
        )}
      </div>

      {!session.summary && (
        <div className="pt-8 pb-4 flex flex-col items-center border-t border-gray-100 dark:border-gray-800">
          {error && (
            <div className="w-full max-w-md mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}
          <AnimatePresence mode="wait">
            {isRecording && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 48 }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-8 w-full max-w-sm"
              >
                <AudioVisualizer isRecording={isRecording} />
              </motion.div>
            )}
          </AnimatePresence>

          <Button
            size="lg"
            variant={isRecording ? 'destructive' : 'default'}
            className={`rounded-full w-20 h-20 flex items-center justify-center shadow-xl transition-all ${isProcessing ? 'opacity-50 pointer-events-none' : 'hover:scale-105'}`}
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isProcessing}
          >
            {isRecording ? <Square className="w-8 h-8" /> : isProcessing ? <RefreshCcw className="w-6 h-6 animate-spin" /> : <Mic className="w-8 h-8" />}
          </Button>
          <p className="mt-4 text-xs text-textSecondary uppercase tracking-widest font-semibold">
            {isRecording ? 'Listening...' : isProcessing ? 'Processing' : 'Your Turn'}
          </p>
        </div>
      )}
    </div>
  );
}
