import { useState, useEffect, useRef } from 'react';
import { Sidebar } from './Sidebar';
import { MessageList } from './MessageList';
import { MessageComposer } from './MessageComposer';
import { WelcomeScreen } from './WelcomeScreen';
import { ResearchPanel } from './ResearchPanel';
import { 
  useConversations, 
  useResearch, 
  useSessionDetail, 
  usePapers, 
  useAnalyses, 
  useGaps, 
  useEvidence, 
  useReport,
  useChat
} from '../hooks/useApi';
import type { Citation, Paper, ResearchStage } from '../types';
import '../styles/ChatWorkspace.css';

export function ChatWorkspace() {
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [composerValue, setComposerValue] = useState('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showResearchPanel, setShowResearchPanel] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const { 
    conversations, 
    loading, 
    createConversation, 
    deleteConversation, 
    updateConversation, 
    refetch 
  } = useConversations();
  
  const { 
    startResearch, 
    progress, 
    result, 
    polling, 
    error: researchError, 
    startPolling, 
    reset 
  } = useResearch();
  
  const { 
    messages, 
    setMessages, 
    isGenerating: chatIsGenerating,
    setIsGenerating: setChatIsGenerating,
    sendMessage,
    error: chatError 
  } = useChat();
  
  const { sessionDetail, refetch: refetchSession } = useSessionDetail(activeConversationId);
  const { papers } = usePapers(activeConversationId);
  const { analyses } = useAnalyses(activeConversationId);
  const { gaps } = useGaps(activeConversationId);
  const { evidence } = useEvidence(activeConversationId);
  const { report } = useReport(activeConversationId);
  
  const [composerValue, setComposerValue] = useState('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showResearchPanel, setShowResearchPanel] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, progress]);

  useEffect(() => {
    if (result && !polling && polling !== undefined) {
      setMessages(prev => prev.map(msg => 
        msg.is_typing ? { ...msg, ...result, is_typing: false } : msg
      ));
      if (result.citations?.length || result.papers?.length || result.report) {
        setShowResearchPanel(true);
      }
    }
    if ((chatIsGenerating || polling) && !showResearchPanel) {
      setShowResearchPanel(true);
    }
  }, [result, polling, chatIsGenerating, showResearchPanel]);

  // Load session data when conversation changes
  useEffect(() => {
    if (activeConversationId) {
      refetchSession();
    }
  }, [activeConversationId, refetchSession]);

  // Close research panel when conversation changes (including when set to null)
  useEffect(() => {
    if (activeConversationId === null) {
      setShowResearchPanel(false);
    }
  }, [activeConversationId]);

const handleSendMessage = async (content: string, isResearch: boolean = false) => {
    if (!content.trim() || chatIsGenerating) return;

    if (isResearch) {
      // Use research workflow
      setShowResearchPanel(true);

      const task = await startResearch({
        query: content,
        conversation_id: activeConversationId || undefined,
      });

      if (task) {
        startPolling(task.task_id);
        
        if (!activeConversationId && task.conversation_id) {
          const newConv = await createConversation(content.slice(0, 60));
          setActiveConversationId(newConv.id);
          refetch();
        }
      } else {
        // Use chat API for regular chat
        sendMessage(content, false);
      }
    };

  const handleNewConversation = async () => {
    const conv = await createConversation('New Research Session');
    setActiveConversationId(conv.id);
    setMessages([]);
    reset();
    setShowResearchPanel(false);
    refetch();
  };

  const handleConversationSelect = async (convId: number) => {
    setActiveConversationId(convId);
    setMessages([]);
    reset();
    setShowResearchPanel(false);
    // Force close research panel
    // The session detail will be loaded via useEffect
    // Also reset research state to ensure panel closes
  };

  // Load previous conversation data when session detail loads
  useEffect(() => {
    if (sessionDetail && activeConversationId) {
      // Convert session data to messages
      const sessionMessages: Array<{
        id: string;
        role: 'user' | 'assistant';
        content: string;
        timestamp: string;
        citations?: Citation[];
        papers?: Paper[];
        report?: string;
        metadata?: Record<string, any>;
        current_stage?: ResearchStage;
        is_typing?: boolean;
        error?: string;
      }> = [];

      // Add the initial research question as user message
      if (sessionDetail.research_question) {
        sessionMessages.push({
          id: crypto.randomUUID(),
          role: 'user',
          content: sessionDetail.research_question,
          timestamp: sessionDetail.created_at,
        });
      }

      // If there are analyses, create an assistant message with results
      if (sessionDetail.analyses && sessionDetail.analyses.length > 0) {
        const papers = sessionDetail.papers || [];
        const citations = papers.slice(0, 10).map(p => ({
          title: p.title,
          authors: p.authors.map(a => a.name),
          year: p.publication_year,
          doi: p.doi,
          url: p.url,
          source: p.source,
          citations: p.citation_count,
        }));

        let content = `## Research Summary\n\n`;
        content += `I found **${sessionDetail.papers?.length || 0} papers** related to your query. `;
        content += `Analyzed **${sessionDetail.analyses.length} papers** in detail.\n\n`;

        if (papers.length > 0) {
          content += `### 📚 Relevant Papers\n`;
          papers.slice(0, 5).forEach((paper, i) => {
            const authors = paper.authors.slice(0, 3).map(a => a.name).join(', ');
            content += `${i + 1}. **${paper.title}** (${paper.publication_year || 'N/A'})  \n`;
            content += `   *${authors}* • ${paper.citation_count} citations • ${paper.source}\n`;
            if (paper.doi) content += `   DOI: ${paper.doi}\n`;
            content += `\n`;
          });
        }

        if (sessionDetail.gaps && sessionDetail.gaps.length > 0) {
          content += `### 💡 Candidate Research Gaps\n`;
          sessionDetail.gaps.slice(0, 3).forEach((gap, i) => {
            content += `${i + 1}. **${gap.gap_statement || gap.title}** (Evidence: ${gap.evidence_strength}/100)\n`;
            content += `   *Direction:* ${gap.potential_research_direction?.slice(0, 150)}...\n\n`;
          });
        }

        if (sessionDetail.report) {
          content += `### 📄 Full Report\n`;
          content += `A comprehensive research report has been generated with full evidence traceability. `;
          content += `Use the actions below to view or download it.\n`;
        }

        sessionMessages.push({
          id: crypto.randomUUID(),
          role: 'assistant',
          content,
          timestamp: sessionDetail.updated_at,
          citations: citations.length > 0 ? citations : undefined,
          papers: papers.slice(0, 10).map(p => ({
            id: p.id,
            session_id: p.session_id || 0,
            title: p.title,
            abstract: p.abstract,
            source: p.source,
            source_id: p.source_id,
            doi: p.doi,
            url: p.url,
            publication_year: p.publication_year,
            venue: p.venue,
            citation_count: p.citation_count,
            downloaded: p.downloaded || 0,
            processed: p.processed || 0,
            created_at: p.created_at,
            updated_at: p.updated_at,
            authors: p.authors.map(a => ({
              id: a.id,
              name: a.name,
              affiliation: a.affiliation,
              orcid: a.orcid,
            })),
          })),
          report: sessionDetail.report,
          metadata: {
            papers_found: sessionDetail.papers?.length || 0,
            papers_analyzed: sessionDetail.analyses?.length || 0,
            gaps_found: sessionDetail.gaps?.length || 0,
            has_report: !!sessionDetail.report,
          },
          current_stage: 'completed',
        });
      }

      setMessages(sessionMessages);
    }
  }, [sessionDetail, activeConversationId]);

  const handleDeleteConversation = async (convId: number) => {
    await deleteConversation(convId);
    if (activeConversationId === convId) {
      setActiveConversationId(null);
      setMessages([]);
      reset();
      setShowResearchPanel(false);
    }
    refetch();
  };

  const handleConversationRename = async (convId: number, newTitle: string) => {
    await updateConversation(convId, newTitle);
    refetch();
  };

  const handleSuggestionClick = async (prompt: string) => {
    if (!activeConversationId) {
      const conv = await createConversation(prompt.slice(0, 60));
      setActiveConversationId(conv.id);
      refetch();
    }
    setComposerValue(prompt);
    handleSendMessage(prompt);
  };

  const lastMessage = messages[messages.length - 1];

  if (loading) {
    return <div className="loading-screen">Loading conversations...</div>;
  };

  return (
    <div className="chat-workspace">
      <Sidebar
        collapsed={sidebarCollapsed}
        open={sidebarOpen}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewConversation={handleNewConversation}
        onConversationSelect={handleConversationSelect}
        onConversationDelete={handleDeleteConversation}
        onConversationRename={handleConversationRename}
      />
      
      <main className="main-area" style={{ 
        marginLeft: sidebarCollapsed ? '72px' : '280px',
        marginRight: showResearchPanel ? '320px' : '0'
      }}>
        {activeConversationId === null ? (
          <WelcomeScreen onSuggestionClick={handleSuggestionClick} />
        ) : (
          <div className="chat-container">
            <header className="chat-header">
              <div className="chat-header-left">
                <button 
                  className="sidebar-toggle-btn"
                  onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                  aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    {sidebarCollapsed ? (
                      <>
                        <line x1="9" y1="18" x2="15" y2="12"/>
                        <line x1="15" y1="6" x2="9" y2="12"/>
                      </>
                    ) : (
                      <>
                        <line x1="15" y1="18" x2="9" y2="12"/>
                        <line x1="9" y1="6" x2="15" y2="12"/>
                      </>
                    )}
                  </svg>
                </button>
                <h1>{conversations.find(c => c.id === activeConversationId)?.title || 'Research Session'}</h1>
              </div>
              <div className="chat-status">
                <span className={`status-indicator ${researchError ? 'error' : ''}`}></span>
                <span>NVIDIA Nemotron-3-Ultra</span>
              </div>
            </header>

            {/* Session Data Tabs */}
            {sessionDetail && (
              <div className="session-tabs">
                <button className={`session-tab ${!showResearchPanel ? 'active' : ''}`} onClick={() => setShowResearchPanel(false)}>
                  Chat
                </button>
                <button className={`session-tab ${showResearchPanel ? 'active' : ''}`} onClick={() => setShowResearchPanel(true)}>
                  Workflow
                  {isGenerating && <span className="tab-badge">Live</span>}
                </button>
                {papers.length > 0 && (
                  <button className="session-tab" onClick={() => { setShowResearchPanel(false); }}>Papers ({papers.length})</button>
                )}
                {analyses.length > 0 && (
                  <button className="session-tab" onClick={() => { setShowResearchPanel(false); }}>Analyses ({analyses.length})</button>
                )}
                {gaps.length > 0 && (
                  <button className="session-tab" onClick={() => { setShowResearchPanel(false); }}>Gaps ({gaps.length})</button>
                )}
                {evidence.length > 0 && (
                  <button className="session-tab" onClick={() => { setShowResearchPanel(false); }}>Evidence ({evidence.length})</button>
                )}
                {report && (
                  <button className="session-tab" onClick={() => { setShowResearchPanel(false); }}>Report</button>
                )}
              </div>
            )}

            <div className="messages-area">
              <MessageList
                messages={messages}
                progress={progress}
                isGenerating={isGenerating}
                researchError={researchError}
              />
              <div ref={messagesEndRef} />
            </div>

            <MessageComposer
              value={composerValue}
              onChange={setComposerValue}
              onSend={handleSendMessage}
              disabled={chatIsGenerating || polling}
              placeholder="Ask a research question... (Shift+Enter for new line, Enter to send)"
            />
          </div>
        )}
      </main>

      {/* Right Research Panel */}
      {showResearchPanel && (
        <ResearchPanel
          progress={progress}
          isGenerating={chatIsGenerating || polling}
          result={lastMessage}
          onClose={() => setShowResearchPanel(false)}
        />
      )}

      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      )}
    </div>
