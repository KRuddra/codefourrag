'use client';

import React from 'react';
import { Message } from '../lib/types';
import SourceCard from './SourceCard';
import ConfidenceBadge from './ConfidenceBadge';
import { IconShield } from './Icons';

interface MessageBubbleProps {
  message: Message;
  query?: string; // For highlighting in sources
}

export default function MessageBubble({ message, query }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  // Extract clean answer text (remove disclaimers for separate display)
  const getAnswerSections = (content: string) => {
    const disclaimerMatch = content.match(/⚠️ DISCLAIMER:.*$/s);
    const cautionMatch = content.match(/🚨 USE OF FORCE CAUTION:.*$/s);
    
    let answerText = content;
    let disclaimer = '';
    let caution = '';
    
    if (disclaimerMatch) {
      disclaimer = disclaimerMatch[0].trim();
      answerText = content.replace(disclaimerMatch[0], '').trim();
    }
    
    if (cautionMatch) {
      caution = cautionMatch[0].trim();
      answerText = answerText.replace(cautionMatch[0], '').trim();
    }
    
    return { answerText, disclaimer, caution };
  };

  const { answerText, disclaimer, caution } = getAnswerSections(message.content);

  return (
    <div className={`message-group ${isUser ? 'text-right' : 'text-left'}`}>
      {!isUser && (
        <div className="message-header">
          <div className="avatar ai">
            <IconShield />
          </div>
          <span className="mono text-xs text-gray-500">LEGAL ASSISTANT</span>
        </div>
      )}

      {isUser ? (
        <div className="bubble-user">{message.content}</div>
      ) : (
        <div className="ai-message-container">
          {/* Answer Section */}
          <div className="ai-answer-section">
            <div className="ai-text">{answerText}</div>
          </div>

          {/* Confidence Section */}
          {message.confidence !== undefined && (
            <div className="ai-meta-section">
              <div className="section-label">Confidence Level</div>
              <ConfidenceBadge confidence={message.confidence} />
            </div>
          )}

          {/* Citations Section */}
          {message.sources && message.sources.length > 0 && (
            <div className="ai-meta-section">
              <div className="section-label">Sources & Citations</div>
              <div className="cards-grid">
                {message.sources.map((source, i) => (
                  <SourceCard key={i} source={source} query={query} />
                ))}
              </div>
            </div>
          )}

          {/* Flags Section */}
          {message.flags && message.flags.length > 0 && (
            <div className="ai-meta-section">
              <div className="section-label">Flags & Warnings</div>
              <div className="flags-container">
                {message.flags.map((flag, i) => (
                  <span key={i} className="flag-badge">
                    {flag.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Disclaimers */}
          {(disclaimer || caution) && (
            <div className="ai-disclaimer-section">
              {disclaimer && <div className="disclaimer-text">{disclaimer}</div>}
              {caution && <div className="caution-text">{caution}</div>}
            </div>
          )}

          {message.error && (
            <div className="mt-2 text-sm text-red-400">
              Error: {message.content}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
