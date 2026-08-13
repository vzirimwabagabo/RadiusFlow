import React, { useEffect, useMemo, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/authState';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import PaginationControls from '../components/PaginationControls';
import { TableSkeleton } from '../components/Skeletons';
import api from '../services/api';

const PAGE_SIZE = 8;

const Vouchers = () => {
  const { user } = useAuth();
  const [vouchers, setVouchers] = useState([]);
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);

  // Generator modal state
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [generateData, setGenerateData] = useState({
    count: 10,
    group_name: '',
    expires_in_days: 30,
  });

  // Redemption modal state
  const [showRedeemModal, setShowRedeemModal] = useState(false);
  const [redeemData, setRedeemData] = useState({ code: '', username: '' });
  const [copiedCode, setCopiedCode] = useState('');

  useEffect(() => {
    fetchVouchers();
    fetchPackages();
  }, []);

  const fetchVouchers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/vouchers');
      setVouchers(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      console.error('Failed to load vouchers:', err);
      setError('Failed to load vouchers');
    } finally {
      setLoading(false);
    }
  };

  const fetchPackages = async () => {
    try {
      const response = await api.get('/groups');
      setPackages(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      console.error('Failed to fetch packages:', err);
    }
  };

  const filteredVouchers = useMemo(() => {
    const query = search.trim().toLowerCase();
    return vouchers.filter((v) => {
      const matchesQuery =
        !query ||
        v.code.toLowerCase().includes(query) ||
        (v.group_name && v.group_name.toLowerCase().includes(query)) ||
        (v.used_by && v.used_by.toLowerCase().includes(query));
      const matchesStatus = statusFilter === 'all' || v.status === statusFilter;
      return matchesQuery && matchesStatus;
    });
  }, [vouchers, search, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredVouchers.length / PAGE_SIZE));
  const paginatedVouchers = useMemo(
    () => filteredVouchers.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [filteredVouchers, page],
  );

  useEffect(() => {
    setPage(1);
  }, [search, statusFilter]);

  const handleGenerate = async (e) => {
    e.preventDefault();
    try {
      await api.post('/vouchers/generate', generateData);
      setShowGenerateModal(false);
      await fetchVouchers();
    } catch (err) {
      console.error('Failed to generate vouchers:', err);
      setError('Failed to batch generate vouchers');
    }
  };

  const handleRedeem = async (e) => {
    e.preventDefault();
    try {
      await api.post('/vouchers/redeem', redeemData);
      setShowRedeemModal(false);
      setRedeemData({ code: '', username: '' });
      await fetchVouchers();
    } catch (err) {
      console.error('Failed to redeem voucher:', err);
      setError(err.response?.data?.detail || 'Failed to redeem voucher');
    }
  };

  const handleDelete = async (code) => {
    if (window.confirm(`Delete voucher ${code}?`)) {
      try {
        await api.delete(`/vouchers/${code}`);
        setVouchers((prev) => prev.filter((v) => v.code !== code));
      } catch (err) {
        console.error('Failed to delete voucher:', err);
        setError('Failed to delete voucher');
      }
    }
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(''), 2000);
  };

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const unusedCount = vouchers.filter((v) => v.status === 'unused').length;
  const usedCount = vouchers.filter((v) => v.status === 'used').length;

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Hotspot & Voucher Sales"
        title="Voucher Batch Management"
        description="Batch generate, print, and redeem access vouchers linked to service package bandwidth profiles."
        actions={
          <div className="flex gap-3">
            <button
              onClick={() => setShowRedeemModal(true)}
              className="rounded-2xl border border-cyan-500/30 bg-cyan-500/10 px-4 py-2.5 text-xs font-bold text-cyan-300 hover:bg-cyan-500/20 transition"
            >
              Redeem Voucher
            </button>
            <button
              onClick={() => setShowGenerateModal(true)}
              className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-500 to-violet-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-cyan-500/20 transition hover:brightness-110"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>Batch Generate Vouchers</span>
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

      {/* KPI Cards */}
      <div className="grid gap-5 sm:grid-cols-3">
        <div className="glass-card rounded-3xl p-6 border-l-4 border-l-cyan-500">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Vouchers</span>
          <p className="font-display mt-2 text-3xl font-extrabold text-slate-100">{vouchers.length}</p>
        </div>
        <div className="glass-card rounded-3xl p-6 border-l-4 border-l-emerald-500">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Unused / Ready</span>
          <p className="font-display mt-2 text-3xl font-extrabold text-emerald-400">{unusedCount}</p>
        </div>
        <div className="glass-card rounded-3xl p-6 border-l-4 border-l-violet-500">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Redeemed</span>
          <p className="font-display mt-2 text-3xl font-extrabold text-violet-400">{usedCount}</p>
        </div>
      </div>

      {/* Main Table Panel */}
      <div className="glass-panel overflow-hidden rounded-3xl shadow-xl">
        <div className="flex flex-col gap-4 border-b border-slate-800/80 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="font-display text-lg font-bold text-slate-100">Voucher Inventory ({filteredVouchers.length})</h2>
            <p className="text-xs text-slate-400">Page {page} of {totalPages}</p>
          </div>
          <div className="flex gap-3">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-2xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
            >
              <option value="all">All Statuses</option>
              <option value="unused">Unused</option>
              <option value="used">Used</option>
            </select>
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search code or package..."
              className="w-full sm:w-48 rounded-2xl border border-slate-800 bg-slate-950/80 px-4 py-2 text-xs text-slate-200 placeholder-slate-500 outline-none transition focus:border-cyan-500"
            />
          </div>
        </div>

        {loading ? (
          <TableSkeleton rows={6} columns={6} compact />
        ) : filteredVouchers.length === 0 ? (
          <div className="py-16 text-center text-sm text-slate-400">No vouchers generated yet. Click "Batch Generate Vouchers" to start.</div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-800/80 bg-slate-900/60 text-xs uppercase tracking-wider text-slate-400">
                  <tr>
                    <th className="px-6 py-3.5 font-semibold">Voucher Code</th>
                    <th className="px-6 py-3.5 font-semibold">Package Profile</th>
                    <th className="px-6 py-3.5 font-semibold">Status</th>
                    <th className="px-6 py-3.5 font-semibold">Used By</th>
                    <th className="px-6 py-3.5 font-semibold">Expiration</th>
                    <th className="px-6 py-3.5 text-right font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
                  {paginatedVouchers.map((v) => (
                    <tr key={v.id} className="transition hover:bg-slate-800/40">
                      <td className="px-6 py-4 font-mono font-bold text-cyan-300">
                        {v.code}
                        <button
                          onClick={() => copyCode(v.code)}
                          className="ml-2 text-[10px] text-slate-400 hover:text-cyan-400"
                          title="Copy voucher code"
                        >
                          {copiedCode === v.code ? '✓ Copied' : '📋'}
                        </button>
                      </td>
                      <td className="px-6 py-4 text-xs font-semibold text-slate-200">{v.group_name || 'Standard'}</td>
                      <td className="px-6 py-4">
                        <StatusBadge
                          status={v.status === 'unused' ? 'healthy' : 'offline'}
                          customLabel={v.status === 'unused' ? 'Unused' : 'Used'}
                          size="small"
                        />
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-300">{v.used_by || '—'}</td>
                      <td className="px-6 py-4 text-xs text-slate-400">
                        {v.expires_at ? new Date(v.expires_at).toLocaleDateString() : 'Never'}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => handleDelete(v.code)}
                          className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-1 text-xs font-semibold text-rose-400 hover:bg-rose-500/20"
                        >
                          Delete
                        </button>
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

      {/* Batch Generate Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="glass-panel w-full max-w-md rounded-3xl p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
              <h3 className="font-display text-base font-bold text-slate-100">Batch Generate Vouchers</h3>
              <button onClick={() => setShowGenerateModal(false)} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>
            <form onSubmit={handleGenerate} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Quantity to Generate</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={generateData.count}
                  onChange={(e) => setGenerateData({ ...generateData, count: parseInt(e.target.value) || 1 })}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Package Policy Profile</label>
                <select
                  value={generateData.group_name}
                  onChange={(e) => setGenerateData({ ...generateData, group_name: e.target.value })}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                >
                  <option value="">Standard Default</option>
                  {packages.map((pkg) => (
                    <option key={pkg.groupname} value={pkg.groupname}>
                      {pkg.groupname} ({pkg.rate_limit || 'Unlimited'})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Validity (Days)</label>
                <input
                  type="number"
                  min="1"
                  max="365"
                  value={generateData.expires_in_days}
                  onChange={(e) => setGenerateData({ ...generateData, expires_in_days: parseInt(e.target.value) || 30 })}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                />
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowGenerateModal(false)}
                  className="w-1/2 rounded-xl border border-slate-800 px-3 py-2 text-xs font-semibold text-slate-400 hover:bg-slate-900"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="w-1/2 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 px-3 py-2 text-xs font-bold text-white shadow-lg shadow-cyan-500/20 hover:brightness-110"
                >
                  Generate {generateData.count} Vouchers
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Redeem Modal */}
      {showRedeemModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="glass-panel w-full max-w-md rounded-3xl p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
              <h3 className="font-display text-base font-bold text-slate-100">Redeem Voucher Code</h3>
              <button onClick={() => setShowRedeemModal(false)} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>
            <form onSubmit={handleRedeem} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Voucher Code</label>
                <input
                  type="text"
                  required
                  value={redeemData.code}
                  onChange={(e) => setRedeemData({ ...redeemData, code: e.target.value })}
                  placeholder="RF-XXXX-XXXX"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 font-mono text-xs text-cyan-300 outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Target Subscriber Username</label>
                <input
                  type="text"
                  required
                  value={redeemData.username}
                  onChange={(e) => setRedeemData({ ...redeemData, username: e.target.value })}
                  placeholder="subscriber_name"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                />
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowRedeemModal(false)}
                  className="w-1/2 rounded-xl border border-slate-800 px-3 py-2 text-xs font-semibold text-slate-400 hover:bg-slate-900"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="w-1/2 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 px-3 py-2 text-xs font-bold text-white shadow-lg shadow-cyan-500/20 hover:brightness-110"
                >
                  Apply Voucher
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Vouchers;
