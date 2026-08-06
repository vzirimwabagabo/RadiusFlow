import React from 'react';

const PageHeader = ({ badge, title, description, actions }) => {
  return (
    <div className="glass-panel rounded-3xl p-6 shadow-xl">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          {badge && (
            <p className="font-display text-xs font-bold uppercase tracking-[0.25em] text-cyan-400">
              {badge}
            </p>
          )}
          <h1 className="font-display mt-1 text-2xl font-bold text-slate-100 sm:text-3xl">
            {title}
          </h1>
          {description && (
            <p className="mt-1 max-w-3xl text-sm text-slate-400">
              {description}
            </p>
          )}
        </div>
        {actions && <div className="flex flex-wrap items-center gap-3">{actions}</div>}
      </div>
    </div>
  );
};

export default PageHeader;
