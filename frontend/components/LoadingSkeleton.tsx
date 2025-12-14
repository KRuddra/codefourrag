'use client';

import React from 'react';
import { IconShield } from './Icons';

export default function LoadingSkeleton() {
  return (
    <div className="message-group">
      <div className="message-header">
        <div className="avatar ai">
          <IconShield />
        </div>
        <span className="mono text-xs text-gray-500">ANALYZING...</span>
      </div>
      <div className="skeleton-wrapper">
        <div className="skeleton" style={{ width: '90%' }}></div>
        <div className="skeleton" style={{ width: '95%' }}></div>
        <div className="skeleton" style={{ width: '60%' }}></div>
      </div>
    </div>
  );
}
