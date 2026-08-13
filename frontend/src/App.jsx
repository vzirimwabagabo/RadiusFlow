import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/authState';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import Packages from './pages/Packages';
import NAS from './pages/NAS';
import Sessions from './pages/Sessions';
import Login from './pages/Login';
import AppShell from './components/AppShell';
import AuthLogs from './pages/AuthLogs';
import Reports from './pages/Reports';
import SystemHealth from './pages/SystemHealth';
import Settings from './pages/Settings';
import Vouchers from './pages/Vouchers';
import AdminUsers from './pages/AdminUsers';
import AuditLogs from './pages/AuditLogs';

function App() {
  const { user } = useAuth();

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <AppShell>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/users" element={<Users />} />
        <Route path="/packages" element={<Packages />} />
        <Route path="/vouchers" element={<Vouchers />} />
        <Route path="/nas" element={<NAS />} />
        <Route path="/sessions" element={<Sessions />} />
        <Route path="/auth-logs" element={<AuthLogs />} />
        <Route path="/admin-users" element={<AdminUsers />} />
        <Route path="/system-audit" element={<AuditLogs />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/health" element={<SystemHealth />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/login" element={<Navigate to="/dashboard" replace />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AppShell>
  );
}

export default App;