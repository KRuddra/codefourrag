'use client';

import React from 'react';

interface ConfidenceBadgeProps {
  confidence: number; // 0.0 to 1.0
}

export default function ConfidenceBadge({ confidence }: ConfidenceBadgeProps) {
  const percentage = Math.round(confidence * 100);
  
  // Determine color based on confidence level
  let colorClass = 'text-gray-400';
  let bgClass = 'bg-gray-800';
  
  if (confidence >= 0.7) {
    colorClass = 'text-green-400';
    bgClass = 'bg-green-900/20';
  } else if (confidence >= 0.4) {
    colorClass = 'text-yellow-400';
    bgClass = 'bg-yellow-900/20';
  } else {
    colorClass = 'text-red-400';
    bgClass = 'bg-red-900/20';
  }

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold ${bgClass} ${colorClass} border border-gray-700`}>
      <span>Confidence:</span>
      <span className="font-mono">{percentage}%</span>
    </div>
  );
}
