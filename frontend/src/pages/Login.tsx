import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { BookOpen } from 'lucide-react';
import { api } from '../api';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSignup, setIsSignup] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    
    try {
      if (isSignup) {
        await api.auth.signup({ email, password });
        setSuccessMessage('Account created successfully! Please login.');
        setIsSignup(false);
        setPassword('');
      } else {
        await login({ email, password });
        // Only clear password on successful login (which will navigate away)
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'An error occurred';
      setError(errorMessage);
      // Clear password on failed login attempt
      setPassword('');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background dark:bg-dark-background px-6">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className="max-w-md w-full space-y-12"
      >
        <div className="text-center space-y-6">
          <BookOpen className="w-16 h-16 text-primary mx-auto" />
          <h1 className="text-5xl font-serif text-textPrimary dark:text-white tracking-tight">Eloq</h1>
          <p className="text-textSecondary text-lg font-light max-w-sm mx-auto leading-relaxed">
            Your personal speaking studio. Refine your voice, master your narrative.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8 bg-surface dark:bg-dark-surface p-10 rounded-[2.5rem] shadow-2xl shadow-primary/5">
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}
          {successMessage && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-600 dark:text-green-400 px-4 py-3 rounded-lg text-sm">
              {successMessage}
            </div>
          )}
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-semibold tracking-wide text-textSecondary uppercase mb-3">
                Email
              </label>
              <input
                type="email"
                className="w-full text-lg bg-transparent border-b-2 border-gray-200 dark:border-gray-800 focus:border-primary focus:outline-none transition-colors pb-3 text-textPrimary dark:text-white"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-semibold tracking-wide text-textSecondary uppercase mb-3">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="w-full text-lg bg-transparent border-b-2 border-gray-200 dark:border-gray-800 focus:border-primary focus:outline-none transition-colors pb-3 text-textPrimary dark:text-white pr-10"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-0 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
              {isSignup && (
                <p className="text-xs text-textSecondary mt-2">
                  Password must be at least 8 characters with 1 uppercase and 1 number
                </p>
              )}
            </div>
          </div>
          <button
            type="submit"
            className="w-full bg-textPrimary dark:bg-white text-white dark:text-textPrimary text-lg py-4 rounded-full font-medium hover:bg-primary dark:hover:bg-primary hover:text-white transition-all hover:scale-[1.02] shadow-xl hover:shadow-primary/25"
          >
            {isSignup ? 'Create Account' : 'Enter Studio'}
          </button>
          <div className="text-center">
            <button
              type="button"
              onClick={() => {
                setIsSignup(!isSignup);
                setError('');
                setSuccessMessage('');
              }}
              className="text-sm text-textSecondary hover:text-primary transition-colors"
            >
              {isSignup ? 'Already have an account? Login' : "Don't have an account? Sign up"}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
