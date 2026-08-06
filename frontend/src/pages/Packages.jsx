import React, { useEffect, useMemo, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/authState';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import PaginationControls from '../components/PaginationControls';
import { TableSkeleton } from '../components/Skeletons';
import api from '../services/api';
import { buildPackagePayload } from '../utils/formPayloads';

const EMPTY_FORM = {
  groupname: '',
  rate_limit: '',
  session_timeout: '',
  max_down: '',
  max_up: '',
  idle_timeout: '',
};

const PAGE_SIZE = 8;

const Packages = () => {
  const { user } = useAuth();
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [editMode, setEditMode] = useState(false);
  const [editingPackageId, setEditingPackageId] = useState(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    const fetchPackages = async () => {
      try {
        setLoading(true);
        const response = await api.get('/groups');
        setPackages(Array.isArray(response.data) ? response.data : []);
      } catch (err) {
        console.error('Failed to fetch packages:', err);
        setError('Failed to load packages');
      } finally {
        setLoading(false);
      }
    };

    fetchPackages();
  }, []);

  const filteredPackages = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return packages;
    return packages.filter(
      (pkg) =>
        (pkg.groupname && pkg.groupname.toLowerCase().includes(query)) ||
        (pkg.rate_limit && pkg.rate_limit.toLowerCase().includes(query)),
    );
  }, [packages, search]);

  const totalPages = Math.max(1, Math.ceil(filteredPackages.length / PAGE_SIZE));
  const paginatedPackages = useMemo(
    () => filteredPackages.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [filteredPackages, page],
  );

  useEffect(() => {
    setPage(1);
  }, [search]);

  useEffect(() => {
    setPage((current) => Math.min(current, totalPages));
  }, [totalPages]);

  const resetForm = () => {
    setFormData(EMPTY_FORM);
    setEditMode(false);
    setEditingPackageId(null);
    setShowForm(false);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const refreshPackages = async () => {
    const response = await api.get('/groups');
    setPackages(Array.isArray(response.data) ? response.data : []);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = buildPackagePayload(formData);
      if (editMode && editingPackageId) {
        await api.put(`/groups/${editingPackageId}`, payload);
      } else {
        await api.post('/groups', payload);
      }
      setError('');
      resetForm();
      await refreshPackages();
    } catch (err) {
      console.error('Failed to save package:', err);
      setError('Failed to save package');
    }
  };

  const handleEditPackage = (pkg) => {
    setEditMode(true);
    setEditingPackageId(pkg.groupname);
    setFormData({
      groupname: pkg.groupname,
      rate_limit: pkg.rate_limit || '',
      session_timeout: pkg.session_timeout ? pkg.session_timeout.toString() : '',
      max_down: pkg.max_down ? pkg.max_down.toString() : '',
      max_up: pkg.max_up ? pkg.max_up.toString() : '',
      idle_timeout: pkg.idle_timeout ? pkg.idle_timeout.toString() : '',
    });
    setShowForm(true);
  };

  const handleDeletePackage = async (groupname) => {
    if (window.confirm(`Are you sure you want to delete package ${groupname}?`)) {
      try {
        await api.delete(`/groups/${groupname}`);
        setPackages((prev) => prev.filter((pkg) => pkg.groupname !== groupname));
      } catch (err) {
        console.error('Failed to delete package:', err);
        setError('Failed to delete package');
      }
    }
  };

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Services & Policies"
        title="Package Policy Profiles"
        description="Manage FreeRADIUS reply profiles (radgroupcheck, radgroupreply) for bandwidth limits and timeouts."
        actions={
          <button
            onClick={() => {
              resetForm();
              setShowForm(true);
            }}
            className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-500 to-violet-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-cyan-500/20 transition hover:brightness-110"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Add New Package</span>
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

      <div className="grid gap-6 lg:grid-cols-[1fr_350px]">
        {/* Table & Filters Column */}
        <div className="space-y-6">
          <div className="glass-panel overflow-hidden rounded-3xl shadow-xl">
            <div className="flex flex-col gap-4 border-b border-slate-800/80 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="font-display text-lg font-bold text-slate-100">Package Profiles ({filteredPackages.length})</h2>
                <p className="text-xs text-slate-400">Page {page} of {totalPages}</p>
              </div>
              <div className="w-full sm:w-64">
                <input
                  type="search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search package name or rate limit..."
                  className="w-full rounded-2xl border border-slate-800 bg-slate-950/80 px-4 py-2 text-xs text-slate-200 placeholder-slate-500 outline-none transition focus:border-cyan-500"
                />
              </div>
            </div>

            {loading ? (
              <TableSkeleton rows={6} columns={6} compact />
            ) : filteredPackages.length === 0 ? (
              <div className="py-16 text-center text-sm text-slate-400">
                No package profiles found matching query.
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-slate-800/80 bg-slate-900/60 text-xs uppercase tracking-wider text-slate-400">
                      <tr>
                        <th className="px-6 py-3.5 font-semibold">Package Name</th>
                        <th className="px-6 py-3.5 font-semibold">Rate Limit</th>
                        <th className="px-6 py-3.5 font-semibold">Max Down/Up (kbps)</th>
                        <th className="px-6 py-3.5 font-semibold">Session Timeout</th>
                        <th className="px-6 py-3.5 font-semibold">Assigned Users</th>
                        <th className="px-6 py-3.5 text-right font-semibold">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
                      {paginatedPackages.map((pkg) => (
                        <tr key={pkg.groupname} className="transition hover:bg-slate-800/40">
                          <td className="px-6 py-4 font-semibold text-slate-100">{pkg.groupname}</td>
                          <td className="font-mono px-6 py-4 text-xs text-cyan-400">{pkg.rate_limit || 'Unlimited'}</td>
                          <td className="font-mono px-6 py-4 text-xs text-slate-300">
                            {pkg.max_down || pkg.max_up ? `${pkg.max_down || '∞'} / ${pkg.max_up || '∞'}` : 'Default'}
                          </td>
                          <td className="px-6 py-4 text-xs text-slate-400">
                            {pkg.session_timeout ? `${pkg.session_timeout}s` : 'Unlimited'}
                          </td>
                          <td className="px-6 py-4 text-xs font-semibold text-slate-200">
                            {pkg.user_count || 0} subscribers
                          </td>
                          <td className="px-6 py-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => handleEditPackage(pkg)}
                                className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1 text-xs font-semibold text-cyan-400 hover:border-cyan-500/40"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleDeletePackage(pkg.groupname)}
                                className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-1 text-xs font-semibold text-rose-400 hover:bg-rose-500/20"
                              >
                                Delete
                              </button>
                            </div>
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

        {/* Form Panel */}
        {(showForm || editMode) && (
          <div className="glass-panel h-fit rounded-3xl p-6 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
              <h3 className="font-display text-base font-bold text-slate-100">
                {editMode ? 'Edit Package Profile' : 'New Package Profile'}
              </h3>
              <button onClick={resetForm} className="text-slate-400 hover:text-slate-200">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Package Name</label>
                <input
                  type="text"
                  name="groupname"
                  required
                  disabled={editMode}
                  value={formData.groupname}
                  onChange={handleChange}
                  placeholder="e.g. 10M_Unlimited"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500 disabled:opacity-50"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">MikroTik Rate Limit</label>
                <input
                  type="text"
                  name="rate_limit"
                  value={formData.rate_limit}
                  onChange={handleChange}
                  placeholder="e.g. 10M/10M"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Session Timeout (secs)</label>
                <input
                  type="number"
                  name="session_timeout"
                  value={formData.session_timeout}
                  onChange={handleChange}
                  placeholder="3600"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">WISPr Max Download (kbps)</label>
                <input
                  type="number"
                  name="max_down"
                  value={formData.max_down}
                  onChange={handleChange}
                  placeholder="10240"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">WISPr Max Upload (kbps)</label>
                <input
                  type="number"
                  name="max_up"
                  value={formData.max_up}
                  onChange={handleChange}
                  placeholder="10240"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Idle Timeout (secs)</label>
                <input
                  type="number"
                  name="idle_timeout"
                  value={formData.idle_timeout}
                  onChange={handleChange}
                  placeholder="600"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                />
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  type="button"
                  onClick={resetForm}
                  className="w-1/2 rounded-xl border border-slate-800 px-3 py-2 text-xs font-semibold text-slate-400 hover:bg-slate-900"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="w-1/2 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 px-3 py-2 text-xs font-bold text-white shadow-lg shadow-cyan-500/20 hover:brightness-110"
                >
                  {editMode ? 'Save Policy' : 'Create Package'}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default Packages;