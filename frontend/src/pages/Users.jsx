import React, { useEffect, useMemo, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/authState';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import PaginationControls from '../components/PaginationControls';
import { TableSkeleton } from '../components/Skeletons';
import api from '../services/api';
import { buildUserPayload, formatExpirationForDateInput } from '../utils/formPayloads';

const EMPTY_FORM = {
  username: '',
  password: '',
  group_name: '',
  rate_limit: '',
  session_timeout: '',
  max_down: '',
  max_up: '',
  idle_timeout: '',
  expiration: '',
  status: 'active',
};

const PAGE_SIZE = 8;

const Users = () => {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [groupFilter, setGroupFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [editMode, setEditMode] = useState(false);
  const [editingUserId, setEditingUserId] = useState(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoading(true);
        const response = await api.get('/users');
        setUsers(Array.isArray(response.data) ? response.data : []);
      } catch (fetchError) {
        console.error('Failed to fetch users:', fetchError);
        setError('Failed to load subscriber accounts');
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  useEffect(() => {
    setPage(1);
  }, [search, statusFilter, groupFilter]);

  const availableGroups = useMemo(
    () => Array.from(new Set(users.map((item) => item.group_name).filter(Boolean))).sort(),
    [users],
  );

  const filteredUsers = useMemo(() => {
    const query = search.trim().toLowerCase();
    return users.filter((item) => {
      const matchesSearch =
        !query ||
        [item.username, item.group_name, item.status]
          .filter(Boolean)
          .some((value) => value.toLowerCase().includes(query));
      const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
      const matchesGroup = groupFilter === 'all' || item.group_name === groupFilter;
      return matchesSearch && matchesStatus && matchesGroup;
    });
  }, [users, search, statusFilter, groupFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredUsers.length / PAGE_SIZE));
  const paginatedUsers = useMemo(
    () => filteredUsers.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [filteredUsers, page],
  );

  useEffect(() => {
    setPage((current) => Math.min(current, totalPages));
  }, [totalPages]);

  const resetForm = () => {
    setEditMode(false);
    setEditingUserId(null);
    setFormData(EMPTY_FORM);
    setShowForm(false);
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((previous) => ({ ...previous, [name]: value }));
  };

  const refreshUsers = async () => {
    const response = await api.get('/users');
    setUsers(Array.isArray(response.data) ? response.data : []);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      const payload = buildUserPayload(formData, { requirePassword: !editMode });
      if (editMode && editingUserId) {
        await api.put(`/users/${editingUserId}`, payload);
      } else {
        await api.post('/users', payload);
      }

      setError('');
      resetForm();
      await refreshUsers();
    } catch (submitError) {
      console.error('Failed to save user:', submitError);
      setError('Failed to save subscriber record');
    }
  };

  const handleEditUser = (selectedUser) => {
    setEditMode(true);
    setEditingUserId(selectedUser.username);
    setFormData({
      username: selectedUser.username,
      password: '',
      group_name: selectedUser.group_name || '',
      rate_limit: selectedUser.rate_limit || '',
      session_timeout: selectedUser.session_timeout ? String(selectedUser.session_timeout) : '',
      max_down: selectedUser.max_down ? String(selectedUser.max_down) : '',
      max_up: selectedUser.max_up ? String(selectedUser.max_up) : '',
      idle_timeout: selectedUser.idle_timeout ? String(selectedUser.idle_timeout) : '',
      expiration: formatExpirationForDateInput(selectedUser.expiration),
      status: selectedUser.status === 'blocked' ? 'blocked' : 'active',
    });
    setShowForm(true);
  };

  const handleDeleteUser = async (username) => {
    if (!window.confirm(`Are you sure you want to delete subscriber ${username}?`)) {
      return;
    }

    try {
      await api.delete(`/users/${username}`);
      setUsers((previous) => previous.filter((item) => item.username !== username));
    } catch (deleteError) {
      console.error('Failed to delete user:', deleteError);
      setError('Failed to delete subscriber');
    }
  };

  const handleBlockUser = async (username, currentlyBlocked) => {
    try {
      if (currentlyBlocked) {
        await api.delete(`/users/${username}/block`);
      } else {
        await api.post(`/users/${username}/block`);
      }
      await refreshUsers();
    } catch (statusError) {
      console.error('Failed to block/unblock user:', statusError);
      setError('Failed to update subscriber status');
    }
  };

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const statusCounts = users.reduce((accumulator, item) => {
    const status = item.status || 'active';
    accumulator[status] = (accumulator[status] || 0) + 1;
    return accumulator;
  }, {});

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Subscriber Management"
        title="Manage FreeRADIUS Subscribers"
        description="Provision, edit, suspend, and monitor network access credentials for active users."
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
            <span>Add New Subscriber</span>
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

      {/* Metric Cards */}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="glass-card rounded-3xl p-5 border-l-4 border-l-cyan-500">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Subscribers</span>
          <p className="font-display mt-2 text-2xl font-extrabold text-slate-100">{users.length}</p>
        </div>
        <div className="glass-card rounded-3xl p-5 border-l-4 border-l-emerald-500">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Active</span>
          <p className="font-display mt-2 text-2xl font-extrabold text-emerald-400">{statusCounts.active || 0}</p>
        </div>
        <div className="glass-card rounded-3xl p-5 border-l-4 border-l-rose-500">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Blocked</span>
          <p className="font-display mt-2 text-2xl font-extrabold text-rose-400">{statusCounts.blocked || 0}</p>
        </div>
        <div className="glass-card rounded-3xl p-5 border-l-4 border-l-amber-500">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Expired</span>
          <p className="font-display mt-2 text-2xl font-extrabold text-amber-400">{statusCounts.expired || 0}</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_350px]">
        {/* Table Column */}
        <div className="space-y-6">
          {/* Filters Bar */}
          <div className="glass-panel rounded-3xl p-5">
            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <label htmlFor="search" className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1.5">
                  Search
                </label>
                <input
                  id="search"
                  type="search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search username or group..."
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 outline-none transition focus:border-cyan-500"
                />
              </div>

              <div>
                <label htmlFor="status-filter" className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1.5">
                  Status
                </label>
                <select
                  id="status-filter"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3.5 py-2 text-xs text-slate-200 outline-none transition focus:border-cyan-500"
                >
                  <option value="all">All Statuses</option>
                  <option value="active">Active</option>
                  <option value="blocked">Blocked</option>
                  <option value="expired">Expired</option>
                </select>
              </div>

              <div>
                <label htmlFor="group-filter" className="block text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1.5">
                  Package / Group
                </label>
                <select
                  id="group-filter"
                  value={groupFilter}
                  onChange={(e) => setGroupFilter(e.target.value)}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3.5 py-2 text-xs text-slate-200 outline-none transition focus:border-cyan-500"
                >
                  <option value="all">All Groups</option>
                  {availableGroups.map((group) => (
                    <option key={group} value={group}>
                      {group}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Table View */}
          <div className="glass-panel overflow-hidden rounded-3xl shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800/80 px-6 py-4">
              <h2 className="font-display text-base font-bold text-slate-100">Subscribers ({filteredUsers.length})</h2>
              <span className="text-xs text-slate-400">
                Page {page} of {totalPages}
              </span>
            </div>

            {loading ? (
              <TableSkeleton rows={6} columns={5} compact />
            ) : filteredUsers.length === 0 ? (
              <div className="py-16 text-center text-sm text-slate-400">
                No subscriber records match the criteria.
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-slate-800/80 bg-slate-900/60 text-xs uppercase tracking-wider text-slate-400">
                      <tr>
                        <th className="px-6 py-3.5 font-semibold">Subscriber</th>
                        <th className="px-6 py-3.5 font-semibold">Package / Group</th>
                        <th className="px-6 py-3.5 font-semibold">Status</th>
                        <th className="px-6 py-3.5 font-semibold">Expiration</th>
                        <th className="px-6 py-3.5 text-right font-semibold">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
                      {paginatedUsers.map((currentUser) => (
                        <tr key={currentUser.username} className="transition hover:bg-slate-800/40">
                          <td className="px-6 py-4 font-semibold text-slate-100">{currentUser.username}</td>
                          <td className="px-6 py-4 text-xs text-slate-300">{currentUser.group_name || 'None'}</td>
                          <td className="px-6 py-4">
                            <StatusBadge status={currentUser.status} size="small" />
                          </td>
                          <td className="px-6 py-4 text-xs text-slate-400">{currentUser.expiration || 'Never'}</td>
                          <td className="px-6 py-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => handleEditUser(currentUser)}
                                className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1 text-xs font-semibold text-cyan-400 hover:border-cyan-500/40"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleBlockUser(currentUser.username, currentUser.status === 'blocked')}
                                className={`rounded-lg border px-3 py-1 text-xs font-semibold ${
                                  currentUser.status === 'blocked'
                                    ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'
                                    : 'border-amber-500/30 bg-amber-500/10 text-amber-400 hover:bg-amber-500/20'
                                }`}
                              >
                                {currentUser.status === 'blocked' ? 'Unblock' : 'Block'}
                              </button>
                              <button
                                onClick={() => handleDeleteUser(currentUser.username)}
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

        {/* Form Sidebar Panel */}
        {(showForm || editMode) && (
          <div className="glass-panel h-fit rounded-3xl p-6 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
              <h3 className="font-display text-base font-bold text-slate-100">
                {editMode ? 'Edit Subscriber' : 'New Subscriber'}
              </h3>
              <button onClick={resetForm} className="text-slate-400 hover:text-slate-200">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Username</label>
                <input
                  type="text"
                  name="username"
                  required
                  disabled={editMode}
                  value={formData.username}
                  onChange={handleChange}
                  placeholder="subscriber_name"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500 disabled:opacity-50"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                  {editMode ? 'New Password (leave empty to keep)' : 'Password'}
                </label>
                <input
                  type="password"
                  name="password"
                  required={!editMode}
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Package / Group</label>
                <input
                  type="text"
                  name="group_name"
                  value={formData.group_name}
                  onChange={handleChange}
                  placeholder="e.g. 10M_Unlimited"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Rate Limit (Bandwidth)</label>
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
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Expiration Date</label>
                <input
                  type="date"
                  name="expiration"
                  value={formData.expiration}
                  onChange={handleChange}
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
                  {editMode ? 'Save Changes' : 'Create Account'}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default Users;