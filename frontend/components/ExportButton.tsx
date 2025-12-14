'use client';

import React, { useState } from 'react';
import { IconCopy } from './Icons';
import { Message } from '../lib/types';

interface ExportButtonProps {
  messages: Message[];
}

export default function ExportButton({ messages }: ExportButtonProps) {
  const [copied, setCopied] = useState(false);

  const exportToMarkdown = (): string => {
    let markdown = '# Legal Chat Export\n\n';
    markdown += `Generated on: ${new Date().toLocaleString()}\n\n`;
    markdown += '---\n\n';

    messages.forEach((message, index) => {
      if (message.role === 'user') {
        markdown += `## User Question ${index + 1}\n\n`;
        markdown += `${message.content}\n\n`;
      } else {
        markdown += `### Assistant Response\n\n`;
        markdown += `${message.content}\n\n`;

        if (message.sources && message.sources.length > 0) {
          markdown += `#### Sources\n\n`;
          message.sources.forEach((source, idx) => {
            markdown += `${idx + 1}. **${source.metadata.title}**\n`;
            if (source.metadata.statute_number) {
              markdown += `   - Statute: ${source.metadata.statute_number}\n`;
            }
            if (source.metadata.case_citation) {
              markdown += `   - Case: ${source.metadata.case_citation}\n`;
            }
            markdown += `   - Relevance: ${(source.score * 100).toFixed(1)}%\n`;
            markdown += `   - Snippet: ${source.text.substring(0, 200)}${source.text.length > 200 ? '...' : ''}\n\n`;
          });
        }
        markdown += '---\n\n';
      }
    });

    return markdown;
  };

  const handleCopy = async () => {
    try {
      const markdown = exportToMarkdown();
      await navigator.clipboard.writeText(markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      alert('Failed to copy to clipboard. Please try again.');
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-600 rounded text-sm font-medium text-gray-200 transition-colors"
      title="Copy conversation to clipboard (Markdown format)"
    >
      <IconCopy width={16} height={16} />
      {copied ? 'Copied!' : 'Export'}
    </button>
  );
}
