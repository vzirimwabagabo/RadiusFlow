import React, { useEffect, useMemo, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/authState';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import PaginationControls from '../components/PaginationControls';
import { TableSkeleton } from '../components/Skeletons';
import api from '../services/api';

const AuthLogs = () => {
  const { user } = useAuth();
  const [logs, setLogs] = useState([]);
  const [failedCount, setFailedCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        setLoading(true);
        const [logsResponse, failedResponse] = await Promise.all([
          api.get('/logs/auth?limit=100'),
          api.get('/logs/failed-attempts'),
        ]);
        setLogs(Array.isArray(logsResponse.data) ? logsResponse.data : []);
        setFailedCount(failedResponse.data?.failed_count || 0);
      } catch (err) {
        console.error('Failed to load authentication logs:', err);
        setError('Failed to load authentication log stream');
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
  }, []);

  const filteredLogs = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return logs;
    return logs.filter(
      (item) =>
        (item.username && item.username.toLowerCase().includes(query)) ||
        (item.reply && item.reply.toLowerCase().includes(query)) ||
        (item.callingstationid && item.callingstationid.toLowerCase().includes(query)) ||
        (item.calledstationid && item.calledstationid.toLowerCase().includes(query)),
    );
  }, [logs, search]);

  const totalPages = Math.max(1, Math.ceil(filteredLogs.length / pageSize));
  const paginatedLogs = useMemo(
    () => filteredLogs.slice((page - 1) * pageSize, page * pageSize),
    [filteredLogs, page],
  );

  useEffect(() => {
    setPage(1);
  }, [search]);

  useEffect(() => {
    setPage((current) => Math.min(current, totalPages));
  }, [totalPages]);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Security & Access Control"
        title="Authentication Log Telemetry"
        description="Streamed subscriber access logs from FreeRADIUS post-auth history (radpostauth)."
      />

      {error && (
        <div className="flex items-center gap-3 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs font-semibold text-rose-300">
          <svg className="h-5 w-5 text-rose-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <div className="glass-card rounded-3xl p-6 transition hover:border-cyan-500/30">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Streamed Events</span>
          <p className="font-display mt-3 text-3xl font-extrabold text-slate-100">{logs.length}</p>
          <p className="mt-1 text-xs text-slate-400">Recent radpostauth records</p>
        </div>

        <div className="glass-card rounded-3xl p-6 transition hover:border-rose-500/30">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Failed Attempts</span>
          <p className="font-display mt-3 text-3xl font-extrabold text-rose-400">{failedCount}</p>
          <p className="mt-1 text-xs text-slate-400">Access-Reject responses</p>
        </div>

        <div className="glass-card rounded-3xl p-6 transition hover:border-emerald-500/30">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Success Rate</span>
          <p className="font-display mt-3 text-3xl font-extrabold text-emerald-400">
            {logs.length > 0
              ? `${(
                  ((logs.length - failedCount) / logs.length) *
                  100
                ).toFixed(1)}%`
              : '100%'}
          </p>
          <p className="mt-1 text-xs text-slate-400">Accepted vs Rejected ratio</p>
        </div>
      </div>

      {/* Log Table Panel */}
      <div className="glass-panel overflow-hidden rounded-3xl shadow-xl">
        <div className="flex flex-col gap-4 border-b border-slate-800/80 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="font-display text-lg font-bold text-slate-100">Live Auth Events</h2>
            <p className="text-xs text-slate-400">{filteredLogs.length} matching events</p>
          </div>
          <div className="w-full sm:w-64">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search user, result, station MAC..."
              className="w-full rounded-2xl border border-slate-800 bg-slate-950/80 px-4 py-2 text-xs text-slate-200 placeholder-slate-500 outline-none transition focus:border-cyan-500"
            />
          </div>
        </div>

        {loading ? (
          <TableSkeleton rows={8} columns={5} compact />
        ) : filteredLogs.length === 0 ? (
          <div className="py-16 text-center text-sm text-slate-400">
            No authentication logs found matching query.
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-800/80 bg-slate-900/60 text-xs uppercase tracking-wider text-slate-400">
                  <tr>
                    <th className="px-6 py-3.5 font-semibold">Subscriber</th>
                    <th className="px-6 py-3.5 font-semibold">Response</th>
                    <th className="px-6 py-3.5 font-semibold">Timestamp</th>
                    <th className="px-6 py-3.5 font-semibold">Calling Station (MAC / Client)</th>
                    <th className="px-6 py-3.5 font-semibold">Called Station (SSID / Gateway)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
                  {paginatedLogs.map((log, idx) => {
                    const isAccept = log.reply === 'Access-Accept';
                    return (
                      <tr key={log.id || `${log.username}-${idx}`} className="transition hover:bg-slate-800/40">
                        <td className="px-6 py-4 font-semibold text-slate-100">{log.username || 'Unknown'}</td>
                        <td className="px-6 py-4">
                          <StatusBadge
                            status={isAccept ? 'healthy' : 'blocked'}
                            customLabel={log.reply || 'Unknown'}
                            size="small"
                          />
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-400">
                          {log.authdate ? new Date(log.authdate).toLocaleString() : 'N/A'}
                        </td>
                        <td className="font-mono px-6 py-4 text-xs text-slate-300">
                          {log.callingstationid || 'N/A'}
                        </td>
                        <td className="font-mono px-6 py-4 text-xs text-slate-300">
                          {log.calledstationid || 'N/A'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="border-t border-slate-800/80 px-6 py-4">
                <PaginationControls page={page} totalPages={totalPages} onPageChange={setPage} />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AuthLogs;