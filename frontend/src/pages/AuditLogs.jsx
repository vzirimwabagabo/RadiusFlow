import React, { useEffect, useMemo, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/authState';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import PaginationControls from '../components/PaginationControls';
import { TableSkeleton } from '../components/Skeletons';
import api from '../services/api';

const PAGE_SIZE = 10;

const AuditLogs = () => {
  const { user } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  useEffect(() => {
    const fetchAuditLogs = async () => {
      try {
        setLoading(true);
        const response = await api.get('/audit-logs?limit=200');
        setLogs(Array.isArray(response.data) ? response.data : []);
      } catch (err) {
        console.error('Failed to load audit logs:', err);
        setError('Failed to load system audit trail');
      } finally {
        setLoading(false);
      }
    };

    fetchAuditLogs();
  }, []);

  const filteredLogs = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return logs;
    return logs.filter(
      (log) =>
        (log.action && log.action.toLowerCase().includes(query)) ||
        (log.actor && log.actor.toLowerCase().includes(query)) ||
        (log.details && log.details.toLowerCase().includes(query)) ||
        (log.resource_id && log.resource_id.toLowerCase().includes(query)),
    );
  }, [logs, search]);

  const totalPages = Math.max(1, Math.ceil(filteredLogs.length / PAGE_SIZE));
  const paginatedLogs = useMemo(
    () => filteredLogs.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [filteredLogs, page],
  );

  useEffect(() => {
    setPage(1);
  }, [search]);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        badge="System Auditability"
        title="System Action Audit Logs"
        description="Comprehensive audit trail of administrator actions, user provisioning, policy changes, and security events."
      />

      {error && (
        <div className="flex items-center gap-3 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs font-semibold text-rose-300">
          <svg className="h-5 w-5 text-rose-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Audit Log Table Panel */}
      <div className="glass-panel overflow-hidden rounded-3xl shadow-xl">
        <div className="flex flex-col gap-4 border-b border-slate-800/80 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="font-display text-lg font-bold text-slate-100">Audit Trail ({filteredLogs.length})</h2>
            <p className="text-xs text-slate-400">Page {page} of {totalPages}</p>
          </div>
          <div className="w-full sm:w-64">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search action, actor, resource..."
              className="w-full rounded-2xl border border-slate-800 bg-slate-950/80 px-4 py-2 text-xs text-slate-200 placeholder-slate-500 outline-none transition focus:border-cyan-500"
            />
          </div>
        </div>

        {loading ? (
          <TableSkeleton rows={8} columns={5} compact />
        ) : filteredLogs.length === 0 ? (
          <div className="py-16 text-center text-sm text-slate-400">No system audit records found.</div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-800/80 bg-slate-900/60 text-xs uppercase tracking-wider text-slate-400">
                  <tr>
                    <th className="px-6 py-3.5 font-semibold">Action</th>
                    <th className="px-6 py-3.5 font-semibold">Operator / Actor</th>
                    <th className="px-6 py-3.5 font-semibold">Resource</th>
                    <th className="px-6 py-3.5 font-semibold">Details</th>
                    <th className="px-6 py-3.5 font-semibold">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
                  {paginatedLogs.map((log) => (
                    <tr key={log.id} className="transition hover:bg-slate-800/40">
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-1 font-mono text-xs font-bold text-cyan-300">
                          {log.action}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-xs font-semibold text-slate-200">{log.actor || 'System'}</td>
                      <td className="px-6 py-4 text-xs text-slate-300">
                        {log.resource_type ? `${log.resource_type}: ${log.resource_id || ''}` : 'N/A'}
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-400 max-w-xs truncate">{log.details || 'N/A'}</td>
                      <td className="px-6 py-4 text-xs text-slate-400">
                        {log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}
                      </td>
                    </tr>
                  ))}
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

export default AuditLogs;
