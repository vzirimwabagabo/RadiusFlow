import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/authState';
import PageHeader from '../components/PageHeader';
import { CardSkeletonGrid } from '../components/Skeletons';
import api from '../services/api';

const Reports = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    onlineUsers: 0,
    activeSessions: 0,
    totalDownload: 0,
    totalUpload: 0,
    totalRevenue: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const exportReport = (format) => {
    const rows = [
      ['metric', 'value'],
      ['online_users', stats.onlineUsers],
      ['active_sessions', stats.activeSessions],
      ['total_download_bytes', stats.totalDownload],
      ['total_upload_bytes', stats.totalUpload],
      ['completed_sessions', stats.totalRevenue],
    ];

    const content =
      format === 'json'
        ? JSON.stringify({ generated_at: new Date().toISOString(), ...stats }, null, 2)
        : rows
            .map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(','))
            .join('\n');

    const blob = new Blob([content], {
      type: format === 'json' ? 'application/json' : 'text/csv;charset=utf-8;',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `radiusflow-report-${new Date().toISOString().slice(0, 10)}.${format}`;
    link.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    const fetchReports = async () => {
      try {
        setLoading(true);
        const [usersResponse, trafficResponse, revenueResponse] = await Promise.all([
          api.get('/monitor/online-users'),
          api.get('/monitor/traffic-stats'),
          api.get('/monitor/revenue'),
        ]);

        setStats({
          onlineUsers: usersResponse.data?.online_users || 0,
          activeSessions: trafficResponse.data?.active_sessions || 0,
          totalDownload: trafficResponse.data?.total_download || 0,
          totalUpload: trafficResponse.data?.total_upload || 0,
          totalRevenue: revenueResponse.data?.total_sessions || 0,
        });
      } catch (err) {
        console.error('Failed to load reports:', err);
        setError('Failed to load operational analytics reports');
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Analytics & Reports"
        title="Operational Analytics & Metrics"
        description="Real-time traffic statistics, subscriber session volume, and exportable operational logs."
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => exportReport('csv')}
              className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-500 to-violet-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-cyan-500/20 transition hover:brightness-110"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>Export CSV</span>
            </button>
            <button
              onClick={() => exportReport('json')}
              className="flex items-center gap-2 rounded-2xl border border-slate-800 bg-slate-900/80 px-4 py-2 text-xs font-bold text-slate-200 transition hover:border-cyan-500/40 hover:bg-slate-900"
            >
              <svg className="h-4 w-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span>Export JSON</span>
            </button>
          </div>
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
        <CardSkeletonGrid cards={5} />
      ) : (
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          <ReportMetricCard
            title="Online Users"
            value={stats.onlineUsers}
            formattedValue={`${stats.onlineUsers} Active`}
            subtext="Current streaming RADIUS sessions"
            tone="cyan"
          />

          <ReportMetricCard
            title="Active Sessions"
            value={stats.activeSessions}
            formattedValue={`${stats.activeSessions} Open`}
            subtext="Active radacct records"
            tone="violet"
          />

          <ReportMetricCard
            title="Total Download Traffic"
            value={stats.totalDownload}
            formattedValue={formatBytes(stats.totalDownload)}
            subtext={`${stats.totalDownload.toLocaleString()} raw octets`}
            tone="emerald"
          />

          <ReportMetricCard
            title="Total Upload Traffic"
            value={stats.totalUpload}
            formattedValue={formatBytes(stats.totalUpload)}
            subtext={`${stats.totalUpload.toLocaleString()} raw octets`}
            tone="indigo"
          />

          <ReportMetricCard
            title="Completed Sessions"
            value={stats.totalRevenue}
            formattedValue={`${stats.totalRevenue} Closed`}
            subtext="Closed radacct records"
            tone="amber"
          />

          <div className="glass-panel rounded-3xl p-6 shadow-xl md:col-span-1 lg:col-span-3">
            <h3 className="font-display text-base font-bold text-slate-100">Telemetry Sources & Notes</h3>
            <p className="mt-2 text-xs text-slate-400 leading-relaxed">
              These metrics are queried live from FreeRADIUS accounting records (<span className="font-mono text-cyan-400">radacct</span>) via the backend monitor service endpoints (<span className="font-mono text-cyan-400">/monitor/online-users</span>, <span className="font-mono text-cyan-400">/monitor/traffic-stats</span>, and <span className="font-mono text-cyan-400">/monitor/revenue</span>).
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

const ReportMetricCard = ({ title, formattedValue, subtext, tone }) => {
  const toneGlow = {
    cyan: 'border-cyan-500/20 hover:border-cyan-500/40 hover:shadow-cyan-500/10',
    violet: 'border-violet-500/20 hover:border-violet-500/40 hover:shadow-violet-500/10',
    emerald: 'border-emerald-500/20 hover:border-emerald-500/40 hover:shadow-emerald-500/10',
    indigo: 'border-indigo-500/20 hover:border-indigo-500/40 hover:shadow-indigo-500/10',
    amber: 'border-amber-500/20 hover:border-amber-500/40 hover:shadow-amber-500/10',
  };

  const topBar = {
    cyan: 'bg-gradient-to-r from-cyan-500 to-cyan-400',
    violet: 'bg-gradient-to-r from-violet-500 to-purple-400',
    emerald: 'bg-gradient-to-r from-emerald-500 to-teal-400',
    indigo: 'bg-gradient-to-r from-indigo-500 to-blue-400',
    amber: 'bg-gradient-to-r from-amber-500 to-orange-400',
  };

  return (
    <div className={`glass-card overflow-hidden rounded-3xl transition-all duration-300 hover:-translate-y-1 ${toneGlow[tone]}`}>
      <div className={`h-1.5 w-full ${topBar[tone]}`} />
      <div className="p-6">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">{title}</span>
        <p className="font-display mt-3 text-2xl font-extrabold text-slate-100">{formattedValue}</p>
        <p className="mt-1 text-xs text-slate-400">{subtext}</p>
      </div>
    </div>
  );
};

export default Reports;