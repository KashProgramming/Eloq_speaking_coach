import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, Square, Loader } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../api';
import { AudioVisualizer } from '../components/AudioVisualizer';
import { Button } from '../components/ui/Button';

export function Practice() {
  const [prompt, setPrompt] = useState<{ id: string; text: string } | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    loadPrompt();
  }, []);

  const loadPrompt = async () => {
    try {
      const res = await api.practice.getPrompt();
      setPrompt({ id: res.prompt_id, text: res.text });
      setError('');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to load prompt';
      setError(errorMessage);
    }
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
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const handleStopRecording = async () => {
    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'recording.webm');
    if (prompt) {
      formData.append('prompt_id', prompt.id);
    }

    try {
      const result = await api.practice.analyze(formData);
      navigate(`/app/feedback/${result.session_id}`, { state: { result } });
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to analyze audio';
      setError(errorMessage);
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] max-w-2xl mx-auto space-y-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-4"
      >
        <span className="text-secondary dark:text-gray-400 uppercase tracking-widest text-sm font-semibold">
          Daily Practice
        </span>
        <h2 className="text-4xl font-serif text-textPrimary dark:text-white leading-tight">
          {prompt ? prompt.text : 'Loading your prompt...'}
        </h2>
      </motion.div>

      {error && (
        <div className="w-full bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      <div className="w-full flex flex-col items-center space-y-8">
        <AnimatePresence mode="wait">
          {isRecording && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 48 }}
              exit={{ opacity: 0, height: 0 }}
            >
              <AudioVisualizer isRecording={isRecording} />
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex items-center justify-center">
          {isProcessing ? (
            <motion.div className="flex flex-col items-center space-y-4">
              <Loader className="w-12 h-12 text-primary animate-spin" />
              <p className="text-textSecondary">Analyzing your speech...</p>
            </motion.div>
          ) : (
            <Button
              size="lg"
              variant={isRecording ? 'destructive' : 'default'}
              className="rounded-full w-24 h-24 flex items-center justify-center shadow-xl hover:scale-105 transition-transform"
              onClick={isRecording ? stopRecording : startRecording}
            >
              {isRecording ? <Square className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
            </Button>
          )}
        </div>
        
        {!isRecording && !isProcessing && (
          <p className="text-textSecondary text-sm">
            Press to start recording your response
          </p>
        )}
      </div>
    </div>
  );
}
