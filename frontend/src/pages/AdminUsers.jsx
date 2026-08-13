import React, { useEffect, useMemo, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/authState';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import PaginationControls from '../components/PaginationControls';
import { TableSkeleton } from '../components/Skeletons';
import api from '../services/api';

const EMPTY_FORM = {
  username: '',
  password: '',
  role: 'operator',
};

const PAGE_SIZE = 8;

const AdminUsers = () => {
  const { user } = useAuth();
  const [adminUsers, setAdminUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [editMode, setEditMode] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    fetchAdminUsers();
  }, []);

  const fetchAdminUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/users');
      setAdminUsers(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      console.error('Failed to fetch admin users:', err);
      setError('Failed to load management accounts');
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = useMemo(() => {
    const query = search.trim().toLowerCase();
    return adminUsers.filter((u) => {
      const matchesQuery = !query || u.username.toLowerCase().includes(query) || u.role.toLowerCase().includes(query);
      const matchesRole = roleFilter === 'all' || u.role === roleFilter;
      return matchesQuery && matchesRole;
    });
  }, [adminUsers, search, roleFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredUsers.length / PAGE_SIZE));
  const paginatedUsers = useMemo(
    () => filteredUsers.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [filteredUsers, page],
  );

  useEffect(() => {
    setPage(1);
  }, [search, roleFilter]);

  const resetForm = () => {
    setFormData(EMPTY_FORM);
    setEditMode(false);
    setEditingUser(null);
    setShowForm(false);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editMode && editingUser) {
        await api.put(`/admin/users/${editingUser.id}`, {
          role: formData.role,
          password: formData.password || undefined,
        });
      } else {
        await api.post('/admin/users', formData);
      }
      setError('');
      resetForm();
      await fetchAdminUsers();
    } catch (err) {
      console.error('Failed to save admin user:', err);
      setError(err.response?.data?.detail || 'Failed to save management user');
    }
  };

  const handleToggleStatus = async (userObj) => {
    try {
      await api.put(`/admin/users/${userObj.id}`, {
        is_active: !userObj.is_active,
      });
      await fetchAdminUsers();
    } catch (err) {
      console.error('Failed to update status:', err);
      setError('Failed to update account status');
    }
  };

  const handleDeleteUser = async (userObj) => {
    if (window.confirm(`Are you sure you want to delete management account "${userObj.username}"?`)) {
      try {
        await api.delete(`/admin/users/${userObj.id}`);
        setAdminUsers((prev) => prev.filter((u) => u.id !== userObj.id));
      } catch (err) {
        console.error('Failed to delete user:', err);
        setError(err.response?.data?.detail || 'Failed to delete account');
      }
    }
  };

  const handleEditClick = (u) => {
    setEditMode(true);
    setEditingUser(u);
    setFormData({
      username: u.username,
      password: '',
      role: u.role,
    });
    setShowForm(true);
  };

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        badge="Administration & Security"
        title="Management Console Users"
        description="Manage system administrator, operator, and read-only user access accounts (app_users)."
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
            <span>Create Admin User</span>
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
        {/* Table Column */}
        <div className="space-y-6">
          <div className="glass-panel overflow-hidden rounded-3xl shadow-xl">
            <div className="flex flex-col gap-4 border-b border-slate-800/80 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="font-display text-lg font-bold text-slate-100">Management Accounts ({filteredUsers.length})</h2>
                <p className="text-xs text-slate-400">Page {page} of {totalPages}</p>
              </div>
              <div className="flex gap-3">
                <select
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                  className="rounded-2xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                >
                  <option value="all">All Roles</option>
                  <option value="super_admin">Super Admin</option>
                  <option value="admin">Admin</option>
                  <option value="network_admin">Network Admin</option>
                  <option value="operator">Operator</option>
                  <option value="viewer">Viewer</option>
                </select>
                <input
                  type="search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search username..."
                  className="w-full sm:w-48 rounded-2xl border border-slate-800 bg-slate-950/80 px-4 py-2 text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            {loading ? (
              <TableSkeleton rows={5} columns={5} compact />
            ) : filteredUsers.length === 0 ? (
              <div className="py-16 text-center text-sm text-slate-400">No management users found.</div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-slate-800/80 bg-slate-900/60 text-xs uppercase tracking-wider text-slate-400">
                      <tr>
                        <th className="px-6 py-3.5 font-semibold">Username</th>
                        <th className="px-6 py-3.5 font-semibold">Role</th>
                        <th className="px-6 py-3.5 font-semibold">Status</th>
                        <th className="px-6 py-3.5 font-semibold">Last Login</th>
                        <th className="px-6 py-3.5 text-right font-semibold">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
                      {paginatedUsers.map((u) => (
                        <tr key={u.id} className="transition hover:bg-slate-800/40">
                          <td className="px-6 py-4 font-semibold text-slate-100">{u.username}</td>
                          <td className="px-6 py-4 text-xs font-mono capitalize text-cyan-400">{u.role}</td>
                          <td className="px-6 py-4">
                            <StatusBadge status={u.is_active ? 'active' : 'offline'} customLabel={u.is_active ? 'Active' : 'Disabled'} size="small" />
                          </td>
                          <td className="px-6 py-4 text-xs text-slate-400">
                            {u.last_login_at ? new Date(u.last_login_at).toLocaleString() : 'Never'}
                          </td>
                          <td className="px-6 py-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => handleEditClick(u)}
                                className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1 text-xs font-semibold text-cyan-400 hover:border-cyan-500/40"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleToggleStatus(u)}
                                className={`rounded-lg border px-3 py-1 text-xs font-semibold ${
                                  u.is_active
                                    ? 'border-amber-500/30 bg-amber-500/10 text-amber-400 hover:bg-amber-500/20'
                                    : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'
                                }`}
                              >
                                {u.is_active ? 'Disable' : 'Enable'}
                              </button>
                              <button
                                onClick={() => handleDeleteUser(u)}
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

        {/* Side Form Panel */}
        {(showForm || editMode) && (
          <div className="glass-panel h-fit rounded-3xl p-6 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
              <h3 className="font-display text-base font-bold text-slate-100">
                {editMode ? `Edit Role / Password` : 'Create Admin Account'}
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
                  placeholder="admin_username"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500 disabled:opacity-50"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                  {editMode ? 'New Password (leave blank to keep)' : 'Password'}
                </label>
                <input
                  type="password"
                  name="password"
                  required={!editMode}
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="••••••••••••"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Management Role</label>
                <select
                  name="role"
                  value={formData.role}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500"
                >
                  <option value="super_admin">Super Admin (Full Control)</option>
                  <option value="admin">Administrator</option>
                  <option value="network_admin">Network Admin (NAS & Packages)</option>
                  <option value="operator">Operator (Subscribers & Vouchers)</option>
                  <option value="viewer">Viewer (Read Only)</option>
                </select>
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
                  {editMode ? 'Save Role' : 'Create Account'}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminUsers;
