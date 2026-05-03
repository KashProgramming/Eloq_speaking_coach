import { motion } from 'framer-motion';

export function AudioVisualizer({ isRecording }: { isRecording: boolean }) {
  return (
    <div className="flex items-center justify-center space-x-1 h-12 w-full">
      {[...Array(20)].map((_, i) => (
        <motion.div
          key={i}
          className="w-1.5 bg-primary rounded-full"
          initial={{ height: 4 }}
          animate={{ height: isRecording ? [4, Math.random() * 24 + 12, 4] : 4 }}
          transition={{
            repeat: Infinity,
            duration: 0.5 + Math.random() * 0.5,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}
