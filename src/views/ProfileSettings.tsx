import React, { useState } from 'react';
import { useAuth, UserProfile } from '../contexts/AuthContext';
import { motion } from 'motion/react';
import { 
  User as UserIcon, 
  Mail, 
  Calendar as CalendarIcon, 
  Phone, 
  Camera, 
  Save, 
  AlertCircle,
  CheckCircle2,
  Lock,
  Bell,
  BellOff,
  Smartphone
} from 'lucide-react';
import { BentoCard } from '../components/ui/BentoCard';
import { InputGroup } from '../components/ui/InputGroup';
import { NotificationService } from '../lib/notifications';
import { cn } from '../lib/utils';

export const ProfileSettings = () => {
  const { profile, updateProfile } = useAuth();
  const [isSaving, setIsSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notifState, setNotifState] = useState<'granted' | 'denied' | 'default'>(
    typeof Notification !== 'undefined' ? Notification.permission : 'default'
  );

  const [formData, setFormData] = useState<Partial<UserProfile>>({
    displayName: profile?.displayName || '',
    photoURL: profile?.photoURL || '',
    birthday: profile?.birthday || '',
    bio: profile?.bio || '',
    phoneNumber: profile?.phoneNumber || '',
  });

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSuccess(false);
    setError(null);

    try {
      await updateProfile(formData);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError('Failed to update sanctuary profile');
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleEnableNotifications = async () => {
    const granted = await NotificationService.requestPermission();
    if (granted) {
      setNotifState('granted');
      NotificationService.showLocalNotification('Sanctuary Synced', 'You will now receive family alerts on this device.');
    } else {
      setNotifState('denied');
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto space-y-12"
    >
      <header>
        <h1 className="text-5xl font-black font-headline tracking-tighter text-slate-900">Sanctuary Profile</h1>
        <p className="text-xl text-slate-500 font-medium">Manage your digital presence and privacy settings.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Identity & Notifications */}
        <div className="lg:col-span-4 space-y-6">
          <section className="bg-white rounded-[2rem] p-8 border border-slate-200 ambient-shadow">
            <div className="flex flex-col items-center gap-6">
              <div className="relative group">
                <div className="w-32 h-32 rounded-full overflow-hidden border-4 border-slate-50 ambient-shadow bg-slate-100">
                  <img 
                    src={formData.photoURL || "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&q=80&w=200"} 
                    alt="Profile" 
                    referrerPolicy="no-referrer"
                    className="w-full h-full object-cover"
                  />
                </div>
                <button className="absolute bottom-0 right-0 p-2.5 bg-primary text-white rounded-xl shadow-lg hover:bg-primary-container transition-all active:scale-95">
                  <Camera size={18} />
                </button>
              </div>

              <div className="text-center space-y-1">
                <h2 className="text-xl font-black font-headline text-slate-900">{profile?.displayName || 'Family Member'}</h2>
                <div className="flex items-center justify-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-widest leading-none">
                  <Lock size={10} className="text-slate-300" />
                  Locally Encrypted
                </div>
              </div>
            </div>
          </section>

          {/* Notification Card */}
          <section className="bg-slate-900 rounded-[2rem] p-8 text-white ambient-shadow space-y-6">
            <div className="flex items-center gap-4">
              <div className={cn(
                "w-12 h-12 rounded-2xl flex items-center justify-center",
                notifState === 'granted' ? "bg-emerald-500/20 text-emerald-400" : "bg-white/10 text-white/40"
              )}>
                {notifState === 'granted' ? <Bell size={24} /> : <BellOff size={24} />}
              </div>
              <div>
                <h3 className="font-black font-headline tracking-tight">Push Alerts</h3>
                <p className="text-[10px] uppercase font-bold tracking-widest text-white/40">Real-time Syncing</p>
              </div>
            </div>

            <p className="text-sm font-medium text-white/60 leading-relaxed">
              Enable notifications to receive instant updates on logistics, financing requests, and family syncs.
            </p>

            <button 
              type="button"
              onClick={handleEnableNotifications}
              disabled={notifState === 'granted'}
              className={cn(
                "w-full py-4 rounded-2xl font-black text-sm transition-all active:scale-95 flex items-center justify-center gap-2",
                notifState === 'granted' 
                  ? "bg-white/5 text-white/40 cursor-default" 
                  : "bg-primary text-white shadow-xl shadow-primary/20 hover:scale-[1.02]"
              )}
            >
              {notifState === 'granted' ? (
                <>
                  <CheckCircle2 size={18} />
                  Enabled on Device
                </>
              ) : (
                <>
                  <Smartphone size={18} />
                  Setup Notifications
                </>
              )}
            </button>
          </section>
        </div>

        {/* Right Column: Settings Form */}
        <form onSubmit={handleSave} className="lg:col-span-8 space-y-6">
          <div className="bg-white rounded-[2.5rem] p-8 md:p-10 border border-slate-200 ambient-shadow space-y-10">
            
            <section className="space-y-6">
              <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-400 border-b border-slate-50 pb-2">Core Identity</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <InputGroup 
                  label="Display Name" 
                  icon={UserIcon} 
                  value={formData.displayName}
                  onChange={(e: any) => setFormData({...formData, displayName: e.target.value})}
                  placeholder="Sarah Miller"
                />
                <InputGroup 
                  label="Email Address" 
                  icon={Mail} 
                  value={profile?.email}
                  disabled
                  placeholder="sarah@filiation.com"
                />
              </div>
            </section>

            <section className="space-y-6">
              <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-400 border-b border-slate-50 pb-2">Personal Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <InputGroup 
                  label="Birthday" 
                  icon={CalendarIcon} 
                  type="date"
                  value={formData.birthday}
                  onChange={(e: any) => setFormData({...formData, birthday: e.target.value})}
                />
                <InputGroup 
                  label="Phone Number" 
                  icon={Phone} 
                  placeholder="+1 (555) 000-0000"
                  value={formData.phoneNumber}
                  onChange={(e: any) => setFormData({...formData, phoneNumber: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">About Me</label>
                <div className="relative">
                    <textarea 
                      placeholder="Share a short bio with your family..."
                      value={formData.bio}
                      onChange={(e) => setFormData({...formData, bio: e.target.value})}
                      className="w-full h-32 bg-slate-50 border-none rounded-2xl px-6 py-4 text-sm focus:ring-2 focus:ring-primary/10 transition-all font-medium resize-none shadow-inner"
                    />
                </div>
              </div>
            </section>

            <section className="space-y-6">
              <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-400 border-b border-slate-50 pb-2">Profile Metadata</h3>
              <InputGroup 
                label="Profile Image URL" 
                icon={Camera} 
                placeholder="https://..."
                value={formData.photoURL}
                onChange={(e: any) => setFormData({...formData, photoURL: e.target.value})}
              />
            </section>

            <div className="pt-4 flex items-center justify-between gap-6">
               {success && (
                 <motion.div 
                   initial={{ opacity: 0, x: -10 }} 
                   animate={{ opacity: 1, x: 0 }}
                   className="flex items-center gap-2 text-emerald-500 font-bold text-sm"
                 >
                   <CheckCircle2 size={18} />
                   Sanctuary Synced!
                 </motion.div>
               )}
               {error && (
                 <div className="flex items-center gap-2 text-rose-500 font-bold text-sm">
                   <AlertCircle size={18} />
                   {error}
                 </div>
               )}
               <button 
                 type="submit"
                 disabled={isSaving}
                 className={cn(
                   "ml-auto px-8 py-4 bg-primary text-white rounded-2xl font-black flex items-center gap-3 transition-all active:scale-95 shadow-xl shadow-primary/20",
                   isSaving && "opacity-50 cursor-not-allowed"
                 )}
               >
                 <Save size={20} />
                 {isSaving ? 'Saving...' : 'Update Profile'}
               </button>
            </div>
          </div>
        </form>
      </div>
    </motion.div>
  );
};
