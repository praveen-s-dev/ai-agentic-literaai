import { useState } from 'react';
import { 
  Plus, Search, Edit, Trash2, Settings, ChevronLeft, ChevronRight 
} from 'lucide-react';
import type { Conversation } from '../types';
import '../styles/Sidebar.css';

interface SidebarProps {
  collapsed: boolean;
  open: boolean;
  onToggleCollapse: () => void;
  conversations: Conversation[];
  activeConversationId: number | null;
  onNewConversation: () => void;
  onConversationSelect: (id: number) => void;
  onConversationDelete: (id: number) => void;
  onConversationRename: (id: number, newTitle: string) => void;
}

export function Sidebar({
  collapsed,
  open,
  onToggleCollapse,
  conversations,
  activeConversationId,
  onNewConversation,
  onConversationSelect,
  onConversationDelete,
  onConversationRename,
}: SidebarProps) {
  const [expandedSections, setExpandedSections] = useState({
    today: true,
    week: true,
    older: true,
  });
  const [renamingId, setRenamingId] = useState<number | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const today = new Date();
  const weekAgo = new Date(today);
  weekAgo.setDate(today.getDate() - 7);

  const filteredConversations = conversations.filter(conv =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const groupedConversations = filteredConversations.reduce((acc, conv) => {
    const convDate = new Date(conv.updated_at);
    const dateStr = convDate.toDateString();
    const todayStr = today.toDateString();

    if (dateStr === todayStr) {
      acc.today.push(conv);
    } else if (convDate >= weekAgo) {
      acc.week.push(conv);
    } else {
      acc.older.push(conv);
    }
    return acc;
  }, { today: [] as Conversation[], week: [] as Conversation[], older: [] as Conversation[] });

  const handleRenameStart = (conv: Conversation) => {
    setRenamingId(conv.id);
    setRenameValue(conv.title);
  };

  const handleRenameSave = async (id: number) => {
    if (renameValue.trim()) {
      await onConversationRename(id, renameValue.trim());
      setRenamingId(null);
    }
  };

  const handleDeleteConfirm = (id: number) => {
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      onConversationDelete(id);
    }
    setDeletingId(null);
  };

  return (
    <aside 
      className={`sidebar ${collapsed ? 'collapsed' : ''} ${open ? 'open' : ''}`}
      role="navigation"
      aria-label="Conversation history"
    >
      <header className="sidebar-header">
        <div className="sidebar-brand">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          {!collapsed && <span className="brand-text">Research Assistant</span>}
        </div>
        <button 
          className="collapse-btn" 
          onClick={onToggleCollapse}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </header>

      {!collapsed && (
        <>
          <button className="new-conversation-btn" onClick={onNewConversation}>
            <Plus size={14} />
            <span>New Research</span>
          </button>

          <div className="search-container">
            <Search size={16} className="search-icon" />
            <input 
              type="text" 
              placeholder="Search conversations..." 
              className="search-input"
              aria-label="Search conversations"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <nav className="conversation-list" aria-label="Conversations">
            {groupedConversations.today.length > 0 && (
              <ConversationSection
                title="Today"
                conversations={groupedConversations.today}
                expanded={expandedSections.today}
                onToggle={() => setExpandedSections(prev => ({ ...prev, today: !prev.today }))}
                activeConversationId={activeConversationId}
                onSelect={onConversationSelect}
                onRename={handleRenameStart}
                renamingId={renamingId}
                renameValue={renameValue}
                setRenameValue={setRenameValue}
                setRenamingId={setRenamingId}
                onRenameSave={handleRenameSave}
                deletingId={deletingId}
                setDeletingId={setDeletingId}
                onDeleteConfirm={handleDeleteConfirm}
              />
            )}

            {groupedConversations.week.length > 0 && (
              <ConversationSection
                title="Previous 7 Days"
                conversations={groupedConversations.week}
                expanded={expandedSections.week}
                onToggle={() => setExpandedSections(prev => ({ ...prev, week: !prev.week }))}
                activeConversationId={activeConversationId}
                onSelect={onConversationSelect}
                onRename={handleRenameStart}
                renamingId={renamingId}
                renameValue={renameValue}
                setRenameValue={setRenameValue}
                setRenamingId={setRenamingId}
                onRenameSave={handleRenameSave}
                deletingId={deletingId}
                setDeletingId={setDeletingId}
                onDeleteConfirm={handleDeleteConfirm}
              />
            )}

            {groupedConversations.older.length > 0 && (
              <ConversationSection
                title="Older"
                conversations={groupedConversations.older}
                expanded={expandedSections.older}
                onToggle={() => setExpandedSections(prev => ({ ...prev, older: !prev.older }))}
                activeConversationId={activeConversationId}
                onSelect={onConversationSelect}
                onRename={handleRenameStart}
                renamingId={renamingId}
                renameValue={renameValue}
                setRenameValue={setRenameValue}
                setRenamingId={setRenamingId}
                onRenameSave={handleRenameSave}
                deletingId={deletingId}
                setDeletingId={setDeletingId}
                onDeleteConfirm={handleDeleteConfirm}
              />
            )}
          </nav>
        </>
      )}

      <footer className="sidebar-footer">
        {!collapsed && (
          <button className="settings-btn" onClick={() => alert('Settings coming soon')}>
            <Settings size={18} />
            <span>Settings</span>
          </button>
        )}
      </footer>
    </aside>
  );
}

interface ConversationSectionProps {
  title: string;
  conversations: Conversation[];
  expanded: boolean;
  onToggle: () => void;
  activeConversationId: number | null;
  onSelect: (id: number) => void;
  onRename: (conv: Conversation) => void;
  renamingId: number | null;
  renameValue: string;
  setRenameValue: (value: string) => void;
  setRenamingId: (id: number | null) => void;
  onRenameSave: (id: number) => void;
  deletingId: number | null;
  setDeletingId: (id: number | null) => void;
  onDeleteConfirm: (id: number) => void;
}

function ConversationSection({
  title,
  conversations,
  expanded,
  onToggle,
  activeConversationId,
  onSelect,
  onRename,
  renamingId,
  renameValue,
  setRenameValue,
  setRenamingId,
  onRenameSave,
  deletingId,
  setDeletingId,
  onDeleteConfirm,
}: ConversationSectionProps) {
  return (
    <section className="conversation-section">
      <button 
        className="section-header" 
        onClick={onToggle}
        aria-expanded={expanded}
      >
        <span className="section-title">{title}</span>
        <ChevronRight size={14} className={expanded ? 'expanded' : ''} />
      </button>

      {expanded && (
        <ul className="conversation-list" role="list">
          {conversations.map(conv => (
            <ConversationItem
              key={conv.id}
              conversation={conv}
              isActive={activeConversationId === conv.id}
              onSelect={() => onSelect(conv.id)}
              onRename={onRename}
              renamingId={renamingId}
              renameValue={renameValue}
              setRenameValue={setRenameValue}
              setRenamingId={setRenamingId}
              onRenameSave={onRenameSave}
              deletingId={deletingId}
              setDeletingId={setDeletingId}
              onDeleteConfirm={onDeleteConfirm}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onRename: (conv: Conversation) => void;
  renamingId: number | null;
  renameValue: string;
  setRenameValue: (value: string) => void;
  setRenamingId: (id: number | null) => void;
  onRenameSave: (id: number) => void;
  deletingId: number | null;
  setDeletingId: (id: number | null) => void;
  onDeleteConfirm: (id: number) => void;
}

function ConversationItem({
  conversation,
  isActive,
  onSelect,
  onRename,
  renamingId,
  renameValue,
  setRenameValue,
  setRenamingId,
  onRenameSave,
  deletingId,
  setDeletingId,
  onDeleteConfirm,
}: ConversationItemProps) {
  const isRenaming = renamingId === conversation.id;
  const isDeleting = deletingId === conversation.id;

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (isRenaming) {
      if (e.key === 'Enter') onRenameSave(conversation.id);
      if (e.key === 'Escape') setRenamingId(null);
    }
  };

  return (
    <li className={`conversation-item ${isActive ? 'active' : ''}`} role="listitem">
      {isRenaming ? (
        <input
          type="text"
          value={renameValue}
          onChange={e => setRenameValue(e.target.value)}
          onBlur={() => onRenameSave(conversation.id)}
          onKeyDown={handleKeyDown}
          autoFocus
          className="rename-input"
        />
      ) : (
        <div className="conversation-button" onClick={onSelect} role="button" tabIndex={0} aria-current={isActive ? 'true' : 'false'} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(); } }}>
          <div className="conversation-content">
            <span className="conversation-title" title={conversation.title}>
              {conversation.title}
            </span>
            <span className="conversation-date">
              {new Date(conversation.updated_at).toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </span>
          </div>
          <div className="conversation-menu">
            <button 
              className="menu-btn"
              onClick={(e) => { e.stopPropagation(); onRename(conversation); }}
              aria-label="Rename"
            >
              <Edit size={14} />
            </button>
            <button 
              className="menu-btn danger"
              onClick={(e) => { e.stopPropagation(); setDeletingId(conversation.id); }}
              aria-label="Delete"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>
      )}

      {isDeleting && (
        <div className="delete-confirm">
          <span>Delete this conversation?</span>
          <div className="delete-actions">
            <button onClick={() => setDeletingId(null)}>Cancel</button>
            <button className="confirm" onClick={() => onDeleteConfirm(conversation.id)}>Delete</button>
          </div>
        </div>
      )}
    </li>
  );
}