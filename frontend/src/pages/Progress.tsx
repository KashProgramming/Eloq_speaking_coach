import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Flame, TrendingUp, Award, Calendar, BarChart3 } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { api } from '../api';

type Period = 'week' | 'month' | 'all';

export function Progress() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');
  const [period, setPeriod] = useState<Period>('week');

  useEffect(() => {
    loadProgress();
  }, [period]);

  const loadProgress = async () => {
    try {
      const res = await api.practice.getProgress(period);
      setData(res);
      setError('');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to load progress data';
      setError(errorMessage);
    }
  };

  if (error) {
    return (
      <div className="max-w-4xl mx-auto space-y-8 py-8">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-6 py-4 rounded-lg">
          {error}
        </div>
      </div>
    );
  }

  if (!data) return <div className="text-center mt-20 font-serif text-xl animate-pulse text-textSecondary">Loading insights...</div>;

  // Scale bars to max of 10 for better visibility
  const maxFluency = Math.max(...data.weekly_trend.map((d: any) => d.avg_fluency), 10);

  return (
    <div className="max-w-4xl mx-auto space-y-16 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-end justify-between"
      >
        <div className="space-y-4">
          <h2 className="text-4xl font-serif text-textPrimary dark:text-white">Your Journey</h2>
          <p className="text-textSecondary text-lg font-light tracking-wide">
            Level: <span className="font-semibold text-primary">{data.level}</span>
          </p>
        </div>
        
        {/* Period Selector */}
        <div className="flex gap-2 bg-surface dark:bg-dark-surface rounded-xl p-1 shadow-sm">
          {(['week', 'month', 'all'] as Period[]).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                period === p
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-textSecondary hover:text-textPrimary dark:hover:text-white'
              }`}
            >
              {p === 'week' ? 'Week' : p === 'month' ? 'Month' : 'All Time'}
            </button>
          ))}
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <motion.div
          whileHover={{ scale: 1.02 }}
          className="col-span-1 bg-surface dark:bg-dark-surface p-8 rounded-3xl space-y-6 group border border-transparent hover:border-accent/20 transition-all shadow-sm"
        >
          <div className="w-12 h-12 bg-accent/10 rounded-full flex items-center justify-center text-accent group-hover:scale-110 transition-transform">
            <Flame className="w-6 h-6" />
          </div>
          <div>
            <p className="text-5xl font-light text-textPrimary dark:text-white mb-2">{data.streak}</p>
            <p className="text-sm font-semibold tracking-wide text-textSecondary uppercase">Day Streak</p>
          </div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="col-span-1 bg-surface dark:bg-dark-surface p-8 rounded-3xl space-y-6 group border border-transparent hover:border-primary/20 transition-all shadow-sm"
        >
          <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <p className="text-5xl font-light text-textPrimary dark:text-white mb-2">{data.total_sessions}</p>
            <p className="text-sm font-semibold tracking-wide text-textSecondary uppercase">Sessions Total</p>
          </div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="col-span-1 bg-surface dark:bg-dark-surface p-8 rounded-3xl space-y-6 group border border-transparent transition-all shadow-sm relative overflow-hidden"
        >
          <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center text-textSecondary group-hover:scale-110 transition-transform">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <p className="text-5xl font-light text-textPrimary dark:text-white mb-2">
              {data.prompts_completed}/{data.prompts_remaining_in_level + data.prompts_completed}
            </p>
            <p className="text-sm font-semibold tracking-wide text-textSecondary uppercase">Prompts Done</p>
            <div className="absolute bottom-0 left-0 h-1 bg-primary w-full origin-left" style={{ transform: `scaleX(${data.prompts_completed / (data.prompts_remaining_in_level + data.prompts_completed)})` }} />
          </div>
        </motion.div>
      </div>

      {/* Trend Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-surface dark:bg-dark-surface p-8 rounded-3xl shadow-sm space-y-6"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-primary" />
          </div>
          <h3 className="text-xl font-serif text-textPrimary dark:text-white">
            Fluency Trend
          </h3>
        </div>
        
        <div className="space-y-2">
          {data.weekly_trend.length === 0 ? (
            <p className="text-center text-textSecondary py-8">No data available for this period</p>
          ) : (
            <div className="flex items-end justify-between gap-2 h-48">
              {data.weekly_trend.map((day: any, idx: number) => {
                const date = new Date(day.date);
                const barHeight = day.avg_fluency > 0 ? (day.avg_fluency / maxFluency) * 100 : 0;
                const hasSession = day.session_count > 0;
                
                return (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-2 group">
                    <div className="relative w-full flex flex-col justify-end h-40">
                      {hasSession ? (
                        <motion.div
                          initial={{ height: 0 }}
                          animate={{ height: `${barHeight}%` }}
                          transition={{ delay: idx * 0.05, duration: 0.5 }}
                          className="w-full bg-gradient-to-t from-primary to-primary/60 rounded-t-lg relative group-hover:from-primary/80 group-hover:to-primary/40 transition-colors"
                        >
                          <div className="absolute -top-8 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs px-2 py-1 rounded whitespace-nowrap">
                            {day.avg_fluency.toFixed(1)} • {day.session_count} session{day.session_count !== 1 ? 's' : ''}
                          </div>
                        </motion.div>
                      ) : (
                        <div className="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded" />
                      )}
                    </div>
                    <span className="text-xs text-textSecondary font-medium">
                      {date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
        
        <div className="flex items-center justify-center gap-6 pt-4 border-t border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-primary rounded" />
            <span className="text-sm text-textSecondary">Avg Fluency Score</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-1 bg-gray-200 dark:bg-gray-700 rounded" />
            <span className="text-sm text-textSecondary">No Sessions</span>
          </div>
        </div>
      </motion.div>

      <div className="space-y-8">
        <h3 className="text-xl font-serif text-textPrimary dark:text-white flex items-center gap-3">
          <Calendar className="w-5 h-5 text-primary" /> Key Improvements
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {Object.entries(data.improvements).map(([key, val]: [string, any], idx) => (
            <Card key={idx} className="bg-surface dark:bg-dark-surface border-none shadow-sm p-6 rounded-2xl">
              <h4 className="text-sm font-semibold tracking-wide text-textSecondary uppercase mb-3 capitalize">{key.replace('_', ' ')}</h4>
              <p className="text-lg text-textPrimary dark:text-gray-200">{val}</p>
            </Card>
          ))}
        </div>
      </div>
      
      <div className="pt-8 border-t border-gray-100 dark:border-gray-800">
         <p className="text-sm text-textSecondary text-center italic">"Your baseline: {data.baseline}"</p>
      </div>
    </div>
  );
}
