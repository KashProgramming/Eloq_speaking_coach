import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, useAnimation, useMotionValue } from 'framer-motion';
import { Mic, Sparkles, TrendingUp, Users, ArrowRight, Volume2, Radio } from 'lucide-react';

export function Landing() {
  const navigate = useNavigate();
  const [hoveredFeature, setHoveredFeature] = useState<number | null>(null);
  const controls = useAnimation();
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  useEffect(() => {
    controls.start({
      opacity: [0.4, 1, 0.4],
      scale: [1, 1.05, 1],
      transition: {
        duration: 3,
        repeat: Infinity,
        ease: "easeInOut"
      }
    });
  }, [controls]);

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    mouseX.set(e.clientX - rect.left);
    mouseY.set(e.clientY - rect.top);
  };

  const features = [
    {
      icon: Mic,
      title: "AI-Powered Analysis",
      description: "Get instant feedback on fluency, vocabulary, grammar, and structure with advanced speech recognition."
    },
    {
      icon: TrendingUp,
      title: "Track Your Progress",
      description: "Watch your speaking skills improve with detailed metrics, streaks, and weekly performance trends."
    },
    {
      icon: Users,
      title: "Roleplay Scenarios",
      description: "Practice real-world conversations with AI in interviews, debates, and pitch scenarios."
    },
    {
      icon: Sparkles,
      title: "Adaptive Learning",
      description: "Prompts that match your skill level and automatically advance as you improve."
    }
  ];

  // Waveform bars animation
  const WaveformBar = ({ delay, height }: { delay: number; height: number }) => (
    <motion.div
      className="w-1 bg-primary rounded-full"
      initial={{ height: height }}
      animate={{
        height: [height, height * 2, height * 0.5, height * 1.5, height],
        opacity: [0.3, 1, 0.5, 0.8, 0.3]
      }}
      transition={{
        duration: 2,
        delay: delay,
        repeat: Infinity,
        ease: "easeInOut"
      }}
    />
  );

  // Floating audio particles
  const AudioParticle = ({ delay, x, y }: { delay: number; x: number; y: number }) => (
    <motion.div
      className="absolute w-2 h-2 bg-primary/30 rounded-full"
      style={{ left: `${x}%`, top: `${y}%` }}
      animate={{
        y: [0, -30, 0],
        opacity: [0, 1, 0],
        scale: [0, 1.5, 0]
      }}
      transition={{
        duration: 3,
        delay: delay,
        repeat: Infinity,
        ease: "easeOut"
      }}
    />
  );

  return (
    <div className="min-h-screen bg-background dark:bg-dark-background overflow-hidden">
      {/* Hero Section */}
      <div className="relative min-h-screen flex items-center justify-center px-6" onMouseMove={handleMouseMove}>
        {/* Animated background particles */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(20)].map((_, i) => (
            <AudioParticle
              key={i}
              delay={i * 0.2}
              x={Math.random() * 100}
              y={Math.random() * 100}
            />
          ))}
        </div>

        {/* Glassmorphic card */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: "easeOut" }}
          className="relative z-10 max-w-6xl w-full"
        >
          {/* Main content card with glass effect */}
          <div className="relative bg-surface/60 dark:bg-dark-surface/60 backdrop-blur-xl rounded-[3rem] p-12 md:p-16 shadow-2xl border border-primary/10">
            {/* Animated glow effect */}
            <motion.div
              className="absolute inset-0 rounded-[3rem] bg-gradient-to-br from-primary/5 via-transparent to-accent/5 pointer-events-none"
              animate={controls}
            />

            <div className="relative z-10 text-center space-y-8">
              {/* Logo and brand */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                className="inline-flex items-center justify-center space-x-3"
              >
                <div className="relative">
                  <Radio className="w-16 h-16 text-primary" />
                  <motion.div
                    className="absolute inset-0"
                    animate={{
                      scale: [1, 1.3, 1],
                      opacity: [0.5, 0, 0.5]
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeOut"
                    }}
                  >
                    <Radio className="w-16 h-16 text-primary" />
                  </motion.div>
                </div>
              </motion.div>

              <motion.h1
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3, duration: 0.8 }}
                className="text-6xl md:text-7xl lg:text-8xl font-serif text-textPrimary dark:text-white tracking-tight"
              >
                Eloq
              </motion.h1>

              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4, duration: 0.8 }}
                className="text-xl md:text-2xl text-textSecondary dark:text-gray-300 font-light max-w-3xl mx-auto leading-relaxed"
              >
                Transform your speaking skills through AI-driven practice, real-time feedback, and immersive roleplay scenarios.
              </motion.p>

              {/* Waveform visualization */}
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.5, duration: 0.8 }}
                className="flex items-end justify-center space-x-1.5 h-24 py-8"
              >
                {[...Array(40)].map((_, i) => (
                  <WaveformBar
                    key={i}
                    delay={i * 0.05}
                    height={Math.random() * 30 + 20}
                  />
                ))}
              </motion.div>

              {/* CTA Buttons */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6, duration: 0.8 }}
                className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
              >
                <motion.button
                  onClick={() => navigate('/login')}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="group relative px-8 py-4 bg-textPrimary dark:bg-white text-white dark:text-textPrimary rounded-full font-medium text-lg shadow-xl hover:shadow-primary/25 transition-all overflow-hidden"
                >
                  <span className="relative z-10 flex items-center space-x-2">
                    <span>Start Speaking</span>
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </span>
                  <motion.div
                    className="absolute inset-0 bg-primary"
                    initial={{ x: "-100%" }}
                    whileHover={{ x: 0 }}
                    transition={{ duration: 0.3 }}
                  />
                </motion.button>

                <motion.button
                  onClick={() => {
                    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
                  }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-8 py-4 bg-transparent border-2 border-textPrimary dark:border-white text-textPrimary dark:text-white rounded-full font-medium text-lg hover:bg-textPrimary/5 dark:hover:bg-white/5 transition-all"
                >
                  Learn More
                </motion.button>
              </motion.div>

              {/* Stats */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8, duration: 0.8 }}
                className="flex flex-wrap items-center justify-center gap-8 pt-8 text-textSecondary"
              >
                <div className="flex items-center space-x-2">
                  <Volume2 className="w-5 h-5 text-primary" />
                  <span className="text-sm font-medium">AI-Powered Feedback</span>
                </div>
                <div className="flex items-center space-x-2">
                  <TrendingUp className="w-5 h-5 text-primary" />
                  <span className="text-sm font-medium">Track Progress</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-5 h-5 text-primary" />
                  <span className="text-sm font-medium">Adaptive Learning</span>
                </div>
              </motion.div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Features Section */}
      <div id="features" className="relative py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-serif text-textPrimary dark:text-white mb-4">
              Everything you need to master speaking
            </h2>
            <p className="text-lg text-textSecondary dark:text-gray-300 max-w-2xl mx-auto">
              From daily practice to immersive roleplay, Eloq provides comprehensive tools to improve your communication skills.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.6 }}
                onHoverStart={() => setHoveredFeature(index)}
                onHoverEnd={() => setHoveredFeature(null)}
                className="relative group"
              >
                <div className="relative bg-surface/80 dark:bg-dark-surface/80 backdrop-blur-sm rounded-3xl p-8 border border-primary/10 hover:border-primary/30 transition-all duration-300 h-full">
                  {/* Hover glow effect */}
                  <motion.div
                    className="absolute inset-0 rounded-3xl bg-gradient-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    animate={hoveredFeature === index ? {
                      scale: [1, 1.02, 1],
                      transition: { duration: 2, repeat: Infinity }
                    } : {}}
                  />

                  <div className="relative z-10">
                    <motion.div
                      animate={hoveredFeature === index ? {
                        rotate: [0, 5, -5, 0],
                        transition: { duration: 0.5 }
                      } : {}}
                      className="inline-flex items-center justify-center w-14 h-14 bg-primary/10 rounded-2xl mb-6 group-hover:bg-primary/20 transition-colors"
                    >
                      <feature.icon className="w-7 h-7 text-primary" />
                    </motion.div>

                    <h3 className="text-2xl font-semibold text-textPrimary dark:text-white mb-3">
                      {feature.title}
                    </h3>
                    <p className="text-textSecondary dark:text-gray-300 leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="relative py-24 px-6">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="max-w-4xl mx-auto text-center"
        >
          <div className="relative bg-gradient-to-br from-primary/10 via-surface/80 to-accent/10 dark:from-primary/20 dark:via-dark-surface/80 dark:to-accent/20 backdrop-blur-xl rounded-[3rem] p-12 md:p-16 border border-primary/20">
            <h2 className="text-4xl md:text-5xl font-serif text-textPrimary dark:text-white mb-6">
              Ready to transform your speaking?
            </h2>
            <p className="text-xl text-textSecondary dark:text-gray-300 mb-8 max-w-2xl mx-auto">
              Join Eloq today and start your journey to confident, fluent communication.
            </p>
            <motion.button
              onClick={() => navigate('/login')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="group relative px-10 py-5 bg-textPrimary dark:bg-white text-white dark:text-textPrimary rounded-full font-medium text-xl shadow-2xl hover:shadow-primary/30 transition-all overflow-hidden"
            >
              <span className="relative z-10 flex items-center space-x-2">
                <span>Get Started</span>
                <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
              </span>
              <motion.div
                className="absolute inset-0 bg-primary"
                initial={{ x: "-100%" }}
                whileHover={{ x: 0 }}
                transition={{ duration: 0.3 }}
              />
            </motion.button>
          </div>
        </motion.div>
      </div>

      {/* Footer */}
      <div className="relative py-12 px-6 border-t border-primary/10">
        <div className="max-w-7xl mx-auto text-center text-textSecondary text-sm">
          <p>© 2026 Eloq. Your personal speaking studio.</p>
        </div>
      </div>
    </div>
  );
}
