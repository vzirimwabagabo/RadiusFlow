import React from 'react';

const AvatarFallback = ({ name = '', className = '' }) => {
  const initials = (name || 'U')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('') || 'U';

  return (
    <div
      className={`inline-flex items-center justify-center rounded-full bg-slate-900 text-white font-semibold tracking-wide ${className}`}
      aria-hidden="true"
    >
      {initials}
    </div>
  );
};

export default AvatarFallback;