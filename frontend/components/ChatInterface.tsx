'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useChat } from '../hooks/useChat';
import MessageBubble from './MessageBubble';
import LoadingSkeleton from './LoadingSkeleton';
import InputDock from './InputDock';
import ConfidenceBadge from './ConfidenceBadge';
import ExportButton from './ExportButton';

interface ChatInterfaceProps {
  initialQuery?: string;
}

export default function ChatInterface({ initialQuery }: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const [lastQuery, setLastQuery] = useState<string>('');
  const { messages, loading, sendMessage } = useChat();
  const endRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Handle initial query
  useEffect(() => {
    if (initialQuery && messages.length === 0) {
      setInput(initialQuery);
      handleSend(initialQuery);
    }
  }, [initialQuery]);

  const handleSend = async (message?: string) => {
    const messageToSend = message || input;
    if (!messageToSend.trim() || loading) return;
    
    setLastQuery(messageToSend);
    if (!message) {
      // Only clear input if it's not from QuickActions
      setInput('');
    }
    await sendMessage(messageToSend);
  };

  // Get latest AI message for confidence and flags
  const latestAiMessage = messages.filter(m => m.role === 'ai').slice(-1)[0];
  const latestResponse = latestAiMessage ? {
    confidence: latestAiMessage.confidence ?? 0.5,
    flags: latestAiMessage.flags ?? [],
  } : null;

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h1 className="text-2xl font-bold">Wisconsin Law Enforcement Legal Chat</h1>
        <div className="flex items-center gap-4">
          {latestResponse && (
            <>
              <ConfidenceBadge confidence={latestResponse.confidence} />
              {latestResponse.flags.length > 0 && (
                <div className="flex gap-2">
                  {latestResponse.flags.map((flag, i) => (
                    <span key={i} className="text-xs px-2 py-1 bg-yellow-900/20 text-yellow-400 rounded border border-yellow-800">
                      {flag}
                    </span>
                  ))}
                </div>
              )}
            </>
          )}
          {messages.length > 0 && <ExportButton messages={messages} />}
        </div>
      </div>

      <div className="chat-feed">
        {messages.map((message) => (
          <MessageBubble key={message.id || Date.now()} message={message} query={lastQuery} />
        ))}
        {loading && <LoadingSkeleton />}
        <div ref={endRef} />
      </div>

      <InputDock
        input={input}
        onInputChange={setInput}
        onSend={handleSend}
        disabled={loading}
      />
    </div>
  );
}
