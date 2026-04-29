import React from 'react';
import { motion } from 'motion/react';
import { cn } from '../../lib/utils';

interface BentoCardProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  whileHover?: boolean;
}

export const BentoCard: React.FC<BentoCardProps> = ({ 
  children, 
  className, 
  delay = 0,
  whileHover = false
}) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay }}
    whileHover={whileHover ? { scale: 1.01, y: -4 } : undefined}
    className={cn(
      "bg-surface-lowest rounded-2xl p-8 border border-slate-200 ambient-shadow transition-all", 
      className
    )}
  >
    {children}
  </motion.div>
);
