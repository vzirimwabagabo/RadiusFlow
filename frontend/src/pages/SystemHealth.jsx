import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/authState';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import { CardSkeletonGrid } from '../components/Skeletons';
import api from '../services/api';

const SystemHealth = () => {
  const { user } = useAuth();
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const fetchHealth = async (isManual = false) => {
    try {
      if (isManual) setRefreshing(true);
      else setLoading(true);
      setError('');
      const response = await api.get('/health');
      setHealth(response.data);
    } catch (err) {
      console.error('Failed to load system health:', err);
      setError('Failed to load system health diagnostics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const isHealthy = health?.status === 'healthy';

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Operations & Telemetry"
        title="System Health & Infrastructure"
        description="Live operational health metrics, database latency, and FreeRADIUS service integration status."
        actions={
          <button
            onClick={() => fetchHealth(true)}
            disabled={refreshing}
            className="flex items-center gap-2 rounded-2xl border border-slate-800 bg-slate-900/80 px-4 py-2 text-xs font-semibold text-cyan-400 transition hover:border-cyan-500/40 hover:bg-slate-900 disabled:opacity-50"
          >
            <svg
              className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            <span>{refreshing ? 'Testing...' : 'Run Diagnostics'}</span>
          </button>
        }
      />

      {error && (
        <div className="flex items-center gap-3 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs font-semibold text-rose-300">
          <svg className="h-5 w-5 text-rose-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <CardSkeletonGrid cards={4} />
      ) : (
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          <TelemetryCard
            title="Overall System Status"
            value={health?.status || 'Unknown'}
            subtext="Consolidated system check"
            badge={<StatusBadge status={isHealthy ? 'healthy' : 'degraded'} />}
            icon={
              <svg className="h-6 w-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            }
          />

          <TelemetryCard
            title="PostgreSQL Engine"
            value={health?.postgresql || 'Unknown'}
            subtext={`DB Query Latency: ${health?.db_latency_ms ?? 'N/A'} ms`}
            badge={<StatusBadge status={health?.postgresql === 'reachable' ? 'online' : 'offline'} />}
            icon={
              <svg className="h-6 w-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
              </svg>
            }
          />

          <TelemetryCard
            title="FreeRADIUS Integration"
            value={health?.freeradius || 'Managed VPS'}
            subtext="Port 1812/1813 authentication & accounting"
            badge={<StatusBadge status="online" customLabel="Active VPS" />}
            icon={
              <svg className="h-6 w-6 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
              </svg>
            }
          />

          <TelemetryCard
            title="FastAPI Web Service"
            value={health?.api_service || 'Online'}
            subtext="REST API Gateway"
            badge={<StatusBadge status="online" />}
            icon={
              <svg className="h-6 w-6 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
          />

          <TelemetryCard
            title="Software Build Version"
            value={`v${health?.version || '1.0.0'}`}
            subtext="RadiusFlow Enterprise Core"
            badge={<span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-300">Stable</span>}
            icon={
              <svg className="h-6 w-6 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              </svg>
            }
          />

          <TelemetryCard
            title="Environment Mode"
            value={health?.environment || 'Development'}
            subtext="Runtime configuration profile"
            badge={<span className="rounded-full bg-cyan-500/10 border border-cyan-500/20 px-3 py-1 text-xs font-semibold text-cyan-400 capitalize">{health?.environment || 'dev'}</span>}
            icon={
              <svg className="h-6 w-6 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L5.595 15.12a2 2 0 00-1.8 1.485l-.558 2.232a2 2 0 001.94 2.484h13.646a2 2 0 001.94-2.484l-.558-2.232z" />
              </svg>
            }
          />
        </div>
      )}
    </div>
  );
};

const TelemetryCard = ({ title, value, subtext, badge, icon }) => (
  <div className="glass-card rounded-3xl p-6 transition-all duration-300 hover:-translate-y-1 hover:border-cyan-500/30">
    <div className="flex items-center justify-between">
      <span className="text-xs font-bold uppercase tracking-wider text-slate-400">{title}</span>
      <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/80">
        {icon}
      </div>
    </div>
    <div className="mt-4 flex items-baseline justify-between gap-2">
      <p className="font-display text-2xl font-extrabold text-slate-100 capitalize">{value}</p>
      {badge}
    </div>
    <p className="mt-2 text-xs text-slate-400">{subtext}</p>
  </div>
);

export default SystemHealth;