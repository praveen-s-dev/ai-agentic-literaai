import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import tomorrow from 'react-syntax-highlighter/dist/esm/styles/prism/tomorrow';
import { Copy, Download, FileText, Search } from 'lucide-react';
import { useState } from 'react';
import type { Citation, Paper, ResearchStage } from '../types';
import { researchStageLabels, researchStageIcons } from '../types/researchStages';
import '../styles/Message.css';

interface AssistantMessageProps {
  content: string;
  timestamp: string;
  citations?: Citation[];
  papers?: Paper[];
  report?: string;
  currentStage?: ResearchStage;
  isTyping?: boolean;
  error?: string;
}

export function AssistantMessage({ 
  content, 
  timestamp, 
  citations, 
  papers, 
  report, 
  currentStage, 
  isTyping, 
  error 
}: AssistantMessageProps) {
  const [copied, setCopied] = useState(false);
  const [expandedCitations, setExpandedCitations] = useState(false);
  const [expandedPapers, setExpandedPapers] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isTyping) {
    return (
      <div className="message assistant-message typing">
        <div className="message-avatar assistant-avatar">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
        </div>
        <div className="message-content">
          <div className="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="message assistant-message">
      <div className="message-avatar assistant-avatar">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
      </div>
      <div className="message-content">
        <div className="message-bubble assistant-bubble">
          <ReactMarkdown
            components={{
// eslint-disable-next-line @typescript-eslint/no-explicit-any
code: (({ node, children }: { node?: { lang?: string; value: string } | unknown; children: React.ReactNode }) => {
  const nodeValue = (node as any)?.value;
  if (!node || nodeValue === undefined) {
    return <code className="inline-code">{children}</code>;
  }
  const inline = !nodeValue.includes('\n');
  if (inline) {
    return <code className="inline-code">{children}</code>;
  }
  return (
    <SyntaxHighlighter 
      language={(node as any).lang || 'text'} 
      style={tomorrow}
      showLineNumbers
      customStyle={{ 
        borderRadius: '8px',
        fontSize: '0.85rem',
      }}
    >
      {String(children).replace(/\n$/, '')}
    </SyntaxHighlighter>
  );
}) as any,
              blockquote: ({ children }) => (
                <blockquote className="markdown-blockquote">{children}</blockquote>
              ),
              table: ({ children }) => (
                <div className="markdown-table-container">
                  <table>{children}</table>
                </div>
              ),
              th: ({ children }) => <th>{children}</th>,
              td: ({ children }) => <td>{children}</td>,
            }}
          >
            {content}
          </ReactMarkdown>

          {currentStage && (
            <div className="research-stage">
              <span className="stage-badge">
                <span className="stage-icon">{researchStageIcons[currentStage]}</span>
                <span>{researchStageLabels[currentStage]}</span>
              </span>
            </div>
          )}

          {citations && citations.length > 0 && (
            <details className="citations-section" open={expandedCitations}>
              <summary onClick={() => setExpandedCitations(!expandedCitations)}>
                <Search size={14} />
                <span>Citations ({citations.length})</span>
                <svg width="16" height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={expandedCitations ? 'rotated' : ''}>
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </summary>
              <div className="citations-list">
                {citations.map((citation, index) => (
                  <div key={index} className="citation-item">
                    <div className="citation-title">{citation.title}</div>
                    <div className="citation-meta">
                      {citation.authors.slice(0, 3).join(', ')}
                      {citation.authors.length > 3 && ' et al.'}
                      {citation.year && ` (${citation.year})`}
                      {citation.source && ` • ${citation.source}`}
                      {citation.citations > 0 && ` • ${citation.citations} citations`}
                    </div>
                    {citation.doi && (
                      <a 
                        href={`https://doi.org/${citation.doi}`} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="citation-link"
                      >
                        DOI: {citation.doi}
                      </a>
                    )}
                    {citation.url && (
                      <a 
                        href={citation.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="citation-link"
                      >
                        Source
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </details>
          )}

          {papers && papers.length > 0 && (
            <details className="papers-section" open={expandedPapers}>
              <summary onClick={() => setExpandedPapers(!expandedPapers)}>
                <FileText size={14} />
                <span>Papers ({papers.length})</span>
                <svg width="16" height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={expandedPapers ? 'rotated' : ''}>
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </summary>
              <div className="papers-list">
                {papers.map((paper, index) => (
                  <div key={index} className="paper-item">
                    <div className="paper-title">{paper.title}</div>
                    <div className="paper-meta">
                      {paper.authors.slice(0, 3).join(', ')}
                      {paper.authors.length > 3 && ' et al.'}
                      {paper.publication_year && ` (${paper.publication_year})`}
                      {paper.source && ` • ${paper.source}`}
                      {paper.citation_count > 0 && ` • ${paper.citation_count} citations`}
                    </div>
                    {paper.doi && (
                      <a 
                        href={`https://doi.org/${paper.doi}`} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="paper-link"
                      >
                        DOI: {paper.doi}
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </details>
          )}

          {report && (
            <details className="report-section" open>
              <summary>
                <Download size={14} />
                <span>Full Report</span>
              </summary>
              <div className="report-content">
                <ReactMarkdown>{report}</ReactMarkdown>
              </div>
            </details>
          )}
        </div>

        <div className="message-actions">
          <button 
            className="action-btn" 
            onClick={handleCopy}
            aria-label={copied ? 'Copied!' : 'Copy response'}
            title={copied ? 'Copied!' : 'Copy response'}
          >
            <Copy size={16} />
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {report && (
            <a 
              href={`data:text/markdown;charset=utf-8,${encodeURIComponent(report)}`}
              download={`research-report-${new Date().toISOString().split('T')[0]}.md`}
              className="action-btn download"
            >
              <Download size={16} />
              <span>Download</span>
            </a>
          )}

          <time className="message-time" dateTime={timestamp}>
            {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </time>
        </div>

        {error && (
          <div className="message-error" role="alert">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <span>{error}</span>
          </div>
        )}
      </div>
    </div>
  );
}