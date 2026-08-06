import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useAuth } from '../contexts/authState';
import AvatarFallback from './AvatarFallback';

const ROUTE_NAMES = {
  '/dashboard': 'Dashboard',
  '/users': 'Subscribers',
  '/packages': 'Packages',
  '/nas': 'NAS Devices',
  '/sessions': 'Active Sessions',
  '/auth-logs': 'Authentication Logs',
  '/reports': 'Reports & Analytics',
  '/health': 'System Health',
  '/settings': 'Settings',
};

const Header = ({ onMobileNavToggle }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const currentTitle = ROUTE_NAMES[location.pathname] || 'Console';

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-800/80 bg-slate-950/80 px-4 backdrop-blur-md sm:px-6 lg:px-8">
      <div className="flex items-center gap-3">
        {/* Mobile Nav Trigger */}
        <button
          onClick={onMobileNavToggle}
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-800 bg-slate-900 text-slate-400 hover:text-white md:hidden"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Breadcrumb Navigation */}
        <nav className="flex items-center gap-2 text-xs text-slate-400">
          <Link to="/dashboard" className="transition hover:text-cyan-400">RadiusFlow</Link>
          <span>/</span>
          <span className="font-semibold text-slate-200">{currentTitle}</span>
        </nav>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* Live System Indicator */}
        <div className="hidden items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 sm:flex">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          System Operational
        </div>

        {/* Profile Pill & Menu */}
        <div className="flex items-center gap-3 border-l border-slate-800 pl-4">
          <AvatarFallback
            name={user?.username}
            className="h-9 w-9 bg-gradient-to-br from-cyan-500 to-violet-600 text-xs font-bold text-white shadow-md shadow-cyan-950/30"
          />
          <div className="hidden min-w-0 flex-col sm:flex">
            <span className="truncate text-xs font-bold text-slate-200">{user?.username || 'Admin'}</span>
            <span className="truncate text-[10px] font-semibold text-slate-400 uppercase tracking-wider">{user?.role || 'Administrator'}</span>
          </div>
          <button
            onClick={logout}
            title="Sign out"
            className="ml-1 rounded-lg p-2 text-slate-400 transition hover:bg-slate-800 hover:text-rose-400"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
