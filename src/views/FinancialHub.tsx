import React from 'react';
import { motion } from 'motion/react';
import { 
  Lock, 
  Plus, 
  TrendingUp, 
  CheckCircle, 
  PieChart as ChartIcon, 
  CreditCard, 
  ArrowUpRight, 
  ArrowDownLeft,
  Building2,
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import { BentoCard } from '../components/ui/BentoCard';
import { cn } from '../lib/utils';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const categoryData = [
  { name: 'Utilities', value: 450, color: '#6366f1' },
  { name: 'Subscriptions', value: 120, color: '#f59e0b' },
  { name: 'Food', value: 800, color: '#10b981' },
  { name: 'Entertainment', value: 200, color: '#ec4899' },
  { name: 'Taxes', value: 1500, color: '#f43f5e' },
  { name: 'Housing', value: 2200, color: '#8b5cf6' },
];

const transactionHistory = [
  { id: 1, name: 'Whole Foods', category: 'Food', amount: -142.50, date: 'Today, 2:45 PM', status: 'completed' },
  { id: 2, name: 'Netflix', category: 'Subscriptions', amount: -15.99, date: 'Yesterday', status: 'completed' },
  { id: 3, name: 'IRS Quarterly', category: 'Taxes', amount: -1500.00, date: 'Oct 24, 2023', status: 'pending' },
  { id: 4, name: 'PGE Utilities', category: 'Utilities', amount: -210.15, date: 'Oct 22, 2023', status: 'completed' },
];

const linkedAccounts = [
  { id: 1, bank: 'Chase Bank', name: 'Premium Checking', balance: 12450.80, lastSync: '10m ago' },
  { id: 2, bank: 'American Express', name: 'Gold Card', balance: -2140.12, lastSync: '1h ago' },
];

export const FinancialHub = () => {
  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-12"
    >
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-5xl font-black font-headline tracking-tighter mb-2">Finance Center</h1>
          <p className="text-xl text-stone-500 font-medium">Holistic view of your family's economic sanctuary.</p>
        </div>
        <div className="flex gap-3">
          <button className="px-6 py-3 bg-white border border-slate-200 rounded-2xl font-bold text-sm text-slate-600 hover:bg-slate-50 transition-all active:scale-95 flex items-center gap-2">
            <Building2 size={18} />
            Link Bank
          </button>
          <button className="px-6 py-3 bg-primary text-white rounded-2xl font-bold text-sm shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center gap-2">
            <Plus size={18} />
            Request Funds
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Main Stats Card */}
        <BentoCard className="lg:col-span-8 p-10 flex flex-col justify-between min-h-[380px]">
          <div>
            <div className="flex justify-between items-start mb-10">
               <div>
                  <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Collective Liquidity</span>
                  <div className="text-6xl font-black font-headline tracking-tighter text-slate-900 mt-2">$42,892.20</div>
               </div>
               <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-600 rounded-full text-xs font-black">
                  <TrendingUp size={14} />
                  +12.4% THIS MONTH
               </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-8 border-t border-slate-100">
               <StatSmall label="Income" value="$12,400" icon={ArrowDownLeft} color="text-emerald-500" />
               <StatSmall label="Expenses" value="$5,270" icon={ArrowUpRight} color="text-rose-500" />
               <StatSmall label="Synced Banks" value="4 Institutions" icon={Building2} color="text-primary" />
            </div>
          </div>
          
          <div className="mt-10 p-5 bg-slate-50 rounded-2xl flex items-center justify-between border border-slate-100">
             <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                   <Lock size={18} />
                </div>
                <div>
                   <p className="text-xs font-bold text-slate-900 leading-none">Vault Encryption Active</p>
                   <p className="text-[10px] text-slate-400 mt-1 uppercase font-bold tracking-widest leading-none">External API Keys localized</p>
                </div>
             </div>
             <ChevronRight size={20} className="text-slate-300" />
          </div>
        </BentoCard>

        {/* Expenses by Category Chart */}
        <BentoCard className="lg:col-span-4 p-8 flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-black font-headline text-lg text-slate-900 flex items-center gap-2">
              <ChartIcon size={20} className="text-primary" />
              Burn Profile
            </h3>
          </div>
          <div className="flex-1 min-h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                  itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-6 space-y-2">
             {categoryData.slice(0, 3).map(item => (
                <div key={item.name} className="flex items-center justify-between">
                   <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{item.name}</span>
                   </div>
                   <span className="text-xs font-black text-slate-900">${item.value}</span>
                </div>
             ))}
          </div>
        </BentoCard>

        {/* Sync Feed */}
        <BentoCard className="lg:col-span-8 p-10">
          <div className="flex items-center justify-between mb-8">
            <h3 className="font-black font-headline text-2xl text-slate-900">Sync Feed</h3>
            <button className="text-[10px] font-black uppercase tracking-widest text-primary hover:underline">View Ledger</button>
          </div>
          <div className="space-y-6">
            {transactionHistory.map(item => (
              <div key={item.id} className="flex items-center justify-between p-4 rounded-2xl hover:bg-slate-50 transition-all border border-transparent hover:border-slate-100 group">
                <div className="flex items-center gap-6">
                   <div className={cn(
                     "w-14 h-14 rounded-2xl flex items-center justify-center ambient-shadow",
                     item.amount > 0 ? "bg-emerald-50 text-emerald-600" : "bg-white text-slate-400 group-hover:bg-primary group-hover:text-white transition-all"
                   )}>
                      {item.amount > 0 ? <ArrowDownLeft size={24} /> : <CreditCard size={24} />}
                   </div>
                   <div>
                      <div className="text-lg font-black font-headline text-slate-900">{item.name}</div>
                      <div className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.15em] mt-0.5">{item.category} • {item.date}</div>
                   </div>
                </div>
                <div className="text-right">
                   <div className={cn("text-xl font-black font-headline", item.amount > 0 ? "text-emerald-600" : "text-slate-900")}>
                      {item.amount > 0 ? '+' : ''}{item.amount.toFixed(2)}
                   </div>
                   <div className={cn(
                     "text-[9px] font-black uppercase tracking-widest mt-1",
                     item.status === 'pending' ? "text-amber-500" : "text-emerald-500"
                   )}>
                      {item.status}
                   </div>
                </div>
              </div>
            ))}
          </div>
        </BentoCard>

        {/* External Vaults */}
        <BentoCard className="lg:col-span-4 p-8">
          <div className="flex items-center justify-between mb-8">
            <h3 className="font-black font-headline text-lg text-slate-900">External Vaults</h3>
            <div className="w-8 h-8 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600">
               <CheckCircle size={16} />
            </div>
          </div>
          <div className="space-y-6">
             {linkedAccounts.map(acc => (
               <div key={acc.id} className="p-5 rounded-2xl border border-slate-100 bg-slate-50/50 space-y-4 group hover:bg-white hover:ambient-shadow transition-all">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{acc.bank}</div>
                      <div className="font-black font-headline text-slate-800">{acc.name}</div>
                    </div>
                    <button className="text-slate-300 hover:text-primary transition-colors">
                      <ExternalLink size={16} />
                    </button>
                  </div>
                  <div className="flex justify-between items-end">
                    <div className="text-2xl font-black font-headline text-slate-900">${acc.balance.toLocaleString()}</div>
                    <div className="text-[9px] font-bold text-slate-400 uppercase tracking-widest leading-none">Synced {acc.lastSync}</div>
                  </div>
               </div>
             ))}
             
             <button className="w-full p-5 rounded-2xl border-2 border-dashed border-slate-200 bg-white flex flex-col items-center justify-center gap-3 text-center cursor-pointer hover:border-primary hover:bg-primary/5 transition-all group">
                <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center text-slate-400 group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                   <Plus size={24} />
                </div>
                <div>
                  <div className="text-sm font-black font-headline text-slate-900 italic">Expand Sanctuary</div>
                  <p className="text-[10px] text-slate-400 font-medium leading-tight mt-1 max-w-[140px]">Link external APIs for global visibility.</p>
                </div>
             </button>
          </div>
        </BentoCard>
      </div>
    </motion.div>
  );
};

const StatSmall = ({ label, value, icon: Icon, color }: any) => (
  <div className="space-y-2">
    <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-400">
      <Icon size={12} className={color} />
      {label}
    </div>
    <div className="text-3xl font-black font-headline text-slate-900 tracking-tighter">{value}</div>
  </div>
);
