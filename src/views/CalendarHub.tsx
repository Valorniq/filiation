import React from 'react';
import { cn } from '../lib/utils';
import { motion } from 'motion/react';
import { Calendar as CalendarIcon, Filter, Layers, MoreHorizontal, CheckCircle2, Clock } from 'lucide-react';

const BentoCard = ({ children, className, delay = 0 }: { children: React.ReactNode, className?: string, delay?: number }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay }}
    className={cn("bg-surface-lowest rounded-2xl p-8 ambient-shadow border-0", className)}
  >
    {children}
  </motion.div>
);

export const CalendarHub = () => {
  const days = Array.from({ length: 31 }, (_, i) => i + 1);
  const startDay = 2; // Offset for Oct 2024 (starts on Tues)

  return (
    <div className="space-y-12">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-8">
        <div>
          <h1 className="text-5xl font-black font-headline tracking-tighter mb-2">October 2024</h1>
          <p className="text-xl text-stone-500 font-medium">3 events scheduled for today</p>
        </div>
        
        <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-none">
          <FilterChip label="All Members" color="bg-primary" active />
          <FilterChip label="Sarah" color="bg-amber-400" />
          <FilterChip label="David" color="bg-emerald-400" />
          <FilterChip label="Leo" color="bg-rose-400" />
          <button className="p-3 bg-surface-low text-stone-500 rounded-full hover:bg-white transition-all">
            <Filter size={18} />
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        {/* Calendar Grid Section */}
        <div className="lg:col-span-12 space-y-8">
           <div className="grid grid-cols-7 gap-4">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                <div key={day} className="text-center text-[10px] font-black uppercase tracking-[0.2em] text-stone-400 pb-4">
                  {day}
                </div>
              ))}
              
              {/* Empty padding */}
              {Array.from({ length: startDay }).map((_, i) => (
                <div key={`empty-${i}`} className="aspect-square bg-surface-low/30 rounded-2xl" />
              ))}

              {days.map(day => {
                const isToday = day === 3;
                return (
                  <div 
                    key={day} 
                    className={cn(
                      "aspect-square p-4 rounded-2xl transition-all duration-300 group cursor-pointer border border-transparent",
                      isToday ? "bg-primary text-white ambient-shadow scale-105 z-10" : "bg-surface-lowest border-surface-low hover:ambient-shadow hover:scale-102 hover:border-primary/20",
                      day > 0 && "relative"
                    )}
                  >
                    <span className={cn("text-lg font-black font-headline", isToday ? "text-white" : "text-stone-900")}>{day}</span>
                    
                    {/* Event indicators */}
                    <div className="mt-3 flex flex-wrap gap-1">
                      {day % 4 === 0 && <div className={cn("w-1.5 h-1.5 rounded-full", isToday ? "bg-white" : "bg-primary")} />}
                      {day % 7 === 0 && <div className={cn("w-1.5 h-1.5 rounded-full", isToday ? "bg-white/60" : "bg-secondary")} />}
                    </div>

                    {/* Specific event labels for desktop */}
                    {day === 5 && (
                      <div className="hidden xl:block mt-2">
                        <div className="text-[9px] bg-secondary/10 text-secondary font-black px-2 py-1 rounded-lg truncate">Soccer Practice</div>
                      </div>
                    )}
                  </div>
                );
              })}
           </div>
        </div>

        {/* Today's Focus Detail Section */}
        <div className="lg:col-span-12 space-y-8">
          <div className="flex justify-between items-end">
            <h3 className="text-3xl font-black font-headline tracking-tighter">Today's Focus</h3>
            <button className="text-primary font-bold text-sm hover:underline">View All</button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
            {/* Primary Event Hero */}
            <BentoCard className="md:col-span-8 bg-primary text-white relative overflow-hidden group">
               <div className="relative z-10">
                  <span className="inline-block px-3 py-1 bg-white/20 rounded-full text-[10px] font-black uppercase tracking-widest mb-6">Urgent</span>
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-4xl font-black font-headline tracking-tight mb-3">School Fundraising Gala</h4>
                      <p className="text-primary-foreground/70 font-medium max-w-lg leading-relaxed text-lg">
                        The annual primary school event starts at 6:30 PM. Everyone needs to be dressed and ready by 6:00 PM.
                      </p>
                    </div>
                    <button className="p-3 bg-white/20 rounded-full hover:bg-white/30">
                      <MoreHorizontal size={20} />
                    </button>
                  </div>

                  <div className="mt-12 flex items-center gap-6">
                    <div className="flex -space-x-2">
                      {[1,2,3,4].map(i => (
                        <img 
                          key={i}
                          src={`https://i.pravatar.cc/100?u=${i + 20}`} 
                          alt="Face" 
                          className="w-10 h-10 rounded-full border-2 border-primary ambient-shadow"
                        />
                      ))}
                    </div>
                    <span className="text-sm font-bold opacity-80 uppercase tracking-tighter">Whole Family Attending</span>
                  </div>
               </div>
               <div className="absolute -right-20 -top-20 w-80 h-80 bg-white/10 rounded-full blur-[100px] pointer-events-none" />
            </BentoCard>

            {/* Satellite Tasks */}
            <div className="md:col-span-4 flex flex-col gap-6">
              <TaskCard 
                time="6:00 AM" 
                title="Leo's Meal Prep" 
                desc="Dairy-free lunchbox for trip" 
                completed 
                color="text-secondary" 
                bg="bg-secondary/10" 
              />
              <TaskCard 
                time="4:00 PM" 
                title="Grocery Run" 
                desc="Pickup Sarah's medicine" 
                color="text-amber-500" 
                bg="bg-amber-400/10" 
                action="Mark as Done"
              />
              <div className="flex-1 rounded-[2rem] border-2 border-dashed border-stone-100 flex flex-col items-center justify-center p-6 text-stone-300 group hover:border-primary/20 hover:text-primary transition-all cursor-pointer">
                <div className="w-16 h-16 rounded-full bg-surface-low flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <PlusCircle size={32} />
                </div>
                <span className="text-[11px] font-black uppercase tracking-[0.3em]">Add Task</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const FilterChip = ({ label, color, active }: any) => (
  <button className={cn(
    "flex items-center gap-2 px-6 py-3 rounded-full text-sm font-black transition-all",
    active ? "bg-primary/10 text-primary" : "bg-surface-low text-stone-400 hover:bg-white"
  )}>
    <div className={cn("w-2 h-2 rounded-full", color)} />
    {label}
  </button>
);

const TaskCard = ({ time, title, desc, completed, color, bg, action }: any) => (
  <BentoCard className="p-6">
    <div className="flex justify-between items-start mb-4">
      <div className={cn("p-2.5 rounded-xl ambient-shadow", bg, color)}>
        {completed ? <CheckCircle2 size={16} /> : <Clock size={16} />}
      </div>
      <span className="text-[10px] font-black uppercase tracking-widest text-stone-400">{time}</span>
    </div>
    <h5 className="text-lg font-black font-headline tracking-tighter mb-1">{title}</h5>
    <p className="text-xs font-medium text-stone-400 mb-6">{desc}</p>
    {completed ? (
      <span className="text-[10px] font-black uppercase tracking-widest text-secondary bg-secondary/10 px-3 py-1.5 rounded-lg">Completed</span>
    ) : (
      <button className="w-full py-3 bg-surface-low text-stone-500 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-stone-200 transition-colors">
        {action}
      </button>
    )}
  </BentoCard>
);

const PlusCircle = ({ size, className }: any) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="12" cy="12" r="10" />
    <path d="M12 8v8M8 12h8" />
  </svg>
);
