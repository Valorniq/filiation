import React, { useState } from 'react';
import { motion } from 'motion/react';
import { 
  RefreshCw, 
  ShieldCheck, 
  Users, 
  Smartphone, 
  Zap, 
  Globe, 
  Server, 
  CheckCircle2, 
  Clock,
  ArrowRight,
  Send,
  AlertTriangle,
  Building2,
  Key,
  Database
} from 'lucide-react';
import { BentoCard } from '../components/ui/BentoCard';
import { NotificationService } from '../lib/notifications';
import { cn } from '../lib/utils';

export const SyncHub = () => {
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'complete'>('idle');
  const [activeMembers] = useState(['You', 'Maddie', 'Leo']);
  const [p2pRequests] = useState([
    { id: 1, type: 'Financial', from: 'Maddie', amount: '$25.00', note: 'Dinner sync', status: 'pending' },
    { id: 2, type: 'Logistics', from: 'Leo', note: 'Pick up at School', status: 'pending' },
  ]);

  const handleSync = () => {
    setSyncStatus('syncing');
    setTimeout(() => {
      setSyncStatus('complete');
      NotificationService.showLocalNotification('Sanctuary Sync Complete', 'All family nodes have been updated.');
      setTimeout(() => setSyncStatus('idle'), 3000);
    }, 2500);
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-12"
    >
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-5xl font-black font-headline tracking-tighter mb-2">Sync Engine</h1>
          <p className="text-xl text-stone-500 font-medium">Global family presence & P2P relay.</p>
        </div>
        <button 
          onClick={handleSync}
          disabled={syncStatus !== 'idle'}
          className={cn(
            "px-8 py-4 rounded-2xl font-black text-white transition-all flex items-center justify-center gap-3 shadow-xl overflow-hidden relative",
            syncStatus === 'syncing' ? "bg-slate-800" : syncStatus === 'complete' ? "bg-emerald-500 shadow-emerald-500/20" : "bg-primary shadow-primary/20 hover:scale-105 active:scale-95"
          )}
        >
          {syncStatus === 'syncing' ? (
            <>
              <RefreshCw size={20} className="animate-spin" />
              Relaying Nodes...
            </>
          ) : syncStatus === 'complete' ? (
            <>
              <CheckCircle2 size={20} />
              Nodes Aligned
            </>
          ) : (
            <>
              <RefreshCw size={20} />
              Manual Sanctuary Sync
            </>
          )}
          
          {syncStatus === 'syncing' && (
            <motion.div 
              layoutId="sync-progress"
              initial={{ x: "-100%" }}
              animate={{ x: "0%" }}
              className="absolute bottom-0 left-0 h-1 bg-white/30 w-full"
            />
          )}
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Active Node Map */}
        <BentoCard className="md:col-span-8 p-10 bg-slate-900 border-0 text-white min-h-[400px] flex flex-col justify-between relative overflow-hidden">
          <div className="absolute top-0 right-0 p-10 opacity-10">
            <Globe size={300} />
          </div>
          
          <div className="relative z-10">
            <h3 className="text-2xl font-black font-headline tracking-tight mb-8 flex items-center gap-3">
              <Zap className="text-primary-container" size={24} />
              Live Sanctuary Map
            </h3>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-8">
               <NodeStat label="Active Nodes" value={activeMembers.length.toString()} icon={Users} status="Online" />
               <NodeStat label="Encryption" value="AES-256" icon={ShieldCheck} status="Hardened" />
               <NodeStat label="P2P Latency" value="14ms" icon={Server} status="Optimized" />
            </div>
          </div>

          <div className="mt-12 space-y-4 relative z-10">
             <p className="text-xs font-bold text-white/40 uppercase tracking-[0.2em]">Sanctuary Health</p>
             <div className="flex gap-1">
                {[...Array(24)].map((_, i) => (
                  <motion.div 
                    key={i} 
                    animate={{ height: [16, 24, 16] }}
                    transition={{ duration: 1, repeat: Infinity, delay: i * 0.1 }}
                    className="flex-1 rounded-full bg-emerald-500/50" 
                  />
                ))}
             </div>
          </div>
        </BentoCard>

        {/* Device Status */}
        <BentoCard className="md:col-span-4 p-8 flex flex-col justify-between">
          <div>
            <h3 className="text-xl font-black font-headline tracking-tight mb-6">Linked Hardware</h3>
            <div className="space-y-4">
              <DeviceItem label="Sarah's iPhone" status="Filiation Node Active" icon={Smartphone} />
              <DeviceItem label="Fili-Hub Node 1" status="Primary Relay" icon={Server} />
              <DeviceItem label="Leo's Android" status="Disconnected" icon={Smartphone} inactive />
            </div>
          </div>
          
          <div className="mt-8 p-4 bg-primary/5 rounded-2xl border border-primary/10">
             <p className="text-[10px] font-bold text-primary leading-relaxed text-center uppercase tracking-widest">
                Nodes are authenticated via RSA Keypairs generated locally.
             </p>
          </div>
        </BentoCard>

        {/* External API Vault */}
        <BentoCard className="md:col-span-12 p-10 border border-slate-100 flex flex-col md:flex-row gap-10 items-center">
          <div className="flex-1 space-y-6">
            <div className="flex items-center gap-5">
              <div className="w-16 h-16 rounded-[1.5rem] bg-stone-900 flex items-center justify-center p-3">
                 <Building2 className="text-white" size={32} />
              </div>
              <div>
                <h3 className="text-3xl font-black font-headline tracking-tighter">API Vault</h3>
                <span className="px-3 py-1 bg-emerald-100 text-emerald-600 text-[10px] font-black uppercase tracking-[0.2em] rounded-full">Encrypted</span>
              </div>
            </div>
            
            <p className="text-slate-500 font-medium leading-relaxed max-w-md">
              Securely store credentials for Plaid, Schoology, and Insurance portals. Keys are never sent to our servers; they stay on your family nodes.
            </p>

            <div className="flex gap-4">
               <button className="h-14 px-10 bg-slate-900 text-white font-black rounded-2xl active:scale-95 transition-all flex items-center gap-3">
                 <Key size={18} />
                 Manage Keys
               </button>
               <button className="h-14 px-10 bg-slate-100 text-slate-500 font-black rounded-2xl hover:bg-slate-200 transition-all flex items-center gap-3">
                 <Database size={18} />
                 Clear Cache
               </button>
            </div>
          </div>
          
          <div className="w-full md:w-64 aspect-square rounded-[3rem] overflow-hidden bg-slate-50 ambient-shadow border-4 border-white flex items-center justify-center">
             <ShieldCheck size={120} className="text-primary/20" />
          </div>
        </BentoCard>

        {/* P2P Request Relay */}
        <BentoCard className="md:col-span-12 p-10">
           <div className="flex items-center justify-between mb-10">
              <h3 className="text-3xl font-black font-headline tracking-tighter italic">P2P Request Relay</h3>
              <div className="flex items-center gap-2 px-4 py-2 bg-slate-100 rounded-full text-[10px] font-black uppercase tracking-widest text-slate-500">
                 <AlertTriangle size={14} className="text-amber-500" />
                 2 Pending Handshakes
              </div>
           </div>

           <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {p2pRequests.map(req => (
                <div key={req.id} className="p-6 rounded-[2rem] bg-slate-50 border border-slate-100 flex items-center justify-between group hover:bg-white hover:ambient-shadow transition-all">
                   <div className="flex items-center gap-6">
                      <div className="w-16 h-16 rounded-2xl bg-white flex items-center justify-center ambient-shadow text-primary font-black scale-110">
                         {req.type[0]}
                      </div>
                      <div>
                         <div className="text-lg font-black font-headline text-slate-800">{req.from}</div>
                         <p className="text-xs font-medium text-slate-400 max-w-[200px] line-clamp-1">{req.note}</p>
                         <div className="mt-1 inline-flex items-center gap-1.5 text-[9px] font-black uppercase tracking-widest text-secondary">
                            <Clock size={10} />
                            Requested 4h ago
                         </div>
                      </div>
                   </div>
                   
                   <div className="flex flex-col items-end gap-3">
                      {req.amount && <div className="text-2xl font-black font-headline text-slate-900">{req.amount}</div>}
                      <button className="px-6 h-10 bg-slate-900 text-white rounded-full text-xs font-black flex items-center gap-2 hover:bg-primary transition-colors">
                         Settle
                         <ArrowRight size={14} />
                      </button>
                   </div>
                </div>
              ))}
           </div>

           <div className="mt-12 flex justify-center">
              <button className="flex items-center gap-3 text-sm font-black text-slate-300 hover:text-primary transition-all group">
                 <Send size={18} className="group-hover:-translate-y-1 group-hover:translate-x-1 transition-transform" />
                 Broadcast New Collective Request
              </button>
           </div>
        </BentoCard>
      </div>
    </motion.div>
  );
};

const NodeStat = ({ label, value, status, icon: Icon }: any) => (
  <div className="space-y-3">
    <div className="flex items-center gap-2">
       <Icon size={18} className="text-primary-container" />
       <span className="text-[10px] font-black uppercase tracking-widest text-white/40">{label}</span>
    </div>
    <div className="space-y-0.5">
       <div className="text-3xl font-black font-headline">{value}</div>
       <div className="text-[9px] font-bold text-emerald-400 uppercase tracking-widest flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          {status}
       </div>
    </div>
  </div>
);

const DeviceItem = ({ label, status, icon: Icon, inactive = false }: any) => (
  <div className={cn(
    "flex items-center gap-4 p-4 rounded-2xl border border-slate-50",
    inactive ? "opacity-50" : "bg-white"
  )}>
    <div className={cn(
      "w-12 h-12 rounded-xl flex items-center justify-center",
      inactive ? "bg-slate-100 text-slate-400" : "bg-emerald-50 text-emerald-600"
    )}>
      <Icon size={20} />
    </div>
    <div className="flex-1">
      <div className="text-sm font-black text-slate-800">{label}</div>
      <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{status}</div>
    </div>
    {!inactive && <div className="w-2 h-2 rounded-full bg-emerald-500" />}
  </div>
);
