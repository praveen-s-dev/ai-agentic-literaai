import '../styles/Message.css';

interface UserMessageProps {
  content: string;
  timestamp: string;
}

export function UserMessage({ content, timestamp }: UserMessageProps) {
  return (
    <div className="message user-message">
      <div className="message-avatar user-avatar">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
      </div>
      <div className="message-content">
        <div className="message-bubble user-bubble">
          <pre className="message-text">{content}</pre>
        </div>
        <div className="message-meta">
          <time dateTime={timestamp}>
            {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </time>
        </div>
      </div>
    </div>
  );
}