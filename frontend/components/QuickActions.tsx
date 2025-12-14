'use client';

import React from 'react';
import QuickAction from './QuickAction';

interface QuickActionsProps {
  onQuerySelect: (query: string) => void;
  disabled?: boolean;
}

const DEMO_QUERIES = [
  {
    icon: '🚗',
    label: 'OWI 3rd Offense',
    query: 'OWI 3rd offense elements',
  },
  {
    icon: '🚔',
    label: 'Vehicle Search',
    query: 'Vehicle search during traffic stop',
  },
  {
    icon: '⏱️',
    label: 'Theft Statute',
    query: 'Misdemeanor theft statute of limitations',
  },
  {
    icon: '⚖️',
    label: 'Terry Stop Cases',
    query: 'Recent Terry stop cases',
  },
  {
    icon: '🏃',
    label: 'Pursuit Policy',
    query: 'Department pursuit policy',
  },
  {
    icon: '👶',
    label: 'Miranda Juveniles',
    query: 'Miranda warnings for juveniles',
  },
];

export default function QuickActions({ onQuerySelect, disabled = false }: QuickActionsProps) {
  return (
    <div className="actions-row">
      {DEMO_QUERIES.map((action, i) => (
        <QuickAction
          key={i}
          icon={action.icon}
          label={action.label}
          onClick={() => !disabled && onQuerySelect(action.query)}
          disabled={disabled}
        />
      ))}
    </div>
  );
}
