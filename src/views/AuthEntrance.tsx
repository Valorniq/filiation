import React, { useState } from 'react';
import { cn } from '../lib/utils';
import { motion } from 'motion/react';
import { useAuth } from '../contexts/AuthContext';
import { 
  LayoutGrid as HubIcon, 
  ShieldCheck as SecurityIcon, 
  UserCheck as UserCheckIcon, 
  Mail as MailIcon, 
  Smartphone as AppleIcon, 
  Github as GithubIcon, 
  Info as InfoIcon, 
  CheckCircle2,
  Chrome
} from 'lucide-react';
import { InputGroup } from '../components/ui/InputGroup';

export const AuthEntrance = () => {
  const { loginWithGoogle } = useAuth();
  const [isProcessing, setIsProcessing] = useState(false);
  const [mode, setMode] = useState<'login' | 'register'>('login');

  const handleGoogleLogin = async () => {
    if (isProcessing) return; // Basic Rate Limiting / Debounce
    setIsProcessing(true);
    try {
      await loginWithGoogle();
    } catch (error) {
      console.error(error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background-base flex items-center justify-center p-6 md:p-12">
      <main className="w-full max-w-7xl grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
        
        {/* Branding Column */}
        <div className="lg:col-span-5 space-y-12">
           <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-primary rounded-2xl flex items-center justify-center text-white ambient-shadow">
                 <HubIcon size={28} />
              </div>
              <h1 className="text-3xl font-black font-headline tracking-tighter text-primary">Filiation</h1>
           </div>

           <div className="space-y-6">
              <motion.h2 
                key={mode}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-6xl md:text-7xl font-black font-headline tracking-[-0.04em] leading-[0.9] text-stone-900"
              >
                {mode === 'login' ? (
                  <>Secure your family’s <br/> <span className="bg-gradient-to-br from-primary to-primary-container bg-clip-text text-transparent italic">digital sanctuary.</span></>
                ) : (
                  <>Establish your family’s <br/> <span className="bg-gradient-to-br from-secondary to-secondary-container bg-clip-text text-transparent italic">encrypted hub.</span></>
                )}
              </motion.h2>
              <p className="text-xl text-stone-500 font-medium max-w-lg leading-relaxed">
                {mode === 'login' 
                  ? "Connect, sync, and protect your home with an encrypted collective hub designed for the modern family."
                  : "Start your journey today. One click to secure your family's future with state-of-the-art encryption and shared visibility."
                }
              </p>
           </div>

           <div className="grid grid-cols-2 gap-6 pt-10">
              <FeatureMinimal icon={SecurityIcon} label="End-to-End Encryption" />
              <FeatureMinimal icon={UserCheckIcon} label="Shared Legacy Hub" />
           </div>
        </div>

        {/* Auth Form Column */}
        <section className="lg:col-span-7 bg-surface-low p-2 rounded-[3.5rem] ambient-shadow">
          <div className="bg-white rounded-[3rem] p-10 md:p-16 flex flex-col gap-12">
            
            <nav className="flex items-center gap-2 p-1.5 bg-surface-low rounded-full self-start">
               <button 
                onClick={() => setMode('login')}
                className={cn(
                  "px-10 py-3 rounded-full text-sm font-black transition-all",
                  mode === 'login' ? "bg-white text-primary ambient-shadow" : "text-stone-400 hover:bg-stone-100"
                )}
               >
                 Login
               </button>
               <button 
                onClick={() => setMode('register')}
                className={cn(
                  "px-10 py-3 rounded-full text-sm font-black transition-all",
                  mode === 'register' ? "bg-white text-primary ambient-shadow" : "text-stone-400 hover:bg-stone-100"
                )}
               >
                 Register
               </button>
            </nav>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-16">
               {/* Inputs */}
               <div className="space-y-8">
                  <div className="space-y-2">
                    <h3 className="text-2xl font-black font-headline tracking-tighter">
                      {mode === 'login' ? 'Access Hub' : 'Create Identity'}
                    </h3>
                    <p className="text-stone-400 text-sm font-medium">
                      {mode === 'login' ? 'Enter your sanctuary credentials.' : 'Initialize your presence in the collective.'}
                    </p>
                  </div>

                  <div className="space-y-4">
                    <button 
                      onClick={handleGoogleLogin}
                      disabled={isProcessing}
                      className={cn(
                        "w-full h-16 bg-white border-2 border-surface-low text-stone-700 font-bold rounded-2xl flex items-center justify-center gap-4 hover:bg-surface-low transition-all active:scale-95",
                        isProcessing && "opacity-50 cursor-not-allowed"
                      )}
                    >
                      <Chrome className="text-primary" />
                      {isProcessing ? 'Connecting...' : `Sign ${mode === 'login' ? 'In' : 'Up'} with Google`}
                    </button>
                    
                    <div className="p-4 bg-primary/5 rounded-xl border border-primary/10">
                       <p className="text-[10px] font-bold text-primary/60 text-center uppercase tracking-widest leading-relaxed">
                          Note: Email/Password registration must be enabled in the Firebase Console. Google is the default secure sync method.
                       </p>
                    </div>
                  </div>

                  <div className="relative py-4">
                    <div className="absolute inset-0 flex items-center">
                       <div className="w-full border-t border-surface-low" />
                    </div>
                    <div className="relative flex justify-center">
                       <span className="bg-white px-4 text-[10px] font-black uppercase tracking-[0.4em] text-stone-300">Other Methods</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-4 gap-4">
                    <SocialButton icon={MailIcon} />
                    <SocialButton icon={AppleIcon} />
                    <SocialButton icon={GithubIcon} />
                    <SocialButton icon={InfoIcon} />
                  </div>
               </div>

               {/* Onboarding Preview */}
               <div className="p-8 rounded-[2.5rem] bg-surface-low space-y-8">
                  <div className="space-y-2">
                    <h3 className="text-2xl font-black font-headline tracking-tighter text-stone-800">Onboarding</h3>
                    <p className="text-stone-400 text-sm font-medium">Syncing your presence.</p>
                  </div>

                  <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
                    <div className="space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-stone-400 ml-1">Join Family Code</label>
                        <div className="relative">
                            <input 
                                type="text" 
                                placeholder="F-294-88X" 
                                className="w-full h-14 bg-white border-none rounded-2xl px-6 font-mono font-bold tracking-widest text-primary focus:ring-2 focus:ring-primary/20 transition-all uppercase"
                            />
                            <div className="absolute right-4 top-1/2 -translate-y-1/2 text-secondary">
                                <CheckCircle2 size={20} className="text-secondary" />
                            </div>
                        </div>
                        <p className="text-[10px] text-stone-400 italic px-2">Enter the unique hex-code from your Family Head.</p>
                    </div>

                    <div className="p-6 bg-primary/5 rounded-2xl border border-primary/10 flex gap-4">
                       <InfoIcon className="text-primary shrink-0" size={20} />
                       <p className="text-[11px] font-medium leading-relaxed text-primary/70">
                          Joining a family code will automatically sync your shared calendar and logistics hub.
                       </p>
                    </div>
                  </form>
               </div>
            </div>

            <footer className="flex flex-col md:flex-row items-center justify-between border-t border-surface-low pt-8 gap-4">
               <p className="text-[11px] font-bold text-stone-400 uppercase tracking-tight">© 2026 Filiation Systems. Locally Encrypted.</p>
               <div className="flex gap-8">
                  <button className="text-[11px] font-bold text-stone-400 uppercase hover:text-primary transition-colors">Privacy Shield</button>
                  <button className="text-[11px] font-bold text-stone-400 uppercase hover:text-primary transition-colors">Global Terms</button>
               </div>
            </footer>
          </div>
        </section>
      </main>
    </div>
  );
};

const FeatureMinimal = ({ icon: Icon, label }: any) => (
  <div className="flex items-center gap-4 group">
    <div className="w-12 h-12 rounded-2xl bg-white flex items-center justify-center ambient-shadow border border-slate-100 group-hover:scale-110 group-hover:bg-primary group-hover:text-white transition-all duration-300">
      <Icon size={20} />
    </div>
    <span className="text-sm font-black font-headline tracking-tight text-slate-800">{label}</span>
  </div>
);

const SocialButton = ({ icon: Icon }: any) => (
  <button className="h-14 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-800 hover:bg-slate-100 transition-all shadow-sm">
    <Icon size={20} />
  </button>
);
