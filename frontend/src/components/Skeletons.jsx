import React from 'react';

export const TableSkeleton = ({ rows = 5, columns = 5, compact = false }) => (
  <div className={`space-y-3 ${compact ? 'py-4' : 'py-6'}`}>
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <div
        key={rowIndex}
        className={`grid gap-4 rounded-2xl border border-slate-100 bg-slate-50 px-5 ${compact ? 'py-3' : 'py-4'}`}
        style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
      >
        {Array.from({ length: columns }).map((__, columnIndex) => (
          <div
            key={columnIndex}
            className={`h-${compact ? '3' : '4'} animate-pulse rounded-full bg-slate-200 ${columnIndex === columns - 1 ? 'justify-self-end' : ''}`}
          />
        ))}
      </div>
    ))}
  </div>
);

export const CardSkeletonGrid = ({ cards = 4 }) => (
  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    {Array.from({ length: cards }).map((_, index) => (
      <div key={index} className="overflow-hidden rounded-3xl border border-[color:var(--border)] bg-white shadow-sm">
        <div className="h-2 animate-pulse bg-slate-200" />
        <div className="space-y-4 p-6">
          <div className="h-3 w-28 animate-pulse rounded-full bg-slate-200" />
          <div className="h-8 w-24 animate-pulse rounded-full bg-slate-200" />
          <div className="h-3 w-40 animate-pulse rounded-full bg-slate-100" />
        </div>
      </div>
    ))}
  </div>
);
