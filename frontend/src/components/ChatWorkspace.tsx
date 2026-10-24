import { useCallback, useEffect, useRef, useState } from 'react';

import { Sidebar } from './Sidebar';
import { MessageList } from './MessageList';
import { MessageComposer } from './MessageComposer';
import { WelcomeScreen } from './WelcomeScreen';
import { ResearchPanel } from './ResearchPanel';

import {
  useConversations,
  useResearch,
  useSessionDetail,
  useChat,
} from '../hooks/useApi';

import '../styles/ChatWorkspace.css';

export function ChatWorkspace() {
  // --------------------------------------------------
  // UI STATE
  // --------------------------------------------------

  const [activeConversationId, setActiveConversationId] =
    useState<number | null>(null);

  const [composerValue, setComposerValue] = useState('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showResearchPanel, setShowResearchPanel] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const activeConversationRef = useRef<number | null>(null);
  const requestVersionRef = useRef(0);
  const researchCompletedRef = useRef(false);

  const changeActiveConversation = useCallback(
    (id: number | null) => {
      activeConversationRef.current = id;
      setActiveConversationId(id);
    },
    []
  );

  // Ref to store current research query for auto-rename
  const currentResearchQueryRef = useRef<string>('');

  // --------------------------------------------------
  // CONVERSATIONS
  // --------------------------------------------------

  const {
    conversations,
    loading,
    createConversation,
    deleteConversation,
    updateConversation,
    refetch,
  } = useConversations();

  // --------------------------------------------------
  // RESEARCH WORKFLOW
  // --------------------------------------------------

const {
    startResearch,
    progress,
    result,
    polling,
    error: researchError,
    startPolling,
    stopPolling,
    stopResearch,
    task,
    reset,
  } = useResearch();

  // --------------------------------------------------
  // CHAT
  // --------------------------------------------------

const { 
    messages, 
    setMessages, 
    isGenerating: chatIsGenerating,
    sendMessage,
    error: chatError,
    setConversationId,
    saveResearchResult,
    getResearchResult,
  } = useChat();

  // --------------------------------------------------
  // SESSION DATA
  // --------------------------------------------------

  const {
    sessionDetail,
    refetch: refetchSession,
  } = useSessionDetail(activeConversationId);

  // --------------------------------------------------
  // SCROLLING
  // --------------------------------------------------

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'end',
    });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, progress, scrollToBottom]);

  // --------------------------------------------------
  // RESEARCH RESULT HANDLING
  // --------------------------------------------------

  useEffect(() => {
    if (result && !polling) {
      // Prevent multiple triggers for the same completion
      if (researchCompletedRef.current) return;
      researchCompletedRef.current = true;

      const isFailed = result.status === 'failed' || result.error;

      // Remove the user's research question message
      setMessages(prev => prev.filter(m => 
        !(m.role === 'user' && m.content.startsWith('@research'))
      ));

      // Add research result as a NEW message (not replacing typing)
      const researchMessage = {
        id: crypto.randomUUID(),
        role: 'assistant' as const,
        content: result.content || '',
        timestamp: new Date().toISOString(),
        citations: result.citations,
        papers: result.papers,
        report: result.report,
        metadata: result.metadata,
        current_stage: 'completed' as const,
      };
      setMessages(prev => [...prev, researchMessage]);

      if (
        result.citations?.length ||
        result.papers?.length ||
        result.report
      ) {
        setShowResearchPanel(true);
      }

      // Save research result message to localStorage for persistence
      const currentTask = task;
      if (!isFailed && currentTask?.conversation_id) {
        setMessages((prev) => {
          const researchMessage = prev.find(m => 
            m.metadata?.papers_found
          );
          if (researchMessage && currentTask?.conversation_id) {
            saveResearchResult(currentTask.conversation_id, researchMessage);
          }
          return prev;
        });
      }

      // Auto-close research panel on successful completion
      if (!isFailed) {
        setTimeout(() => setShowResearchPanel(false), 3000);
      }

      // Auto-rename conversation after first research completes
      if (!isFailed && currentTask?.conversation_id) {
        const currentTitle = conversations.find(c => c.id === currentTask.conversation_id)?.title || '';
        const researchQuery = currentResearchQueryRef.current;
        const isDefaultTitle = !currentTitle || 
          currentTitle === '' || 
          currentTitle.startsWith('New Research') ||
          currentTitle === researchQuery.slice(0, 60);
        if (isDefaultTitle && researchQuery) {
          // Generate a better title from the research query
          const newTitle = researchQuery.slice(0, 50) + (researchQuery.length > 50 ? '...' : '');
          updateConversation(currentTask.conversation_id, newTitle).catch(console.error);
        }
      }
    } else if (!result || polling) {
      // Reset the flag when new research starts or polling is active
      researchCompletedRef.current = false;
    }
  }, [result, polling, setMessages, task, conversations, updateConversation]);

  useEffect(() => {
    // Only show research panel during active research (polling)
    // Not during normal chat
    if (polling && !showResearchPanel) {
      setShowResearchPanel(true);
    }
  }, [polling, showResearchPanel]);

  // --------------------------------------------------
  // LOAD SESSION DATA
  // --------------------------------------------------

  useEffect(() => {
    if (activeConversationId !== null) {
      const currentVersion = requestVersionRef.current;
      refetchSession().then(() => {
        // Only process if conversation hasn't changed
        if (currentVersion !== requestVersionRef.current) return;
      });
    }
  }, [activeConversationId, refetchSession]);

  // --------------------------------------------------
  // CONVERT SESSION DATA INTO CHAT MESSAGES
  // --------------------------------------------------

useEffect(() => {
    const currentVersion = requestVersionRef.current;

    if (
      !sessionDetail ||
      activeConversationId === null ||
      (sessionDetail.id !== undefined &&
        sessionDetail.id !== activeConversationId)
    ) {
      return;
    }

    // Check if conversation changed during async loading
    if (currentVersion !== requestVersionRef.current) {
      return;
    }

    // DO NOT auto-open panel on session load
    // Panel only opens during active research (polling) or when user clicks Workflow tab

    // Restore research result message from localStorage
    const savedResearchResult = getResearchResult(activeConversationId);
    if (savedResearchResult) {
      setMessages(prev => {
        const exists = prev.some(m => 
          m.id === savedResearchResult.id && m.metadata?.papers_found
        );
        if (exists) return prev;
        return [...prev, savedResearchResult];
      });
    }
  }, [sessionDetail, activeConversationId, setShowResearchPanel, getResearchResult]);

  // --------------------------------------------------
  // NEW CONVERSATION
  // --------------------------------------------------

  const handleNewConversation = async () => {
    const requestVersion = ++requestVersionRef.current;

    try {
      const conversation = await createConversation('New Research Conversation');

      if (requestVersion !== requestVersionRef.current) {
        return;
      }

      changeActiveConversation(conversation.id);
      setConversationId(conversation.id);
      setMessages([]);
      setComposerValue('');
      setShowResearchPanel(false);
      setSidebarOpen(false);
      stopPolling();
      reset();

      await refetch();
    } catch (error) {
      console.error(
        'Failed to create conversation:',
        error
      );
    }
  };

  // --------------------------------------------------
  // SELECT CONVERSATION
  // --------------------------------------------------

  const handleConversationSelect = (
    conversationId: number
  ) => {
    if (
      activeConversationRef.current === conversationId
    ) {
      setSidebarOpen(false);
      return;
    }

    // Invalidate earlier async operations associated
    // with the previous conversation.
    requestVersionRef.current += 1;

    changeActiveConversation(conversationId);

    // Load chat history for this conversation
    setConversationId(conversationId);

    // Don't clear messages immediately - let session loading effect handle it
    // This prevents flicker/glitch when switching conversations
    setComposerValue('');
    setSidebarOpen(false);

    // Don't immediately close the research panel - let the session loading
    // logic decide whether to show it based on existing research data
    stopPolling();
    reset();
  };

  // --------------------------------------------------
  // SEND CHAT OR RESEARCH MESSAGE
  // --------------------------------------------------

  const handleSendMessage = async (
    content: string,
    isResearch = false
  ) => {
    const trimmedContent = content.trim();

    if (
      !trimmedContent ||
      chatIsGenerating ||
      polling
    ) {
      return;
    }

    // Reset research completion flag for new research
    researchCompletedRef.current = false;

    // Store research query for auto-rename after completion
    if (isResearch) {
      currentResearchQueryRef.current = trimmedContent;
    }

    const requestVersion = requestVersionRef.current;
    let conversationId = activeConversationRef.current;

    try {
      // Create a conversation before submitting a message.
      if (conversationId === null) {
        const conversation = await createConversation(
          trimmedContent.slice(0, 60)
        );

        if (requestVersion !== requestVersionRef.current) {
          return;
        }

        conversationId = conversation.id;
        changeActiveConversation(conversationId);

        await refetch();
      }

      if (!isResearch) {
        // Keep the existing chat hook responsible for
        // message submission and assistant responses.
        setComposerValue('');
        await sendMessage(trimmedContent, false);
        return;
      }

      // Add user message (research question)
      const userMessage = {
        id: crypto.randomUUID(),
        role: 'user' as const,
        content: trimmedContent,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, userMessage]);

      // Auto-rename conversation immediately when research starts (if empty/default title)
      const currentConvId = activeConversationRef.current;
      if (currentConvId) {
        const currentConv = conversations.find(c => c.id === currentConvId);
        const isDefaultTitle = !currentConv?.title || currentConv.title === '' || currentConv.title.startsWith('New Research');
        if (isDefaultTitle) {
          const newTitle = trimmedContent.slice(0, 50) + (trimmedContent.length > 50 ? '...' : '');
          updateConversation(currentConvId, newTitle).catch(console.error);
        }
      }

      // Start the dedicated research workflow.
      setShowResearchPanel(true);

      const task = await startResearch({
        query: trimmedContent,
        conversation_id: conversationId,
      });

      if (requestVersion !== requestVersionRef.current) {
        return;
      }

      if (!task) {
        console.error(
          'Research task could not be started.'
        );
        return;
      }

      // Clear composer only after successful task creation
      setComposerValue('');

      // Use the conversation ID returned by the backend
      // when it provides one.
      if (task.conversation_id) {
        changeActiveConversation(
          task.conversation_id
        );
      }

      startPolling(task.task_id);
    } catch (error) {
      console.error(
        'Failed to submit message:',
        error
      );
    }
  };

  // --------------------------------------------------
  // DELETE CONVERSATION
  // --------------------------------------------------

  const handleDeleteConversation = async (
    conversationId: number
  ) => {
    try {
      await deleteConversation(conversationId);

      if (
        activeConversationRef.current === conversationId
      ) {
        requestVersionRef.current += 1;

        changeActiveConversation(null);
        setConversationId(null);
        setMessages([]);
        setComposerValue('');
        setShowResearchPanel(false);

        stopPolling();
        reset();
      }

      await refetch();
    } catch (error) {
      console.error(
        'Failed to delete conversation:',
        error
      );
    }
  };

  // --------------------------------------------------
  // RENAME CONVERSATION
  // --------------------------------------------------

  const handleConversationRename = async (
    conversationId: number,
    newTitle: string
  ) => {
    const title = newTitle.trim();

    if (!title) {
      return;
    }

    try {
      await updateConversation(
        conversationId,
        title
      );

      await refetch();
    } catch (error) {
      console.error(
        'Failed to rename conversation:',
        error
      );
    }
  };

  // --------------------------------------------------
  // WELCOME SCREEN SUGGESTIONS
  // --------------------------------------------------

  const handleSuggestionClick = async (
    prompt: string
  ) => {
    setComposerValue(prompt);

    await handleSendMessage(prompt, false);
  };

  // --------------------------------------------------
  // CURRENT MESSAGE
  // --------------------------------------------------

  const lastMessage = messages[messages.length - 1];

  // --------------------------------------------------
  // LOADING STATE
  // --------------------------------------------------

  if (loading) {
    return (
      <div className="loading-screen">
        Loading conversations...
      </div>
    );
  }

  // --------------------------------------------------
  // MAIN UI
  // --------------------------------------------------

  return (
    <div className="chat-workspace">
      <Sidebar
        collapsed={sidebarCollapsed}
        open={sidebarOpen}
        onToggleCollapse={() =>
          setSidebarCollapsed((value) => !value)
        }
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewConversation={handleNewConversation}
        onConversationSelect={handleConversationSelect}
        onConversationDelete={handleDeleteConversation}
        onConversationRename={handleConversationRename}
      />

      <main
        className="main-area"
        style={{
          marginLeft: sidebarCollapsed
            ? '72px'
            : '280px',
          marginRight: showResearchPanel
            ? '320px'
            : '0',
        }}
      >
        {activeConversationId === null ? (
          <WelcomeScreen
            onSuggestionClick={handleSuggestionClick}
          />
        ) : (
          <div className="chat-container">
            {/* Header */}
            <header className="chat-header">
              <div className="chat-header-left">
                <button
                  type="button"
                  className="sidebar-toggle-btn"
                  onClick={() =>
                    setSidebarCollapsed(
                      (value) => !value
                    )
                  }
                  aria-label={
                    sidebarCollapsed
                      ? 'Expand sidebar'
                      : 'Collapse sidebar'
                  }
                >
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    aria-hidden="true"
                  >
                    {sidebarCollapsed ? (
                      <>
                        <line
                          x1="9"
                          y1="18"
                          x2="15"
                          y2="12"
                        />
                        <line
                          x1="15"
                          y1="6"
                          x2="9"
                          y2="12"
                        />
                      </>
                    ) : (
                      <>
                        <line
                          x1="15"
                          y1="18"
                          x2="9"
                          y2="12"
                        />
                        <line
                          x1="9"
                          y1="6"
                          x2="15"
                          y2="12"
                        />
                      </>
                    )}
                  </svg>
                </button>

                <h1>
                  {conversations.find(
                    (conversation) =>
                      conversation.id ===
                      activeConversationId
                  )?.title ?? 'Research Session'}
                </h1>
              </div>

              <div className="chat-status">
                <span
                  className={`status-indicator ${
                    researchError || chatError
                      ? 'error'
                      : ''
                  }`}
                />

                <span>
                  NVIDIA Nemotron-3-Ultra
                </span>
              </div>
            </header>

            {/* Session navigation */}
            {sessionDetail && (
              <nav
                className="session-tabs"
                aria-label="Research session navigation"
              >
                <button
                  type="button"
                  className={`session-tab ${
                    !showResearchPanel ? 'active' : ''
                  }`}
                  onClick={() => setShowResearchPanel(false)}
                >
                  Chat
                </button>

                <button
                  type="button"
                  className={`session-tab ${
                    showResearchPanel ? 'active' : ''
                  }`}
                  onClick={() =>
                    setShowResearchPanel(true)
                  }
                >
                  Workflow
                  {polling && (
                    <span className="tab-badge">
                      Live
                    </span>
                  )}
                </button>
              </nav>
            )}

            {/* Messages */}
            <div className="messages-area">
              <MessageList
                messages={messages}
                progress={progress}
                isGenerating={
                  chatIsGenerating || Boolean(polling)
                }
                researchError={
                  researchError || undefined
                }
              />

              <div ref={messagesEndRef} />
            </div>

            {/* Composer */}
            <MessageComposer
              value={composerValue}
              onChange={setComposerValue}
              onSend={handleSendMessage}
              disabled={
                chatIsGenerating || Boolean(polling)
              }
              placeholder="Ask a research question... (Enter: send, Shift+Enter: new line)"
            />
          </div>
        )}
      </main>

      {/* Research panel */}
      {showResearchPanel && (
        <ResearchPanel
          progress={progress}
          isGenerating={
            chatIsGenerating || Boolean(polling)
          }
          polling={polling}
          result={lastMessage}
          error={researchError || undefined}
          onClose={() =>
            setShowResearchPanel(false)
          }
          setShowResearchPanel={setShowResearchPanel}
          onStop={() => stopResearch(() => {
            setShowResearchPanel(false);
            // Add stop message to chat
            const stopMessage = {
              id: crypto.randomUUID(),
              role: 'assistant' as const,
              content: 'Research stopped by user.',
              timestamp: new Date().toISOString(),
            };
            setMessages(prev => [...prev, stopMessage]);
          })}
        />
      )}

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          role="presentation"
        />
      )}
    </div>
  );
}

export default ChatWorkspace;