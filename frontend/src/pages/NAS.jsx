import React, { useEffect, useMemo, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/authState';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import PaginationControls from '../components/PaginationControls';
import { TableSkeleton } from '../components/Skeletons';
import api from '../services/api';
import { buildNasPayload } from '../utils/formPayloads';

const EMPTY_FORM = {
  nasname: '',
  shortname: '',
  type: 'mikrotik',
  secret: '',
  ports: '1812',
  server: '',
  community: '',
  description: '',
};

const PAGE_SIZE = 8;

const NASManagement = () => {
  const { user } = useAuth();
  const [nasDevices, setNasDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [editMode, setEditMode] = useState(false);
  const [editingNasId, setEditingNasId] = useState(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    const fetchNasDevices = async () => {
      try {
        setLoading(true);
        const response = await api.get('/nas');
        setNasDevices(Array.isArray(response.data) ? response.data : []);
      } catch (err) {
        console.error('Failed to fetch NAS devices:', err);
        setError('Failed to load NAS gateways');
      } finally {
        setLoading(false);
      }
    };

    fetchNasDevices();
  }, []);

  const filteredNasDevices = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return nasDevices;
    return nasDevices.filter(
      (nas) =>
        (nas.nasname && nas.nasname.toLowerCase().includes(query)) ||
        (nas.shortname && nas.shortname.toLowerCase().includes(query)) ||
        (nas.type && nas.type.toLowerCase().includes(query)),
    );
  }, [nasDevices, search]);

  const totalPages = Math.max(1, Math.ceil(filteredNasDevices.length / PAGE_SIZE));
  const paginatedNasDevices = useMemo(
    () => filteredNasDevices.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [filteredNasDevices, page],
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
    setEditingNasId(null);
    setShowForm(false);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const refreshNas = async () => {
    const response = await api.get('/nas');
    setNasDevices(Array.isArray(response.data) ? response.data : []);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = buildNasPayload(formData);
      if (editMode && editingNasId) {
        await api.put(`/nas/${editingNasId}`, payload);
      } else {
        await api.post('/nas', payload);
      }
      setError('');
      resetForm();
      await refreshNas();
    } catch (err) {
      console.error('Failed to save NAS device:', err);
      setError('Failed to save NAS device configuration');
    }
  };

  const handleEditNas = (nas) => {
    setEditMode(true);
    setEditingNasId(nas.nasname);
    setFormData({
      nasname: nas.nasname,
      shortname: nas.shortname || '',
      type: nas.type || 'other',
      secret: '', // Password/secret left empty to keep unchanged
      server: nas.server || '',
      ports: nas.ports ? String(nas.ports) : '1812',
      community: nas.community || '',
      description: nas.description || '',
    });
    setShowForm(true);
  };

  const handleDeleteNas = async (nasname) => {
    if (window.confirm(`Are you sure you want to delete NAS gateway ${nasname}?`)) {
      try {
        await api.delete(`/nas/${nasname}`);
        setNasDevices((prev) => prev.filter((nas) => nas.nasname !== nasname));
      } catch (err) {
        console.error('Failed to delete NAS device:', err);
        setError('Failed to delete NAS gateway');
      }
    }
  };

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Network Infrastructure"
        title="NAS Gateway Devices"
        description="Register and manage RADIUS clients, NAS gateways, shared secret status, and router vendor profiles."
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
            <span>Register New NAS Gateway</span>
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
        {/* Table & Search Column */}
        <div className="space-y-6">
          <div className="glass-panel overflow-hidden rounded-3xl shadow-xl">
            <div className="flex flex-col gap-4 border-b border-slate-800/80 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="font-display text-lg font-bold text-slate-100">Registered Gateways ({filteredNasDevices.length})</h2>
                <p className="text-xs text-slate-400">Page {page} of {totalPages}</p>
              </div>
              <div className="w-full sm:w-64">
                <input
                  type="search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search IP, shortname, or vendor..."
                  className="w-full rounded-2xl border border-slate-800 bg-slate-950/80 px-4 py-2 text-xs text-slate-200 placeholder-slate-500 outline-none transition focus:border-cyan-500"
                />
              </div>
            </div>

            {loading ? (
              <TableSkeleton rows={6} columns={6} compact />
            ) : filteredNasDevices.length === 0 ? (
              <div className="py-16 text-center text-sm text-slate-400">
                No NAS gateways found matching query.
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-slate-800/80 bg-slate-900/60 text-xs uppercase tracking-wider text-slate-400">
                      <tr>
                        <th className="px-6 py-3.5 font-semibold">NAS Address / IP</th>
                        <th className="px-6 py-3.5 font-semibold">Short Identifier</th>
                        <th className="px-6 py-3.5 font-semibold">Vendor Type</th>
                        <th className="px-6 py-3.5 font-semibold">RADIUS Port</th>
                        <th className="px-6 py-3.5 font-semibold">Secret Key State</th>
                        <th className="px-6 py-3.5 text-right font-semibold">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
                      {paginatedNasDevices.map((nas) => (
                        <tr key={nas.nasname} className="transition hover:bg-slate-800/40">
                          <td className="font-mono px-6 py-4 font-semibold text-cyan-400">{nas.nasname}</td>
                          <td className="px-6 py-4 text-xs font-semibold text-slate-200">{nas.shortname || 'N/A'}</td>
                          <td className="px-6 py-4 text-xs text-slate-300 capitalize">{nas.type || 'Other'}</td>
                          <td className="font-mono px-6 py-4 text-xs text-slate-400">{nas.ports || '1812'}</td>
                          <td className="px-6 py-4">
                            <StatusBadge status="healthy" customLabel="Configured ✓" size="small" />
                          </td>
                          <td className="px-6 py-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => handleEditNas(nas)}
                                className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1 text-xs font-semibold text-cyan-400 hover:border-cyan-500/40"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleDeleteNas(nas.nasname)}
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
                {editMode ? 'Edit NAS Gateway' : 'Register NAS Gateway'}
              </h3>
              <button onClick={resetForm} className="text-slate-400 hover:text-slate-200">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">NAS IP Address / Hostname</label>
                <input
                  type="text"
                  name="nasname"
                  required
                  disabled={editMode}
                  value={formData.nasname}
                  onChange={handleChange}
                  placeholder="192.168.1.1 or nas.domain.com"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500 disabled:opacity-50"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Short Name</label>
                <input
                  type="text"
                  name="shortname"
                  required
                  value={formData.shortname}
                  onChange={handleChange}
                  placeholder="main-router-01"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Vendor Type</label>
                <select
                  name="type"
                  value={formData.type}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                >
                  <option value="mikrotik">MikroTik RouterOS</option>
                  <option value="cisco">Cisco IOS</option>
                  <option value="juniper">Juniper JUNOS</option>
                  <option value="other">Other Vendor</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                  {editMode ? 'New Shared Secret (leave empty to keep)' : 'RADIUS Shared Secret'}
                </label>
                <input
                  type="password"
                  name="secret"
                  required={!editMode}
                  value={formData.secret}
                  onChange={handleChange}
                  placeholder="••••••••••••"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">RADIUS Auth Port</label>
                <input
                  type="number"
                  name="ports"
                  value={formData.ports}
                  onChange={handleChange}
                  placeholder="1812"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Description / Location</label>
                <textarea
                  name="description"
                  rows={2}
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="e.g. Building A Core Router"
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
                  {editMode ? 'Save Router' : 'Register Gateway'}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default NASManagement;