import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Layout } from './components/Layout';
import { cn } from './lib/utils';
import { ArrowRight, Wallet, School, Sun, Cloud, Bell, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Views
import { FinancialHub } from './views/FinancialHub';
import { LogisticsHub } from './views/LogisticsHub';
import { CalendarHub } from './views/CalendarHub';
import { SyncHub } from './views/SyncHub';
import { AuthEntrance } from './views/AuthEntrance';
import { ProfileSettings } from './views/ProfileSettings';

// Common Bento Component
const BentoCard = ({ children, className, delay = 0 }: { children: React.ReactNode, className?: string, delay?: number }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay }}
    className={cn("bg-surface-lowest rounded-2xl p-8 ambient-shadow border-0 transition-transform active:scale-[0.98]", className)}
  >
    {children}
  </motion.div>
);

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-base">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  return <Layout>{children}</Layout>;
};

const PublicRoute = ({ children }: { children: React.ReactNode }) => {
  const { user } = useAuth();
  if (user) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
};

const Home = () => {
  const { profile } = useAuth();
  return (
    <div className="space-y-12">
      <header>
        <motion.h1 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="text-5xl md:text-6xl font-black font-headline tracking-tighter mb-2"
        >
          Good morning, {profile?.displayName?.split(' ')[0] || 'Family'}.
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="text-xl text-stone-500 font-medium"
        >
          Everything is in sync across the sanctuary.
        </motion.p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Featured Hero Card */}
        <BentoCard className="md:col-span-3 bg-gradient-to-br from-primary to-primary-container text-white relative overflow-hidden h-[340px]">
          <div className="relative z-10 flex flex-col justify-between h-full">
            <div>
              <span className="inline-block px-3 py-1 bg-white/20 rounded-full text-[10px] font-black uppercase tracking-[0.2em] mb-6">Active Focus</span>
              <h2 className="text-4xl md:text-5xl font-black font-headline leading-[1.1] max-w-md">
                School Deadline & <br/> Health Checkup today
              </h2>
            </div>
            <div className="flex gap-4">
              <button className="h-14 px-8 bg-white text-primary font-black rounded-xl hover:scale-105 active:scale-95 transition-all shadow-xl">
                View Schedule
              </button>
              <button className="h-14 px-8 bg-white/20 text-white font-black rounded-xl hover:bg-white/30 transition-all">
                Dismiss
              </button>
            </div>
          </div>
          <div className="absolute -right-20 -bottom-20 w-80 h-80 bg-white/10 rounded-[4rem] rotate-12 blur-2xl" />
        </BentoCard>

        {/* Finance Mini Card */}
        <BentoCard className="flex flex-col justify-between" delay={0.1}>
          <div>
            <div className="flex justify-between items-start mb-6">
              <div className="p-3 bg-tertiary/10 text-tertiary rounded-xl">
                <Wallet size={24} />
              </div>
              <span className="px-3 py-1 bg-secondary/10 text-secondary text-[10px] font-black uppercase tracking-widest rounded-full">Live</span>
            </div>
            <h3 className="text-xl font-bold font-headline mb-1">Burn Rate</h3>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-black text-stone-900">$142</span>
              <span className="text-sm font-medium text-stone-400">/day</span>
            </div>
          </div>
          <div className="pt-6 mt-6 border-t border-surface-low flex justify-between items-center">
            <span className="text-xs font-bold text-stone-400 uppercase tracking-widest">P2P Request</span>
            <span className="text-primary font-black">+$45.00</span>
          </div>
        </BentoCard>

        {/* Logistics & Alerts */}
        <BentoCard className="md:col-span-2" delay={0.2}>
          <div className="flex items-center gap-3 mb-8">
             <div className="p-2 text-primary">
                <School size={20} />
             </div>
             <h3 className="text-xl font-black font-headline tracking-tight">Logistics & Alerts</h3>
          </div>
          
          <div className="space-y-4">
            <AlertItem 
              icon={Bell} 
              title="Schoology update" 
              desc="Math 101: New assignment posted" 
              color="text-primary" 
              bg="bg-primary/10"
            />
            <AlertItem 
              icon={AlertTriangle} 
              title="Infinite Campus alert" 
              desc="Missing attendance: Period 4" 
              color="text-tertiary" 
              bg="bg-tertiary/10"
            />
          </div>
        </BentoCard>

        {/* Dynamic Weather Card */}
        <BentoCard className="flex flex-col items-center justify-center text-center py-10" delay={0.3}>
          <Sun size={48} className="text-amber-500 mb-4" />
          <h4 className="text-5xl font-black font-headline mb-2">72°</h4>
          <p className="text-sm font-bold text-stone-400 max-w-[120px] leading-snug tracking-tighter">Perfect day for a family walk</p>
        </BentoCard>

        {/* Sync Status Card */}
        <BentoCard className="flex flex-col justify-between" delay={0.4}>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-2 h-2 rounded-full bg-secondary pulse-ripple" />
            <h3 className="text-xs font-black uppercase tracking-widest text-stone-500">Cloud Status</h3>
          </div>
          
          <div className="flex flex-col items-center py-4">
            <Cloud className="text-secondary mb-2" size={40} />
            <p className="text-xs font-bold text-stone-400 uppercase tracking-[0.2em]">Syncing: 100%</p>
          </div>
          
          <button className="w-full h-12 bg-surface-low hover:bg-surface-variant transition-colors text-[10px] font-black uppercase tracking-widest text-stone-500 rounded-xl">
            Manage Storage
          </button>
        </BentoCard>
      </div>
    </div>
  );
};

const AlertItem = ({ icon: Icon, title, desc, color, bg }: { icon: any, title: string, desc: string, color: string, bg: string }) => (
  <div className="flex items-center gap-5 p-5 rounded-2xl bg-surface-low hover:bg-surface-variant transition-all cursor-pointer group">
    <div className={cn("w-12 h-12 rounded-full flex items-center justify-center", bg, color)}>
      <Icon size={20} />
    </div>
    <div className="flex-1">
      <h4 className="text-sm font-black tracking-tight mb-0.5">{title}</h4>
      <p className="text-xs font-medium text-stone-400">{desc}</p>
    </div>
    <ArrowRight size={16} className="text-stone-300 group-hover:translate-x-1 group-hover:text-primary transition-all" />
  </div>
);

const AnimatedRoutes = () => {
    return (
        <AnimatePresence mode="wait">
            <Routes>
                <Route path="/auth" element={<PublicRoute><AuthEntrance /></PublicRoute>} />
                <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
                <Route path="/finance" element={<ProtectedRoute><FinancialHub /></ProtectedRoute>} />
                <Route path="/logistics" element={<ProtectedRoute><LogisticsHub /></ProtectedRoute>} />
                <Route path="/calendar" element={<ProtectedRoute><CalendarHub /></ProtectedRoute>} />
                <Route path="/sync" element={<ProtectedRoute><SyncHub /></ProtectedRoute>} />
                <Route path="/settings" element={<ProtectedRoute><ProfileSettings /></ProtectedRoute>} />
                <Route path="*" element={<Navigate to="/" />} />
            </Routes>
        </AnimatePresence>
    )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AnimatedRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
