import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Calendar, CreditCard, Box, RefreshCw, LogOut, Settings as SettingsIcon } from 'lucide-react';
import { cn } from '../lib/utils';
import { useAuth } from '../contexts/AuthContext';

const navItems = [
  { icon: Home, label: 'Home', path: '/' },
  { icon: Calendar, label: 'Calendar', path: '/calendar' },
  { icon: CreditCard, label: 'Finance', path: '/finance' },
  { icon: Box, label: 'Logistics', path: '/logistics' },
  { icon: RefreshCw, label: 'Sync', path: '/sync' },
  { icon: SettingsIcon, label: 'Settings', path: '/settings' },
];

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { profile, logout } = useAuth();

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-background-base">
      {/* Sidebar - Desktop */}
      <aside className="hidden md:flex flex-col w-64 h-screen sticky top-0 bg-white p-6 border-r border-slate-200">
        <div className="mb-10 px-2 flex items-center gap-3">
          <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center text-white shadow-lg">
            <RefreshCw size={20} />
          </div>
          <h2 className="text-2xl font-bold font-headline tracking-tight text-slate-900">Filiation</h2>
        </div>
        
        <nav className="flex-1 flex flex-col gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-200 font-medium text-slate-600 hover:text-primary hover:bg-slate-50",
                isActive && "bg-indigo-50 text-primary font-bold"
              )}
            >
              <item.icon size={18} />
              <span className="font-headline text-sm">{item.label}</span>
            </NavLink>
          ))}
          
          <button 
            onClick={logout}
            className="flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-200 font-medium text-rose-500 hover:bg-rose-50 mt-4"
          >
            <LogOut size={18} />
            <span className="font-headline text-sm">Logout</span>
          </button>
        </nav>

        <div className="mt-auto px-2 pt-6 border-t border-slate-100">
           <div className="bg-slate-50 rounded-2xl p-4 flex items-center gap-3">
             <div className="flex -space-x-2">
               <div className="w-8 h-8 rounded-full border-2 border-white bg-blue-400" />
               <div className="w-8 h-8 rounded-full border-2 border-white bg-emerald-400" />
               <div className="w-8 h-8 rounded-full border-2 border-white bg-rose-400" />
             </div>
             <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Family (5)</span>
           </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative pb-32 md:pb-0">
        {/* Header */}
        <header className="h-16 bg-white sticky top-0 z-50 flex items-center justify-between px-6 md:px-12 border-b border-slate-200">
          <div className="flex items-center gap-4">
             <div className="w-10 h-10 rounded-full overflow-hidden bg-slate-100 border border-slate-200">
                <img 
                  src={profile?.photoURL || "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&q=80&w=100"} 
                  alt="Avatar" 
                  referrerPolicy="no-referrer"
                  className="w-full h-full object-cover"
                />
             </div>
             <div className="flex flex-col">
                <span className="text-sm font-bold text-slate-800">Good morning, {profile?.displayName?.split(' ')[0] || 'Member'}</span>
                <span className="text-[10px] uppercase font-black tracking-widest text-secondary">Sanctuary Sync Active</span>
             </div>
          </div>
          
          <div className="flex items-center gap-3">
            <button className="px-4 py-2 bg-primary text-white rounded-lg font-bold text-xs hover:bg-primary-container active:scale-95 transition-all shadow-md">
              Add Quick Event
            </button>
          </div>
        </header>

        <div className="px-6 md:px-12 py-8 max-w-7xl">
          {children}
        </div>
      </main>

      {/* Family Chat - Desktop Right Anchor */}
      <aside className="hidden xl:flex flex-col w-80 h-screen sticky top-0 bg-white border-l border-slate-200 p-8 z-40">
        <div className="flex items-center justify-between mb-8">
          <h3 className="text-lg font-bold font-headline text-slate-900">Family Chat</h3>
          <div className="w-2 h-2 rounded-full bg-secondary" />
        </div>
        
        <div className="flex-1 overflow-y-auto space-y-6">
          <ChatMessage name="Maya" message="Dad, pizza night tonight?" time="9:41 AM" />
          <ChatMessage name="You" message="Absolutely. 6pm! 🍕" time="10:02 AM" sender />
          <ChatMessage name="Sarah" message="Soccer practice at 5:30." time="11:15 AM" />
        </div>
        
        <div className="mt-6">
          <div className="relative">
            <input 
              type="text" 
              placeholder="Send message..."
              className="w-full h-12 bg-slate-50 border-none rounded-xl px-5 text-sm focus:ring-2 focus:ring-primary/10 transition-all font-medium"
            />
          </div>
        </div>
      </aside>

      {/* Bottom Nav - Mobile */}
      <nav className="md:hidden fixed bottom-0 w-full bg-white border-t border-slate-200 flex justify-around items-center px-4 py-4 z-50">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => cn(
              "flex flex-col items-center gap-1 p-2 transition-all",
              isActive ? "text-primary scale-110" : "text-stone-400"
            )}
          >
            <item.icon size={22} />
            <span className="text-[10px] font-bold uppercase tracking-widest">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
};

const ChatMessage = ({ name, message, time, sender }: { name: string, message: string, time: string, sender?: boolean }) => (
  <div className={cn("flex flex-col gap-1 max-w-[85%]", sender ? "items-end ml-auto" : "items-start")}>
    <div className={cn(
      "p-4 rounded-2xl text-sm leading-relaxed",
      sender ? "bg-primary text-white rounded-tr-none" : "bg-surface-low text-stone-800 rounded-tl-none"
    )}>
      {message}
    </div>
    <span className="text-[10px] font-bold text-stone-400 px-2 uppercase tracking-tighter">
      {name} • {time}
    </span>
  </div>
);
