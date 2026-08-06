import React from 'react';

const STATUS_CONFIGS = {
  active: {
    label: 'Active',
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-400',
    border: 'border-emerald-500/20',
    dot: 'bg-emerald-400 animate-pulse',
  },
  online: {
    label: 'Online',
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-400',
    border: 'border-emerald-500/20',
    dot: 'bg-emerald-400 animate-pulse',
  },
  healthy: {
    label: 'Healthy',
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-400',
    border: 'border-emerald-500/20',
    dot: 'bg-emerald-400',
  },
  blocked: {
    label: 'Blocked',
    bg: 'bg-rose-500/10',
    text: 'text-rose-400',
    border: 'border-rose-500/20',
    dot: 'bg-rose-400',
  },
  expired: {
    label: 'Expired',
    bg: 'bg-amber-500/10',
    text: 'text-amber-400',
    border: 'border-amber-500/20',
    dot: 'bg-amber-400',
  },
  degraded: {
    label: 'Degraded',
    bg: 'bg-amber-500/10',
    text: 'text-amber-400',
    border: 'border-amber-500/20',
    dot: 'bg-amber-400',
  },
  offline: {
    label: 'Offline',
    bg: 'bg-slate-500/10',
    text: 'text-slate-400',
    border: 'border-slate-500/20',
    dot: 'bg-slate-400',
  },
};

const StatusBadge = ({ status, customLabel, size = 'normal' }) => {
  const normalized = (status || '').toLowerCase();
  const config = STATUS_CONFIGS[normalized] || {
    label: status || 'Unknown',
    bg: 'bg-slate-500/10',
    text: 'text-slate-400',
    border: 'border-slate-500/20',
    dot: 'bg-slate-400',
  };

  const isSmall = size === 'small';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${config.bg} ${config.text} ${config.border} ${
        isSmall ? 'px-2 py-0.5 text-[10px] font-semibold' : 'px-3 py-1 text-xs font-semibold'
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${config.dot}`} />
      {customLabel || config.label}
    </span>
  );
};

export default StatusBadge;
