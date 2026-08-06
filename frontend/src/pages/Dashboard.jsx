import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/authState';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import PaginationControls from '../components/PaginationControls';
import { CardSkeletonGrid, TableSkeleton } from '../components/Skeletons';
import api from '../services/api';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    onlineUsers: 0,
    totalUsers: 0,
    activeNas: 0,
    activeSessions: 0,
  });
  const [recentSessions, setRecentSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const pageSize = 5;

  const totalPages = Math.max(1, Math.ceil(recentSessions.length / pageSize));
  const paginatedRecentSessions = recentSessions.slice((page - 1) * pageSize, page * pageSize);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [onlineUsersResponse, usersResponse, nasResponse, sessionsResponse] = await Promise.all([
          api.get('/monitor/online-users'),
          api.get('/users'),
          api.get('/nas'),
          api.get('/sessions'),
        ]);

        setStats({
          onlineUsers: onlineUsersResponse.data?.online_users || 0,
          totalUsers: Array.isArray(usersResponse.data) ? usersResponse.data.length : 0,
          activeNas: Array.isArray(nasResponse.data) ? nasResponse.data.length : 0,
          activeSessions: Array.isArray(sessionsResponse.data) ? sessionsResponse.data.length : 0,
        });
        setRecentSessions(Array.isArray(sessionsResponse.data) ? sessionsResponse.data : []);
      } catch (error) {
        console.error('Failed to fetch dashboard stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  useEffect(() => {
    setPage((current) => Math.min(current, totalPages));
  }, [totalPages]);

  const formatDuration = (seconds) => {
    if (!seconds && seconds !== 0) return 'N/A';
    const totalSeconds = Number(seconds);
    if (Number.isNaN(totalSeconds)) return 'N/A';

    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const remainingSeconds = totalSeconds % 60;

    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${remainingSeconds}s`;
    return `${remainingSeconds}s`;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <CardSkeletonGrid cards={4} />
        <div className="glass-panel rounded-3xl p-6 shadow-sm">
          <div className="h-6 w-48 animate-pulse rounded-full bg-slate-800" />
          <TableSkeleton rows={5} columns={4} compact />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Overview"
        title="Network Operations Center"
        description="Real-time telemetry, active subscriber sessions, and infrastructure metrics."
        actions={
          <div className="flex items-center gap-2 rounded-2xl border border-slate-800 bg-slate-900/80 px-4 py-2 text-xs font-semibold text-slate-300">
            <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
            <span>Telemetry Active</span>
          </div>
        }
      />

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Online Subscribers"
          value={stats.onlineUsers}
          subtext="Active RADIUS sessions"
          icon={
            <svg className="h-6 w-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          tone="cyan"
        />

        <KpiCard
          title="Total Subscribers"
          value={stats.totalUsers}
          subtext="Provisioned accounts"
          icon={
            <svg className="h-6 w-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          }
          tone="emerald"
        />

        <KpiCard
          title="NAS Routers"
          value={stats.activeNas}
          subtext="Connected NAS gateways"
          icon={
            <svg className="h-6 w-6 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
            </svg>
          }
          tone="violet"
        />

        <KpiCard
          title="Active Sessions"
          value={stats.activeSessions}
          subtext="Open radacct streams"
          icon={
            <svg className="h-6 w-6 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          }
          tone="amber"
        />
      </div>

      {/* Active Sessions Table */}
      <div className="glass-panel overflow-hidden rounded-3xl shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800/80 px-6 py-5">
          <div>
            <h2 className="font-display text-lg font-bold text-slate-100">Live Accounting Sessions</h2>
            <p className="text-xs text-slate-400">Current ongoing sessions reported by NAS gateways.</p>
          </div>
          <span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-300">
            {recentSessions.length} active
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800/80 bg-slate-900/60 text-xs uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-6 py-3.5 font-semibold">Subscriber</th>
                <th className="px-6 py-3.5 font-semibold">NAS IP</th>
                <th className="px-6 py-3.5 font-semibold">Framed IP</th>
                <th className="px-6 py-3.5 font-semibold">Started At</th>
                <th className="px-6 py-3.5 font-semibold">Duration</th>
                <th className="px-6 py-3.5 text-right font-semibold">State</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
              {recentSessions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-sm text-slate-400">
                    No active sessions currently streaming.
                  </td>
                </tr>
              ) : (
                paginatedRecentSessions.map((session) => (
                  <tr key={session.radacctid} className="transition hover:bg-slate-800/40">
                    <td className="px-6 py-4 font-semibold text-slate-100">
                      {session.username || 'Unknown'}
                    </td>
                    <td className="font-mono px-6 py-4 text-xs text-slate-300">
                      {session.nasipaddress || 'N/A'}
                    </td>
                    <td className="font-mono px-6 py-4 text-xs text-cyan-400">
                      {session.framedipaddress || 'Dynamic'}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {session.acctstarttime ? new Date(session.acctstarttime).toLocaleString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 text-xs font-semibold text-slate-300">
                      {formatDuration(session.acctsessiontime)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <StatusBadge status="online" size="small" />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {recentSessions.length > pageSize && (
          <div className="border-t border-slate-800/80 px-6 py-4">
            <PaginationControls page={page} totalPages={totalPages} onPageChange={setPage} />
          </div>
        )}
      </div>
    </div>
  );
};

const KpiCard = ({ title, value, subtext, icon, tone }) => {
  const glowStyles = {
    cyan: 'hover:border-cyan-500/30 hover:shadow-cyan-500/10',
    emerald: 'hover:border-emerald-500/30 hover:shadow-emerald-500/10',
    violet: 'hover:border-violet-500/30 hover:shadow-violet-500/10',
    amber: 'hover:border-amber-500/30 hover:shadow-amber-500/10',
  };

  const bgStyles = {
    cyan: 'bg-cyan-500/10 border-cyan-500/20',
    emerald: 'bg-emerald-500/10 border-emerald-500/20',
    violet: 'bg-violet-500/10 border-violet-500/20',
    amber: 'bg-amber-500/10 border-amber-500/20',
  };

  return (
    <div className={`glass-card rounded-3xl p-6 transition-all duration-300 hover:-translate-y-1 ${glowStyles[tone]}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">{title}</span>
        <div className={`flex h-11 w-11 items-center justify-center rounded-2xl border ${bgStyles[tone]}`}>
          {icon}
        </div>
      </div>
      <p className="font-display mt-4 text-3xl font-extrabold text-slate-100">{value}</p>
      <p className="mt-1 text-xs text-slate-400">{subtext}</p>
    </div>
  );
};

export default Dashboard;