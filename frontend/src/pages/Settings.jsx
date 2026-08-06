import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/authState';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';

const Settings = () => {
  const { user } = useAuth();
  const [settings, setSettings] = useState({
    apiBaseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    refreshInterval: '30',
    notifications: true,
  });

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setSettings((current) => ({
      ...current,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  return (
    <div className="space-y-6">
      <PageHeader
        badge="System Configuration"
        title="Application Settings & Profile"
        description="View API gateway configuration, active operator session profile, and system preferences."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* API & UI Settings Panel */}
        <div className="glass-panel rounded-3xl p-6 shadow-xl space-y-5">
          <h2 className="font-display text-base font-bold text-slate-100 border-b border-slate-800/80 pb-3">
            Console Preferences & API Gateway
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                API Base Endpoint URL
              </label>
              <input
                type="text"
                readOnly
                value={settings.apiBaseUrl}
                className="w-full rounded-2xl border border-slate-800 bg-slate-950/80 px-4 py-3 font-mono text-xs text-cyan-400 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Telemetry Refresh Rate (Seconds)
              </label>
              <input
                type="text"
                name="refreshInterval"
                value={settings.refreshInterval}
                onChange={handleChange}
                className="w-full rounded-2xl border border-slate-800 bg-slate-950/80 px-4 py-3 text-xs text-slate-200 outline-none focus:border-cyan-500"
              />
            </div>

            <label className="flex items-center gap-3 rounded-2xl border border-slate-800 bg-slate-950/40 p-4 cursor-pointer hover:bg-slate-950/80 transition">
              <input
                type="checkbox"
                name="notifications"
                checked={settings.notifications}
                onChange={handleChange}
                className="h-4 w-4 rounded border-slate-800 bg-slate-950 text-cyan-500 focus:ring-cyan-500/20"
              />
              <div>
                <p className="text-xs font-semibold text-slate-200">System Toast Notifications</p>
                <p className="text-[10px] text-slate-400">Display visual alerts for stale sessions and API errors</p>
              </div>
            </label>
          </div>
        </div>

        {/* User Profile Panel */}
        <div className="glass-panel rounded-3xl p-6 shadow-xl space-y-5">
          <h2 className="font-display text-base font-bold text-slate-100 border-b border-slate-800/80 pb-3">
            Active Operator Profile
          </h2>

          <div className="space-y-4 text-xs">
            <div className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
              <span className="text-slate-400">Username</span>
              <span className="font-bold text-slate-100">{user?.username || 'Admin'}</span>
            </div>

            <div className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
              <span className="text-slate-400">Assigned Management Role</span>
              <StatusBadge status="online" customLabel={user?.role || 'Administrator'} size="small" />
            </div>

            <div className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
              <span className="text-slate-400">Authentication Method</span>
              <span className="font-mono text-cyan-400">JWT Bearer (Scrypt Session)</span>
            </div>

            <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-4 text-slate-300 leading-relaxed">
              <p className="font-bold text-cyan-300 mb-1">Architecture Note</p>
              <p className="text-[11px] text-slate-400">
                RadiusFlow Enterprise separates management user accounts (<span className="font-mono text-slate-200">app_users</span>) from network subscriber credentials (<span className="font-mono text-slate-200">radcheck</span>).
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;