import React, { useEffect, useMemo, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/authState';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import PaginationControls from '../components/PaginationControls';
import { TableSkeleton } from '../components/Skeletons';
import api from '../services/api';

const Sessions = () => {
  const { user } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [staleSessions, setStaleSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('active'); // 'active' or 'stale'
  const [activePage, setActivePage] = useState(1);
  const [stalePage, setStalePage] = useState(1);
  const pageSize = 8;

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const [sessionsRes, staleRes] = await Promise.all([
        api.get('/sessions'),
        api.get('/sessions/stale').catch(() => ({ data: [] })),
      ]);
      setSessions(Array.isArray(sessionsRes.data) ? sessionsRes.data : []);
      setStaleSessions(Array.isArray(staleRes.data) ? staleRes.data : []);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
      setError('Failed to load accounting sessions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const activeTotalPages = Math.max(1, Math.ceil(sessions.length / pageSize));
  const staleTotalPages = Math.max(1, Math.ceil(staleSessions.length / pageSize));

  const paginatedActiveSessions = useMemo(
    () => sessions.slice((activePage - 1) * pageSize, activePage * pageSize),
    [sessions, activePage],
  );

  const paginatedStaleSessions = useMemo(
    () => staleSessions.slice((stalePage - 1) * pageSize, stalePage * pageSize),
    [staleSessions, stalePage],
  );

  useEffect(() => {
    setActivePage((current) => Math.min(current, activeTotalPages));
  }, [activeTotalPages]);

  useEffect(() => {
    setStalePage((current) => Math.min(current, staleTotalPages));
  }, [staleTotalPages]);

  const handleCleanupStale = async () => {
    if (window.confirm('Are you sure you want to clean up all stale sessions? This will close all orphaned radacct entries.')) {
      try {
        const response = await api.post('/sessions/cleanup/stale');
        alert(`Cleaned up ${response.data.cleaned} stale sessions`);
        await fetchSessions();
      } catch (err) {
        console.error('Failed to cleanup stale sessions:', err);
        setError('Failed to clean up stale sessions');
      }
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds && seconds !== 0) return '0s';
    const totalSeconds = Number(seconds);
    if (Number.isNaN(totalSeconds)) return '0s';

    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const remainingSeconds = totalSeconds % 60;

    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${remainingSeconds}s`;
    return `${remainingSeconds}s`;
  };

  const formatMB = (octets) => {
    if (!octets) return '0.00 MB';
    return `${(octets / 1024 / 1024).toFixed(2)} MB`;
  };

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Subscriber Telemetry"
        title="Active Accounting Sessions"
        description="Monitor ongoing RADIUS accounting streams (radacct) and identify stale or orphaned sessions."
        actions={
          <div className="flex items-center gap-3">
            <div className="flex rounded-2xl border border-slate-800 bg-slate-900/80 p-1">
              <button
                onClick={() => setActiveTab('active')}
                className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                  activeTab === 'active'
                    ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Active ({sessions.length})
              </button>
              <button
                onClick={() => setActiveTab('stale')}
                className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                  activeTab === 'stale'
                    ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Stale ({staleSessions.length})
              </button>
            </div>

            {activeTab === 'stale' && staleSessions.length > 0 && (
              <button
                onClick={handleCleanupStale}
                className="rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-2 text-xs font-semibold text-amber-400 transition hover:bg-amber-500/20"
              >
                Clean Stale ({staleSessions.length})
              </button>
            )}
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

      {/* Tab Panels */}
      <div className="glass-panel overflow-hidden rounded-3xl shadow-xl">
        {activeTab === 'active' ? (
          <>
            <div className="flex items-center justify-between border-b border-slate-800/80 px-6 py-4">
              <h2 className="font-display text-base font-bold text-slate-100">Live Active Streams</h2>
              <span className="text-xs text-slate-400">Page {activePage} of {activeTotalPages}</span>
            </div>

            {loading ? (
              <TableSkeleton rows={5} columns={6} compact />
            ) : sessions.length === 0 ? (
              <div className="py-16 text-center text-sm text-slate-400">
                No active subscriber sessions found.
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-slate-800/80 bg-slate-900/60 text-xs uppercase tracking-wider text-slate-400">
                      <tr>
                        <th className="px-6 py-3.5 font-semibold">Subscriber</th>
                        <th className="px-6 py-3.5 font-semibold">NAS Gateway</th>
                        <th className="px-6 py-3.5 font-semibold">Framed IP</th>
                        <th className="px-6 py-3.5 font-semibold">Session Start</th>
                        <th className="px-6 py-3.5 font-semibold">Duration</th>
                        <th className="px-6 py-3.5 font-semibold">Download / Upload</th>
                        <th className="px-6 py-3.5 text-right font-semibold">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
                      {paginatedActiveSessions.map((session) => (
                        <tr key={session.radacctid} className="transition hover:bg-slate-800/40">
                          <td className="px-6 py-4 font-semibold text-slate-100">{session.username || 'Unknown'}</td>
                          <td className="font-mono px-6 py-4 text-xs text-slate-300">{session.nasipaddress || 'N/A'}</td>
                          <td className="font-mono px-6 py-4 text-xs text-cyan-400">{session.framedipaddress || 'Dynamic'}</td>
                          <td className="px-6 py-4 text-xs text-slate-400">
                            {session.acctstarttime ? new Date(session.acctstarttime).toLocaleString() : 'N/A'}
                          </td>
                          <td className="px-6 py-4 text-xs font-semibold text-slate-300">
                            {formatDuration(session.acctsessiontime)}
                          </td>
                          <td className="font-mono px-6 py-4 text-xs text-slate-300">
                            {`${formatMB(session.acctinputoctets)} ↓ / ${formatMB(session.acctoutputoctets)} ↑`}
                          </td>
                          <td className="px-6 py-4 text-right">
                            <StatusBadge status="online" size="small" />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {activeTotalPages > 1 && (
                  <div className="border-t border-slate-800/80 px-6 py-4">
                    <PaginationControls page={activePage} totalPages={activeTotalPages} onPageChange={setActivePage} />
                  </div>
                )}
              </>
            )}
          </>
        ) : (
          <>
            <div className="flex items-center justify-between border-b border-slate-800/80 px-6 py-4">
              <div>
                <h2 className="font-display text-base font-bold text-amber-400">Stale Session Detection</h2>
                <p className="text-xs text-slate-400">Sessions inactive for over 2 hours without stop packet.</p>
              </div>
              {staleSessions.length > 0 && (
                <button
                  onClick={handleCleanupStale}
                  className="rounded-xl bg-amber-500 px-4 py-2 text-xs font-bold text-slate-950 transition hover:bg-amber-400"
                >
                  Clean All Stale ({staleSessions.length})
                </button>
              )}
            </div>

            {loading ? (
              <TableSkeleton rows={5} columns={5} compact />
            ) : staleSessions.length === 0 ? (
              <div className="py-16 text-center text-sm text-emerald-400 font-semibold">
                No stale or orphaned sessions detected.
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-slate-800/80 bg-slate-900/60 text-xs uppercase tracking-wider text-slate-400">
                      <tr>
                        <th className="px-6 py-3.5 font-semibold">Subscriber</th>
                        <th className="px-6 py-3.5 font-semibold">NAS Gateway</th>
                        <th className="px-6 py-3.5 font-semibold">Session Start</th>
                        <th className="px-6 py-3.5 font-semibold">Duration</th>
                        <th className="px-6 py-3.5 text-right font-semibold">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
                      {paginatedStaleSessions.map((session) => (
                        <tr key={session.radacctid} className="transition hover:bg-slate-800/40">
                          <td className="px-6 py-4 font-semibold text-slate-100">{session.username || 'Unknown'}</td>
                          <td className="font-mono px-6 py-4 text-xs text-slate-300">{session.nasipaddress}</td>
                          <td className="px-6 py-4 text-xs text-slate-400">
                            {session.acctstarttime ? new Date(session.acctstarttime).toLocaleString() : 'N/A'}
                          </td>
                          <td className="px-6 py-4 text-xs font-semibold text-amber-400">
                            {formatDuration(session.acctsessiontime)}
                          </td>
                          <td className="px-6 py-4 text-right">
                            <StatusBadge status="expired" customLabel="Stale" size="small" />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {staleTotalPages > 1 && (
                  <div className="border-t border-slate-800/80 px-6 py-4">
                    <PaginationControls page={stalePage} totalPages={staleTotalPages} onPageChange={setStalePage} />
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Sessions;