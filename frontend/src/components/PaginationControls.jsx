import React from 'react';

const PaginationControls = ({ page, totalPages, onPageChange, className = '' }) => {
  if (!totalPages || totalPages <= 1) {
    return null;
  }

  const visiblePages = Array.from({ length: Math.min(totalPages, 5) }, (_, index) => index + 1);

  return (
    <div className={`flex flex-col items-center justify-between gap-4 border-t border-slate-100 pt-4 lg:flex-row ${className}`.trim()}>
      <p className="text-sm text-[var(--muted)]">
        Page {page} of {totalPages}
      </p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={page === 1}
          className="rounded-xl border border-[color:var(--border)] bg-white px-3 py-2 text-sm font-semibold text-[var(--text)] transition hover:border-[var(--brand)] hover:text-[var(--brand)] disabled:cursor-not-allowed disabled:opacity-40"
        >
          Previous
        </button>
        {visiblePages.map((currentPage) => (
          <button
            key={currentPage}
            type="button"
            onClick={() => onPageChange(currentPage)}
            className={`rounded-xl px-3 py-2 text-sm font-semibold transition ${page === currentPage ? 'bg-[linear-gradient(135deg,var(--brand),var(--accent))] text-white' : 'border border-[color:var(--border)] bg-white text-[var(--text)] hover:border-[var(--brand)] hover:text-[var(--brand)]'}`}
          >
            {currentPage}
          </button>
        ))}
        <button
          type="button"
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          disabled={page === totalPages}
          className="rounded-xl border border-[color:var(--border)] bg-white px-3 py-2 text-sm font-semibold text-[var(--text)] transition hover:border-[var(--brand)] hover:text-[var(--brand)] disabled:cursor-not-allowed disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default PaginationControls;