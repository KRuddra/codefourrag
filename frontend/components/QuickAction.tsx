'use client';

import React from 'react';

interface QuickActionProps {
  icon: string | React.ReactNode;
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

export default function QuickAction({ icon, label, onClick, disabled = false }: QuickActionProps) {
  return (
    <button
      className="btn-action"
      onClick={onClick}
      disabled={disabled}
      type="button"
    >
      {typeof icon === 'string' ? <span>{icon}</span> : icon}
      <span>{label}</span>
    </button>
  );
}

