'use client';

import React from 'react';
import { SourceDocument } from '../lib/types';

interface SourceCardProps {
  source: SourceDocument;
  query?: string; // For highlighting search terms
}

export default function SourceCard({ source, query }: SourceCardProps) {
  const { metadata, text, score } = source;

  // Highlight search terms in text (simple approach)
  const highlightText = (text: string, searchTerms?: string): React.ReactNode => {
    if (!searchTerms) return text;
    
    const terms = searchTerms.toLowerCase().split(/\s+/).filter(t => t.length > 2);
    if (terms.length === 0) return text;

    let highlighted = text;
    terms.forEach(term => {
      const regex = new RegExp(`(${term})`, 'gi');
      highlighted = highlighted.replace(regex, '<mark class="highlight-term">$1</mark>');
    });

    return <span dangerouslySetInnerHTML={{ __html: highlighted }} />;
  };

  const getDocTypeLabel = (docType?: string): string => {
    switch (docType) {
      case 'statute': return 'STATUTE';
      case 'case_law': return 'CASE LAW';
      case 'policy': return 'POLICY';
      case 'training': return 'TRAINING';
      default: return 'DOCUMENT';
    }
  };

  return (
    <div className="source-card">
      <div className="card-meta">
        <span className="text-xs font-semibold text-blue-400">
          {getDocTypeLabel(metadata.doc_type)}
        </span>
        <span className="mono text-xs text-gray-500">
          {metadata.source_id.slice(0, 12)}...
        </span>
      </div>
      
      <div className="card-title">{metadata.title}</div>
      
      <div className="card-snippet">
        {highlightText(text, query)}
      </div>

      <div className="mt-3 pt-3 border-t border-gray-700 flex items-center justify-between text-xs text-gray-500">
        <div className="flex gap-4">
          {metadata.statute_number && (
            <span className="font-mono">§ {metadata.statute_number}</span>
          )}
          {metadata.case_citation && (
            <span className="font-mono">{metadata.case_citation}</span>
          )}
        </div>
        <span className="text-gray-600">
          {(score * 100).toFixed(1)}% match
        </span>
      </div>
    </div>
  );
}
