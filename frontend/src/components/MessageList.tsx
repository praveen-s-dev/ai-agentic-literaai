import { useRef, useEffect } from 'react';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { TypingIndicator } from './TypingIndicator';
import type { ResearchProgress, Citation, Paper, ResearchStage } from '../types';

interface MessageListProps {
  messages: Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    citations?: Citation[];
    papers?: Paper[];
    report?: string;
    current_stage?: ResearchStage;
    is_typing?: boolean;
    error?: string;
  }>;
  progress?: ResearchProgress | null;
  isGenerating: boolean;
  researchError?: string | null;
}

export function MessageList({ messages, progress, isGenerating, researchError }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, progress]);

  if (messages.length === 0) {
    return (
      <div className="message-list empty">
        <div className="empty-state">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          <p>Start a new research session to begin</p>
        </div>
      </div>
    );
  }

  return (
    <div className="message-list" role="log" aria-live="polite" aria-label="Conversation">
      {messages.map((message) => (
        <div key={message.id} className={`message ${message.role}`}>
          {message.role === 'user' ? (
            <UserMessage 
              content={message.content} 
              timestamp={message.timestamp}
            />
          ) : (
            <AssistantMessage
              content={message.content}
              timestamp={message.timestamp}
              citations={message.citations}
              papers={message.papers}
              report={message.report}
              currentStage={message.current_stage}
              isTyping={message.is_typing}
              error={message.error}
            />
          )}
        </div>
      ))}

      {isGenerating && (
        <TypingIndicator />
      )}

      {researchError && (
        <div className="error-message" role="alert">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>{researchError}</span>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}