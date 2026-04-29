import React from 'react';
import { cn } from '../../lib/utils';
import { LucideIcon } from 'lucide-react';

interface InputGroupProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  icon?: LucideIcon;
  error?: string;
}

export const InputGroup: React.FC<InputGroupProps> = ({ 
  label, 
  icon: Icon, 
  error,
  className,
  ...props 
}) => (
  <div className="space-y-2 flex-1">
    <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">
      {label}
    </label>
    <div className="relative">
        {Icon && (
          <div className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-300">
              <Icon size={18} />
          </div>
        )}
        <input 
          {...props}
          className={cn(
            "w-full h-14 bg-slate-50 border-none rounded-2xl px-6 text-sm focus:ring-2 focus:ring-primary/10 transition-all font-medium",
            Icon && "pl-12",
            props.disabled && "opacity-50 cursor-not-allowed",
            error && "ring-2 ring-rose-500/20",
            className
          )}
        />
    </div>
    {error && <p className="text-[10px] text-rose-500 font-bold px-2">{error}</p>}
  </div>
);
