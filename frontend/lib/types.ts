/**
 * Type definitions for the frontend application
 */

export interface Message {
  id?: string;
  role: 'user' | 'ai';
  content: string;
  sources?: SourceDocument[];
  confidence?: number;
  flags?: string[];
  timestamp?: string;
  error?: boolean;
}

export interface SourceDocument {
  text: string;
  metadata: {
    source_id: string;
    title: string;
    statute_number?: string;
    case_citation?: string;
    source_uri: string;
    chunk_id?: string;
    doc_type?: string;
    jurisdiction?: string;
    [key: string]: any;
  };
  score: number;
}

export interface ChatResponse {
  response: string;
  sources: SourceDocument[];
  confidence: number;
  flags: string[];
  conversation_id: string;
}

