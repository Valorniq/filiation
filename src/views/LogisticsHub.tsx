import React from 'react';
import { motion } from 'motion/react';
import { School, Shield, Car, Bus, ShoppingBasket, PlusCircle, CheckCircle2, Box } from 'lucide-react';
import { cn } from '../lib/utils';
import { BentoCard } from '../components/ui/BentoCard';

export const LogisticsHub = () => {
  return (
    <div className="space-y-12">
      <header>
        <h1 className="text-5xl font-black font-headline tracking-tighter mb-2">Logistics Hub</h1>
        <p className="text-xl text-stone-500 font-medium">Centralized command for school, health, and family operations.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        
        {/* School Alerts Timeline - Wide Card */}
        <BentoCard className="md:col-span-8 space-y-10">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-primary/10 text-primary rounded-2xl">
                <School size={24} />
              </div>
              <h2 className="text-2xl font-black font-headline tracking-tight">School Operations</h2>
            </div>
            <span className="px-4 py-1.5 bg-surface-low text-stone-500 rounded-full text-[10px] font-black uppercase tracking-[0.2em]">2 New Alerts</span>
          </div>

          <div className="space-y-8 relative before:absolute before:left-[11px] before:top-2 before:h-[calc(100%-16px)] before:w-0.5 before:bg-surface-low">
            <TimelineItem 
              status="Infinite Campus • Now"
              title="Quarter 3 Progress Report Available"
              desc="Grade updates for Leo and Maya are now visible in the portal. Please review and sign off."
              color="bg-primary"
              actions={['Sign Portal', 'Details']}
            />
            <TimelineItem 
              status="Schoology • 2h ago"
              title="Missing Assignment: AP History"
              desc="Maya has an overdue project: 'Industrial Revolution Analysis'. Due date was yesterday."
              color="bg-tertiary"
            />
            <TimelineItem 
              status="Calendar • Tomorrow"
              title="Early Dismissal: Faculty Planning"
              desc="Both schools dismissing at 12:30 PM. After-school activities are cancelled."
              color="bg-secondary"
            />
          </div>
        </BentoCard>

        {/* Health Hub Column */}
        <div className="md:col-span-4 space-y-8">
           <BentoCard className="space-y-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-tertiary/10 text-tertiary rounded-2xl">
                  <Shield size={22} />
                </div>
                <h3 className="text-xl font-black font-headline tracking-tight">Health Status</h3>
              </div>
              
              <div className="space-y-4">
                <div className="p-5 rounded-2xl bg-surface-low">
                  <div className="flex items-start gap-4">
                    <div className="p-2 bg-white text-tertiary rounded-xl ambient-shadow">
                      <Box size={16} />
                    </div>
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-widest text-stone-400 mb-1">Immunization Update</p>
                      <p className="text-sm font-bold leading-snug">Leo: Tdap booster due by Sep 1st</p>
                      <button className="text-[10px] font-black text-primary uppercase mt-2 hover:underline">Schedule Clinic</button>
                    </div>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-secondary/5 border border-secondary/10">
                  <div className="flex items-start gap-4">
                    <div className="p-2 bg-secondary text-white rounded-xl">
                      <CheckCircle2 size={16} />
                    </div>
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-widest text-secondary/60 mb-1">Sports Physicals</p>
                      <p className="text-sm font-bold text-secondary leading-snug">Maya: Approved for Soccer Season</p>
                      <p className="text-[9px] font-bold text-secondary/40 mt-1 uppercase tracking-tighter">Valid thru Jun 2025</p>
                    </div>
                  </div>
                </div>
              </div>
           </BentoCard>

           <BentoCard className="bg-primary text-white relative overflow-hidden group">
              <div className="relative z-10">
                <h3 className="text-2xl font-black font-headline mb-2">Security Hub</h3>
                <p className="text-primary-foreground/60 text-xs font-medium leading-relaxed mb-8">Manage emergency contacts and child location permissions.</p>
                <button className="w-full h-14 bg-white text-primary font-black rounded-2xl transition-all active:scale-95 shadow-xl">
                  Audit Permissions
                </button>
              </div>
              <Shield className="absolute -right-8 -bottom-8 opacity-10 group-hover:scale-110 transition-transform" size={160} />
           </BentoCard>
        </div>

        {/* Daily Logistics Section */}
        <div className="md:col-span-12 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h3 className="text-3xl font-black font-headline tracking-tighter">Daily Logistics</h3>
              <p className="text-stone-400 font-medium">Transport and after-school coverage for today.</p>
            </div>
            <div className="flex -space-x-3">
               {[1,2,3].map(i => (
                 <div key={i} className="w-12 h-12 rounded-full border-4 border-background-base overflow-hidden bg-surface-low">
                   <img 
                    src={`https://i.pravatar.cc/100?u=${i + 10}`} 
                    alt="Family" 
                    className="w-full h-full object-cover"
                   />
                 </div>
               ))}
               <div className="w-12 h-12 rounded-full border-4 border-background-base bg-surface-low flex items-center justify-center text-[10px] font-black text-stone-400">+1</div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <LogisticCard label="Leo • 3:30 PM" icon={Bus} title="Bus Route #14" status="On Schedule" statusColor="text-secondary" />
            <LogisticCard label="Maya • 5:15 PM" icon={Car} title="Dad Pick-up" status="Soccer Field 3" />
            <LogisticCard label="Groceries • Pending" icon={ShoppingBasket} title="Target Drive-up" status="Expires in 2h" statusColor="text-tertiary" />
            <motion.div 
               whileHover={{ scale: 1.02 }}
               whileTap={{ scale: 0.98 }}
               className="bg-primary rounded-[2.5rem] flex flex-col items-center justify-center text-center p-8 text-white cursor-pointer ambient-shadow"
            >
              <PlusCircle size={32} className="mb-2" />
              <span className="text-[11px] font-black uppercase tracking-widest">New Logistic Item</span>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

const TimelineItem = ({ status, title, desc, color, actions }: any) => (
  <div className="flex gap-6 relative">
    <div className={cn("w-6 h-6 rounded-full border-4 border-white ambient-shadow z-10 shrink-0", color)} />
    <div className="flex-1 pb-6">
      <p className={cn("text-[10px] font-black uppercase tracking-widest mb-1", color.replace('bg-', 'text-'))}>{status}</p>
      <h4 className="text-lg font-black font-headline tracking-tight mb-1">{title}</h4>
      <p className="text-sm font-medium text-stone-500 leading-relaxed max-w-2xl">{desc}</p>
      {actions && (
        <div className="flex gap-3 mt-6">
          {actions.map((act: string, i: number) => (
            <button 
              key={act} 
              className={cn(
                "h-10 px-6 rounded-xl text-xs font-black transition-all",
                i === 0 ? "bg-primary text-white shadow-lg" : "bg-surface-low text-stone-500"
              )}
            >
              {act}
            </button>
          ))}
        </div>
      )}
    </div>
  </div>
);

const LogisticCard = ({ label, icon: Icon, title, status, statusColor }: any) => (
  <BentoCard className="p-6 bg-surface-low/50 border-0 flex flex-col justify-between">
    <span className="text-[10px] font-black uppercase tracking-widest text-stone-400">{label}</span>
    <div className="my-4 flex items-center gap-3">
      <div className="p-2.5 bg-white rounded-xl text-primary ambient-shadow">
        <Icon size={20} />
      </div>
      <span className="text-base font-black font-headline tracking-tight">{title}</span>
    </div>
    <p className={cn("text-xs font-bold", statusColor || "text-stone-400")}>{status}</p>
  </BentoCard>
);
