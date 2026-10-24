"""
Premium ChatGPT-Style Research Assistant
A polished, evidence-grounded conversational AI for academic literature investigation.

Architecture:
- Streamlit frontend with custom CSS for premium ChatGPT-style UI
- LangGraph multi-agent workflow for research orchestration
- NVIDIA API for LLM inference (Nemotron-3-Ultra)
- OpenAlex, Semantic Scholar, Crossref, arXiv for paper retrieval
- RAG with ChromaDB + BGE embeddings
- SQLite for persistence
- PDF processing with PyMuPDF
"""

import streamlit as st
import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
from copy import deepcopy

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.logging_config import setup_logging
from agents.search_agent import PaperSearchAgent
from agents.paper_analysis_agent import PaperAnalysisAgent
from agents.cross_paper_agent import CrossPaperAgent
from agents.research_gap_agent import ResearchGapAgent
from academic.schemas import PaperSource, Paper
from reports.report_generator import ReportGenerator
from database.connection import init_db, get_session
from database.models import ResearchSession, ResearchSessionStatus, Paper as PaperModel
from papers.storage import (
    save_papers_to_session, get_papers_with_authors, get_chunks_by_paper, save_chunks_to_paper
)
from papers.downloader import PDFDownloader
from papers.pdf_processor import PDFProcessor
from papers.chunker import TextChunker, TextChunk
from rag.vector_store import VectorStore
from rag.embeddings import get_embedding_model

# ═══════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════
# PREMIUM CSS - ChatGPT-Style Design System
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ════════════════════════════════════════════════════════════════
   DESIGN TOKENS - CSS Custom Properties
════════════════════════════════════════════════════════════════════ */
:root {
    /* Colors - Light Theme */
    --color-bg-primary: #ffffff;
    --color-bg-secondary: #f7f7f8;
    --color-bg-tertiary: #f0f0f1;
    --color-bg-hover: #e8e8e9;
    --color-bg-input: #ffffff;
    --color-text-primary: #1f2937;
    --color-text-secondary: #6b7280;
    --color-text-muted: #9ca3af;
    --color-text-inverse: #ffffff;
    --color-border: #e5e5e5;
    --color-border-hover: #d1d5db;
    --color-border-focus: #10a37f;
    --color-accent: #10a37f;
    --color-accent-hover: #0d8f6f;
    --color-accent-light: #d1fae5;
    --color-accent-muted: rgba(16, 163, 127, 0.1);
    --color-user-msg: #f7f7f8;
    --color-assistant-msg: #ffffff;
    --color-danger: #ef4444;
    --color-warning: #f59e0b;
    --color-info: #3b82f6;
    
    /* Shadows */
    --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.03);
    --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.08);
    --shadow-xl: 0 16px 48px rgba(0, 0, 0, 0.1);
    
    /* Radius */
    --radius-xs: 4px;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 24px;
    --radius-full: 9999px;
    
    /* Spacing */
    --space-1: 4px;
    --space-2: 8px;
    --space-3: 12px;
    --space-4: 16px;
    --space-5: 20px;
    --space-6: 24px;
    --space-8: 32px;
    --space-10: 40px;
    --space-12: 48px;
    
    /* Layout */
    --sidebar-width: 280px;
    --sidebar-collapsed-width: 64px;
    --max-chat-width: 768px;
    --composer-height: 56px;
    --header-height: 56px;
    
    /* Typography */
    --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    --font-mono: 'SF Mono', 'Fira Code', 'Fira Mono', Menlo, Consolas, monospace;
    --text-xs: 0.75rem;     /* 12px */
    --text-sm: 0.8125rem;   /* 13px */
    --text-base: 0.875rem;  /* 14px */
    --text-lg: 1rem;        /* 16px */
    --text-xl: 1.125rem;    /* 18px */
    --text-2xl: 1.25rem;    /* 20px */
    --text-3xl: 1.5rem;     /* 24px */
    --text-4xl: 2rem;       /* 32px */
    
    /* Transitions */
    --transition-fast: 120ms ease;
    --transition-base: 200ms ease;
    --transition-slow: 300ms ease;
}

/* Dark Theme */
@media (prefers-color-scheme: dark) {
    :root {
        --color-bg-primary: #171717;
        --color-bg-secondary: #1f1f1f;
        --color-bg-tertiary: #2a2a2a;
        --color-bg-hover: #333333;
        --color-bg-input: #1f1f1f;
        --color-text-primary: #fafafa;
        --color-text-secondary: #a1a1aa;
        --color-text-muted: #71717a;
        --color-border: #27272a;
        --color-border-hover: #3f3f46;
        --color-border-focus: #10a37f;
        --color-accent: #10a37f;
        --color-accent-hover: #14b886;
        --color-accent-light: #064e3b;
        --color-accent-muted: rgba(16, 163, 127, 0.15);
        --color-user-msg: #1f1f1f;
        --color-assistant-msg: #171717;
        --color-danger: #f87171;
        --color-warning: #fbbf24;
        --color-info: #60a5fa;
    }
}

/* ════════════════════════════════════════════════════════════════
   RESET & BASE
═══════════════════════════════════════════════════════════════════ */
* { box-sizing: border-box; }

#MainMenu, footer, header, .stDeployButton { display: none !important; }

.main .block-container {
    padding: 0;
    max-width: 100%;
    min-height: 100vh;
}

/* Streamlit overrides */
.stButton > button {
    border-radius: var(--radius-sm);
    font-weight: 500;
    transition: all var(--transition-fast);
    border: 1px solid transparent;
}

.stButton > button[kind="primary"] {
    background: var(--color-accent);
    color: var(--color-text-inverse);
    border-color: var(--color-accent);
}
.stButton > button[kind="primary"]:hover {
    background: var(--color-accent-hover);
    border-color: var(--color-accent-hover);
}

.stButton > button[kind="secondary"] {
    background: transparent;
    color: var(--color-text-primary);
    border-color: var(--color-border);
}
.stButton > button[kind="secondary"]:hover {
    background: var(--color-bg-hover);
    border-color: var(--color-border-hover);
}

.stTextArea textarea {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--color-border) !important;
    background: var(--color-bg-input) !important;
    color: var(--color-text-primary) !important;
    font-family: var(--font-sans) !important;
    font-size: var(--text-base) !important;
    line-height: 1.5 !important;
    padding: var(--space-3) var(--space-4) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all var(--transition-fast) !important;
}
.stTextArea textarea:focus {
    border-color: var(--color-border-focus) !important;
    box-shadow: 0 0 0 3px var(--color-accent-muted) !important;
    outline: none !important;
}

.stTextArea textarea::placeholder {
    color: var(--color-text-muted) !important;
}

.stSelectbox > div > div,
.stMultiSelect > div > div {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--color-border) !important;
    background: var(--color-bg-input) !important;
}

.stSlider > div > div > div {
    color: var(--color-accent) !important;
}

.stExpander {
    border: 1px solid var(--color-border) !important;
    border-radius: var(--radius-md) !important;
    background: var(--color-bg-primary) !important;
}
.stExpander summary {
    font-weight: 500 !important;
    color: var(--color-text-primary) !important;
}

.stMarkdown, .stText {
    color: var(--color-text-primary) !important;
}

.stCaption {
    color: var(--color-text-muted) !important;
    font-size: var(--text-xs) !important;
}

.stAlert {
    border-radius: var(--radius-md) !important;
}

.stDownloadButton > button {
    border-radius: var(--radius-sm) !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--color-border-hover); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--color-text-muted); }
::-webkit-scrollbar-corner { background: transparent; }

/* Selection */
::selection {
    background: var(--color-accent-light);
    color: var(--color-accent);
}

/* Focus visible */
:focus-visible {
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
}

/* ════════════════════════════════════════════════════════════════
   LAYOUT COMPONENTS
═══════════════════════════════════════════════════════════════════ */

/* App Layout */
.app-layout {
    display: grid;
    grid-template-columns: var(--sidebar-width) 1fr;
    grid-template-rows: var(--header-height) 1fr var(--composer-height);
    grid-template-areas:
        "sidebar header"
        "sidebar chat"
        "sidebar composer";
    height: 100vh;
    min-height: 100vh;
    background: var(--color-bg-primary);
}

.app-layout.sidebar-collapsed {
    grid-template-columns: var(--sidebar-collapsed-width) 1fr;
}

/* Sidebar */
.sidebar {
    grid-area: sidebar;
    background: var(--color-bg-secondary);
    border-right: 1px solid var(--color-border);
    display: flex;
    flex-direction: column;
    height: 100vh;
    position: sticky;
    top: 0;
    z-index: 100;
    transition: width var(--transition-base);
    overflow: hidden;
}

.sidebar.collapsed .sidebar-content {
    display: none;
}

.sidebar.collapsed .sidebar-header {
    justify-content: center;
    padding: var(--space-3);
}

.sidebar-header {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-4);
    border-bottom: 1px solid var(--color-border);
    height: var(--header-height);
}

.sidebar-logo {
    width: 36px;
    height: 36px;
    border-radius: var(--radius-md);
    background: linear-gradient(135deg, var(--color-accent), #0d8f6f);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
}

.sidebar-title {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--color-text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.sidebar-content {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-3);
}

.sidebar-section {
    margin-bottom: var(--space-5);
}

.sidebar-section-title {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: var(--space-2);
    padding: 0 var(--space-2);
}

.sidebar-btn {
    width: 100%;
    justify-content: flex-start;
    background: transparent;
    border: none;
    color: var(--color-text-primary);
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-sm);
    font-size: var(--text-sm);
    font-weight: 400;
    text-align: left;
    gap: var(--space-2);
    transition: all var(--transition-fast);
}
.sidebar-btn:hover {
    background: var(--color-bg-hover);
}
.sidebar-btn.primary {
    background: var(--color-accent);
    color: white;
    font-weight: 500;
}
.sidebar-btn.primary:hover {
    background: var(--color-accent-hover);
}

.sidebar-divider {
    height: 1px;
    background: var(--color-border);
    margin: var(--space-3) 0;
}

/* Conversation Items */
.conv-item {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-sm);
    margin: var(--space-1) 0;
    cursor: pointer;
    transition: all var(--transition-fast);
    position: relative;
}
.conv-item:hover {
    background: var(--color-bg-hover);
}
.conv-item.active {
    background: var(--color-accent-light);
}
.conv-item.active .conv-item-title {
    font-weight: 500;
}

.conv-item-icon {
    width: 28px;
    height: 28px;
    border-radius: var(--radius-sm);
    background: var(--color-bg-tertiary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    flex-shrink: 0;
    color: var(--color-text-secondary);
}

.conv-item-content {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 1px;
}

.conv-item-title {
    font-size: var(--text-sm);
    font-weight: 400;
    color: var(--color-text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.conv-item-date {
    font-size: var(--text-xs);
    color: var(--color-text-muted);
}

.conv-item-menu {
    opacity: 0;
    transition: opacity var(--transition-fast);
    flex-shrink: 0;
}
.conv-item:hover .conv-item-menu {
    opacity: 1;
}
.conv-item-menu-btn {
    background: transparent;
    border: none;
    color: var(--color-text-muted);
    padding: var(--space-1);
    border-radius: var(--radius-xs);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
}
.conv-item-menu-btn:hover {
    color: var(--color-text-primary);
    background: var(--color-bg-hover);
}

/* Conversation Menu Dropdown */
.conv-menu-dropdown {
    position: absolute;
    right: 0;
    top: 100%;
    margin-top: var(--space-1);
    background: var(--color-bg-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
    min-width: 160px;
    z-index: 200;
    padding: var(--space-1);
    animation: fadeIn var(--transition-fast);
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
}
.conv-menu-item {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-sm);
    color: var(--color-text-primary);
    font-size: var(--text-sm);
    cursor: pointer;
    transition: background var(--transition-fast);
}
.conv-menu-item:hover {
    background: var(--color-bg-hover);
}
.conv-menu-item.danger {
    color: var(--color-danger);
}
.conv-menu-divider {
    height: 1px;
    background: var(--color-border);
    margin: var(--space-1) 0;
}

/* Chat Area */
.chat-area {
    grid-area: chat;
    display: flex;
    flex-direction: column;
    height: calc(100vh - var(--header-height) - var(--composer-height));
    overflow: hidden;
    background: var(--color-bg-primary);
}

.chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 var(--space-6);
    height: var(--header-height);
    border-bottom: 1px solid var(--color-border);
    background: var(--color-bg-primary);
    position: sticky;
    top: 0;
    z-index: 50;
}

.chat-header-left {
    display: flex;
    align-items: center;
    gap: var(--space-3);
}

.chat-title {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--color-text-primary);
}

.chat-status {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--text-xs);
    color: var(--color-text-muted);
}

.status-indicator {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-accent);
}
.status-indicator.offline {
    background: var(--color-text-muted);
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-6);
    display: flex;
    flex-direction: column;
    gap: var(--space-5);
    max-width: var(--max-chat-width);
    margin: 0 auto;
    width: 100%;
}

/* Messages */
.message {
    display: flex;
    gap: var(--space-3);
    max-width: 85%;
    animation: fadeInUp var(--transition-base);
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.message.user {
    flex-direction: row-reverse;
    margin-left: auto;
}

.message-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    flex-shrink: 0;
    margin-top: 2px;
}
.message.user .message-avatar {
    background: var(--color-accent);
    color: white;
}
.message.assistant .message-avatar {
    background: var(--color-text-primary);
    color: white;
}

.message-bubble {
    max-width: 100%;
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-lg);
    line-height: 1.6;
    font-size: var(--text-base);
    position: relative;
}

.message.user .message-bubble {
    background: var(--color-user-msg);
    border-bottom-right-radius: var(--radius-sm);
}

.message.assistant .message-bubble {
    background: var(--color-assistant-msg);
    border: 1px solid var(--color-border);
    border-bottom-left-radius: var(--radius-sm);
}

.message-content {
    white-space: pre-wrap;
    word-wrap: break-word;
    line-height: 1.7;
}

/* Markdown styling inside messages */
.message-content h1, .message-content h2, .message-content h3 {
    margin: var(--space-4) 0 var(--space-2);
    font-weight: 600;
    color: var(--color-text-primary);
    line-height: 1.3;
}
.message-content h1 { font-size: var(--text-2xl); }
.message-content h2 { font-size: var(--text-xl); }
.message-content h3 { font-size: var(--text-lg); }
.message-content p { margin: var(--space-2) 0; }
.message-content ul, .message-content ol { margin: var(--space-2) 0; padding-left: var(--space-6); }
.message-content li { margin: var(--space-1) 0; }
.message-content code {
    background: var(--color-bg-tertiary);
    padding: 2px 6px;
    border-radius: var(--radius-xs);
    font-size: 0.9em;
    font-family: var(--font-mono);
}
.message-content pre {
    background: var(--color-bg-tertiary);
    padding: var(--space-3);
    border-radius: var(--radius-sm);
    overflow-x: auto;
    margin: var(--space-3) 0;
}
.message-content pre code { background: none; padding: 0; }
.message-content blockquote {
    border-left: 3px solid var(--color-accent);
    padding-left: var(--space-3);
    margin: var(--space-3) 0;
    color: var(--color-text-secondary);
    font-style: italic;
}
.message-content a { color: var(--color-accent); text-decoration: none; }
.message-content a:hover { text-decoration: underline; }
.message-content strong { font-weight: 600; }
.message-content table { width: 100%; border-collapse: collapse; margin: var(--space-3) 0; font-size: var(--text-sm); }
.message-content th, .message-content td { 
    border: 1px solid var(--color-border); 
    padding: var(--space-2) var(--space-3); 
    text-align: left;
}
.message-content th { background: var(--color-bg-tertiary); font-weight: 600; }

/* Citations */
.citations-container {
    margin-top: var(--space-4);
    padding-top: var(--space-3);
    border-top: 1px solid var(--color-border);
}

.citations-header {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: var(--space-2);
    cursor: pointer;
    padding: var(--space-1) 0;
    user-select: none;
}

.citation-card {
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: var(--space-3);
    margin-bottom: var(--space-2);
    transition: all var(--transition-fast);
}
.citation-card:hover {
    border-color: var(--color-accent);
    box-shadow: var(--shadow-sm);
}

.citation-title {
    font-weight: 500;
    color: var(--color-text-primary);
    margin-bottom: var(--space-2);
    font-size: var(--text-sm);
}

.citation-meta {
    font-size: var(--text-xs);
    color: var(--color-text-secondary);
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
    margin-bottom: var(--space-2);
}

.citation-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: var(--radius-full);
    font-size: var(--text-xs);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.badge-supported { background: var(--color-accent-light); color: #065f46; }
.badge-partially { background: #fef3c7; color: #92400e; }
.badge-not-supported { background: #fee2e2; color: #991b1b; }
.badge-insufficient { background: var(--color-bg-tertiary); color: var(--color-text-secondary); }
.badge-conflicting { background: #ffedd5; color: #9a3412; }

.citation-links {
    display: flex;
    gap: var(--space-2);
}
.citation-link {
    color: var(--color-accent);
    font-size: var(--text-xs);
    text-decoration: none;
    font-weight: 500;
}
.citation-link:hover { text-decoration: underline; }

/* Progress Indicator */
.progress-container {
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    margin: var(--space-4) 0;
}

.progress-header {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: var(--space-3);
}

.progress-step {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-2) 0;
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
    transition: all var(--transition-base);
}
.progress-step.active { color: var(--color-accent); font-weight: 500; }
.progress-step.completed { color: var(--color-text-muted); }

.progress-icon {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    flex-shrink: 0;
    transition: all var(--transition-base);
}
.progress-step.active .progress-icon { background: var(--color-accent); color: white; }
.progress-step.completed .progress-icon { background: var(--color-accent); color: white; }
.progress-step.pending .progress-icon { background: var(--color-bg-tertiary); color: var(--color-text-muted); }

/* Typing Indicator */
.typing-indicator {
    display: flex;
    gap: 4px;
    padding: var(--space-2) var(--space-3);
}
.typing-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-accent);
    animation: typing 1.4s infinite ease-in-out;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }

/* Welcome Screen */
.welcome-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    text-align: center;
    padding: var(--space-12) var(--space-6);
}

.welcome-icon {
    width: 72px;
    height: 72px;
    border-radius: var(--radius-xl);
    background: linear-gradient(135deg, var(--color-accent), #0d8f6f);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
    margin-bottom: var(--space-6);
    box-shadow: var(--shadow-lg);
}

.welcome-title {
    font-size: var(--text-4xl);
    font-weight: 700;
    color: var(--color-text-primary);
    margin-bottom: var(--space-3);
    letter-spacing: -0.02em;
    max-width: 600px;
}

.welcome-subtitle {
    font-size: var(--text-xl);
    color: var(--color-text-secondary);
    max-width: 560px;
    line-height: 1.6;
    margin-bottom: var(--space-10);
}

.suggestion-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: var(--space-4);
    width: 100%;
    max-width: 720px;
}

.suggestion-card {
    background: var(--color-bg-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--space-5);
    cursor: pointer;
    transition: all var(--transition-base);
    text-align: left;
}
.suggestion-card:hover {
    border-color: var(--color-accent);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

.suggestion-icon {
    width: 44px;
    height: 44px;
    border-radius: var(--radius-md);
    background: var(--color-accent-light);
    color: var(--color-accent);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    margin-bottom: var(--space-3);
}

.suggestion-title {
    font-weight: 600;
    font-size: var(--text-base);
    color: var(--color-text-primary);
    margin-bottom: var(--space-2);
}

.suggestion-prompt {
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
    font-family: var(--font-mono);
    background: var(--color-bg-secondary);
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-sm);
    line-height: 1.5;
}

/* Suggestion Chips (for composer) */
.suggestion-chips {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
    margin-top: var(--space-3);
    padding: 0 var(--space-1);
}
.suggestion-chip {
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-full);
    padding: var(--space-1) var(--space-3);
    font-size: var(--text-xs);
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
}
.suggestion-chip:hover {
    border-color: var(--color-accent);
    color: var(--color-accent);
    background: var(--color-accent-muted);
}

/* Composer */
.composer-area {
    grid-area: composer;
    background: var(--color-bg-primary);
    border-top: 1px solid var(--color-border);
    padding: var(--space-3) var(--space-6);
    position: sticky;
    bottom: 0;
    z-index: 100;
}

.composer-inner {
    max-width: var(--max-chat-width);
    margin: 0 auto;
    width: 100%;
}

.composer-settings {
    margin-bottom: var(--space-3);
}

.composer-input-wrapper {
    position: relative;
    display: flex;
    gap: var(--space-3);
    align-items: flex-end;
}

.composer-textarea-wrapper {
    flex: 1;
    position: relative;
}

.composer-textarea {
    width: 100%;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--space-3) var(--space-4);
    font-family: var(--font-sans);
    font-size: var(--text-base);
    line-height: 1.5;
    resize: none;
    min-height: var(--composer-height);
    max-height: 200px;
    background: var(--color-bg-input);
    color: var(--color-text-primary);
    box-shadow: var(--shadow-sm);
    transition: all var(--transition-fast);
}
.composer-textarea:focus {
    outline: none;
    border-color: var(--color-border-focus);
    box-shadow: 0 0 0 3px var(--color-accent-muted);
}
.composer-textarea::placeholder {
    color: var(--color-text-muted);
}

.composer-actions {
    display: flex;
    gap: var(--space-2);
    align-items: flex-end;
    padding-bottom: var(--space-1);
}

.composer-btn {
    width: 44px;
    height: 44px;
    border-radius: var(--radius-full);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all var(--transition-fast);
    flex-shrink: 0;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
}
.composer-btn.primary {
    background: var(--color-accent);
    color: white;
}
.composer-btn.primary:hover:not(:disabled) {
    background: var(--color-accent-hover);
    transform: scale(1.05);
}
.composer-btn.primary:disabled {
    background: var(--color-bg-tertiary);
    color: var(--color-text-muted);
    cursor: not-allowed;
}
.composer-btn.secondary {
    background: var(--color-bg-secondary);
    color: var(--color-text-secondary);
    border: 1px solid var(--color-border);
}
.composer-btn.secondary:hover:not(:disabled) {
    background: var(--color-bg-hover);
    border-color: var(--color-border-hover);
    color: var(--color-text-primary);
}
.composer-btn.secondary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.composer-hint {
    font-size: var(--text-xs);
    color: var(--color-text-muted);
    margin-top: var(--space-2);
    text-align: center;
}

/* Paper Explorer Panel */
.paper-explorer-panel {
    position: fixed;
    right: 0;
    top: var(--header-height);
    bottom: var(--composer-height);
    width: 380px;
    background: var(--color-bg-primary);
    border-left: 1px solid var(--color-border);
    z-index: 200;
    display: flex;
    flex-direction: column;
    animation: slideIn var(--transition-base);
    box-shadow: var(--shadow-xl);
}
@keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

.paper-explorer-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--space-4);
    border-bottom: 1px solid var(--color-border);
    background: var(--color-bg-primary);
}

.paper-explorer-title {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--color-text-primary);
}

.paper-explorer-close {
    background: transparent;
    border: none;
    color: var(--color-text-muted);
    font-size: 1.25rem;
    cursor: pointer;
    padding: var(--space-1);
    border-radius: var(--radius-sm);
    transition: all var(--transition-fast);
}
.paper-explorer-close:hover {
    color: var(--color-text-primary);
    background: var(--color-bg-hover);
}

.paper-explorer-tabs {
    display: flex;
    border-bottom: 1px solid var(--color-border);
    background: var(--color-bg-secondary);
    padding: 0 var(--space-2);
}
.explorer-tab {
    padding: var(--space-2) var(--space-4);
    background: transparent;
    border: none;
    color: var(--color-text-secondary);
    font-size: var(--text-sm);
    font-weight: 500;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all var(--transition-fast);
}
.explorer-tab:hover { color: var(--color-text-primary); }
.explorer-tab.active {
    color: var(--color-accent);
    border-bottom-color: var(--color-accent);
}

.paper-explorer-content {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-3);
}

.paper-card {
    background: var(--color-bg-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    margin-bottom: var(--space-3);
    transition: all var(--transition-fast);
}
.paper-card:hover {
    border-color: var(--color-accent);
    box-shadow: var(--shadow-sm);
}

.paper-card-title {
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: var(--space-2);
    font-size: var(--text-sm);
    line-height: 1.4;
}

.paper-card-meta {
    font-size: var(--text-xs);
    color: var(--color-text-secondary);
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
    margin-bottom: var(--space-3);
}

.paper-card-abstract {
    font-size: var(--text-xs);
    color: var(--color-text-secondary);
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    margin-bottom: var(--space-3);
}

.paper-card-actions {
    display: flex;
    gap: var(--space-2);
}
.paper-card-btn {
    flex: 1;
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: 500;
    border: 1px solid var(--color-border);
    background: var(--color-bg-primary);
    color: var(--color-text-primary);
    cursor: pointer;
    transition: all var(--transition-fast);
    text-align: center;
    text-decoration: none;
}
.paper-card-btn:hover {
    border-color: var(--color-accent);
    color: var(--color-accent);
}
.paper-card-btn.primary {
    background: var(--color-accent);
    border-color: var(--color-accent);
    color: white;
}
.paper-card-btn.primary:hover {
    background: var(--color-accent-hover);
    border-color: var(--color-accent-hover);
}

/* Evidence Panel */
.evidence-card {
    background: var(--color-bg-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    margin-bottom: var(--space-3);
}

.evidence-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: var(--space-3);
    padding-bottom: var(--space-2);
    border-bottom: 1px solid var(--color-border);
}

.evidence-status {
    display: inline-flex;
    align-items: center;
    gap: var(--space-1);
    padding: 2px 8px;
    border-radius: var(--radius-full);
    font-size: var(--text-xs);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.evidence-paper {
    font-size: var(--text-xs);
    color: var(--color-text-secondary);
}

.evidence-text {
    font-size: var(--text-sm);
    color: var(--color-text-primary);
    line-height: 1.6;
    background: var(--color-bg-secondary);
    padding: var(--space-3);
    border-radius: var(--radius-sm);
    margin-bottom: var(--space-3);
}

.evidence-meta {
    font-size: var(--text-xs);
    color: var(--color-text-secondary);
    display: flex;
    gap: var(--space-3);
    flex-wrap: wrap;
}

/* Gap Card */
.gap-card {
    background: var(--color-bg-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    margin-bottom: var(--space-3);
}

.gap-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--space-3);
    margin-bottom: var(--space-3);
}

.gap-title {
    font-weight: 600;
    color: var(--color-text-primary);
    font-size: var(--text-sm);
    line-height: 1.4;
    flex: 1;
}

.gap-evidence-strength {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--color-accent);
    background: var(--color-accent-light);
    padding: 2px 8px;
    border-radius: var(--radius-full);
    flex-shrink: 0;
}

.gap-detail {
    font-size: var(--text-xs);
    color: var(--color-text-secondary);
    line-height: 1.6;
    margin-bottom: var(--space-2);
}

.gap-actions {
    display: flex;
    gap: var(--space-2);
}
.gap-btn {
    flex: 1;
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: 500;
    border: 1px solid var(--color-border);
    background: var(--color-bg-primary);
    color: var(--color-text-primary);
    cursor: pointer;
    transition: all var(--transition-fast);
}
.gap-btn:hover { border-color: var(--color-accent); color: var(--color-accent); }
.gap-btn.primary { background: var(--color-accent); border-color: var(--color-accent); color: white; }
.gap-btn.primary:hover { background: var(--color-accent-hover); border-color: var(--color-accent-hover); }

/* Settings Panel */
.settings-panel {
    position: fixed;
    right: 0;
    top: 0;
    bottom: 0;
    width: 380px;
    background: var(--color-bg-primary);
    border-left: 1px solid var(--color-border);
    z-index: 300;
    display: flex;
    flex-direction: column;
    animation: slideIn var(--transition-base);
    box-shadow: var(--shadow-xl);
}

.settings-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--space-4);
    border-bottom: 1px solid var(--color-border);
}

.settings-content {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-4);
}

.setting-group {
    margin-bottom: var(--space-6);
}
.setting-label {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: var(--space-2);
}

/* Mobile Overlay */
.mobile-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99;
}
@media (max-width: 768px) {
    .mobile-overlay.active { display: block; }
}

/* Responsive */
@media (max-width: 768px) {
    :root {
        --sidebar-width: 100vw;
        --sidebar-collapsed-width: 0;
        --max-chat-width: 100%;
        --header-height: 52px;
        --composer-height: 52px;
    }
    
    .app-layout { grid-template-columns: 1fr; grid-template-areas: "chat" "composer"; }
    .sidebar { position: fixed; left: 0; top: 0; bottom: 0; z-index: 200; transform: translateX(-100%); }
    .sidebar.open { transform: translateX(0); }
    .sidebar.collapsed { width: 100vw; }
    
    .chat-header { padding: 0 var(--space-3); }
    .chat-messages { padding: var(--space-4); }
    .composer-area { padding: var(--space-3) var(--space-4); }
    .message { max-width: 90%; }
    .composer-settings { display: none; }
    
    .paper-explorer-panel { width: 100vw; right: -100vw; }
    .paper-explorer-panel.open { right: 0; }
    
    .settings-panel { width: 100vw; right: -100vw; }
    .settings-panel.open { right: 0; }
}

/* Utility */
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }

/* Print */
@media print {
    .sidebar, .composer-area, .paper-explorer-panel, .settings-panel, .mobile-overlay { display: none !important; }
    .app-layout { display: block; }
    .chat-area { height: auto; }
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# INITIALIZATION
# ══════════════════════════════════════════════════════════════════
setup_logging()
init_db()

# ══════════════════════════════════════════════════════════════════
# DATA CLASSES & ENUMS
# ══════════════════════════════════════════════════════════════════
class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"

class ResearchStage(Enum):
    PLANNING = ("Planning research strategy", "🎯")
    SEARCHING = ("Searching academic sources", "🔍")
    FILTERING = ("Filtering relevant papers", "📋")
    RETRIEVING = ("Retrieving open-access documents", "📥")
    PROCESSING = ("Processing paper content", "⚙️")
    ANALYZING = ("Analyzing papers", "🔬")
    COMPARING = ("Comparing findings", "⚖️")
    VERIFYING = ("Verifying evidence", "✅")
    GAP_DISCOVERY = ("Identifying candidate research gaps", "💡")
    REPORT_GENERATION = ("Generating final report", "📄")
    COMPLETED = ("Research complete", "✨")
    
    def __init__(self, label: str, icon: str):
        self.label = label
        self.icon = icon

@dataclass
class ChatMessage:
    role: MessageRole
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    research_stages: List[ResearchStage] = field(default_factory=list)
    current_stage: Optional[ResearchStage] = None
    citations: List[Dict] = field(default_factory=list)
    papers: List[Paper] = field(default_factory=list)
    report: Optional[str] = None
    is_typing: bool = False
    error: Optional[str] = None

@dataclass
class Conversation:
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessage] = field(default_factory=list)
    session_id: Optional[int] = None

# ══════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ══════════════════════════════════════════════════════════════════
def init_chat_state():
    defaults = {
        "conversations": {},
        "current_conversation_id": None,
        "sidebar_collapsed": False,
        "sidebar_open": False,
        "show_paper_explorer": False,
        "show_settings": False,
        "show_mobile_sidebar": False,
        "composer_value": "",
        "is_generating": False,
        "search_settings": {
            "sources": ["OpenAlex", "Crossref", "arXiv"],
            "max_papers": 20,
            "open_access_only": True,
            "min_year": 2015,
        },
        "current_research_stage": None,
        "paper_explorer_tab": "papers",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_chat_state()

# ══════════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ══════════════════════════════════════════════════════════════════
def save_conversation_to_db(conversation: Conversation) -> int:
    with get_session() as session:
        if conversation.session_id:
            rs = session.get(ResearchSession, conversation.session_id)
            if rs:
                rs.research_question = conversation.title
                rs.updated_at = datetime.utcnow()
                session.commit()
                return rs.id
        
        rs = ResearchSession(
            research_question=conversation.title,
            status=ResearchSessionStatus.IN_PROGRESS,
        )
        session.add(rs)
        session.commit()
        session.refresh(rs)
        return rs.id

def load_conversations_from_db() -> Dict[int, Conversation]:
    conversations = {}
    with get_session() as session:
        research_sessions = session.query(ResearchSession).order_by(ResearchSession.updated_at.desc()).all()
        for rs in research_sessions:
            conv = Conversation(
                id=rs.id,
                title=rs.research_question or f"Session {rs.id}",
                created_at=rs.created_at,
                updated_at=rs.updated_at,
                session_id=rs.id,
            )
            conversations[rs.id] = conv
    return conversations

def delete_conversation(conv_id: int):
    with get_session() as session:
        rs = session.get(ResearchSession, conv_id)
        if rs:
            session.delete(rs)
            session.commit()

def rename_conversation(conv_id: int, new_title: str):
    with get_session() as session:
        rs = session.get(ResearchSession, conv_id)
        if rs:
            rs.research_question = new_title
            rs.updated_at = datetime.utcnow()
            session.commit()

# ═══════════════════════════════════════════════════════════════════
# RESEARCH WORKFLOW
# ══════════════════════════════════════════════════════════════════
async def run_research_workflow(query: str, conversation: Conversation, search_settings: Dict) -> ChatMessage:
    stages = list(ResearchStage)
    all_papers = []
    analysis_results = {}
    comparison_results = None
    discovered_gaps = []
    generated_report = None
    citations = []

    try:
        # Stage 1: Planning
        st.session_state.current_research_stage = ResearchStage.PLANNING
        await asyncio.sleep(0.1)
        
        # Stage 2: Searching
        st.session_state.current_research_stage = ResearchStage.SEARCHING
        agent = PaperSearchAgent()
        source_enums = [PaperSource[s.upper().replace(" ", "_")] for s in search_settings["sources"]]
        
        papers_result = await agent.search(
            query=query,
            limit=search_settings["max_papers"],
            sources=source_enums,
            open_access_only=search_settings["open_access_only"]
        )
        all_papers = papers_result.papers
        await agent.close()
        
        if not all_papers:
            return ChatMessage(
                role=MessageRole.ASSISTANT,
                content="I couldn't find any relevant papers for your query. Try broadening your search terms or removing the open-access filter.",
                research_stages=stages,
                current_stage=ResearchStage.COMPLETED,
            )
        
        # Filter by year
        if search_settings.get("min_year"):
            all_papers = [p for p in all_papers if p.year and p.year >= search_settings["min_year"]]
        
        if not all_papers:
            return ChatMessage(
                role=MessageRole.ASSISTANT,
                content=f"No papers found from {search_settings['min_year']} onwards. Try adjusting the year filter.",
                research_stages=stages,
                current_stage=ResearchStage.COMPLETED,
            )

        # Save papers
        if conversation.session_id:
            saved_paper_models, paper_id_map = save_papers_to_session(all_papers, conversation.session_id)
        else:
            saved_paper_models = []
            paper_id_map = {}

        # Stage 3: Processing
        st.session_state.current_research_stage = ResearchStage.PROCESSING
        papers_to_analyze = all_papers[:5]
        
        for paper in papers_to_analyze:
            db_pid = paper_id_map.get(paper.source_specific_id, paper.paper_id)
            
            if paper.pdf_url:
                try:
                    downloader = PDFDownloader()
                    path = await downloader.download(str(paper.pdf_url), str(paper.paper_id))
                    await downloader.close()
                    
                    processor = PDFProcessor()
                    pdf_doc = processor.extract_text(str(path))
                    
                    if pdf_doc.extraction_success:
                        chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
                        chunks = chunker.chunk_document(pdf_doc, db_pid)
                        save_chunks_to_paper(db_pid, conversation.session_id, chunks)
                except Exception:
                    pass
            else:
                try:
                    if paper.abstract:
                        chunk = TextChunk(
                            chunk_id=f"{db_pid}_abstract",
                            page_number=1,
                            text=paper.abstract,
                            char_start=0,
                            char_end=len(paper.abstract),
                            word_count=len(paper.abstract.split()),
                            char_count=len(paper.abstract),
                        )
                        save_chunks_to_paper(db_pid, conversation.session_id, [chunk])
                except Exception:
                    pass

        # Stage 4: Analyzing
        st.session_state.current_research_stage = ResearchStage.ANALYZING
        analysis_agent = PaperAnalysisAgent()
        db_paper_ids = [paper_id_map.get(p.source_specific_id, p.paper_id) for p in papers_to_analyze[:3]]
        
        for db_pid in db_paper_ids:
            try:
                result = analysis_agent.analyze_paper(
                    paper_id=db_pid,
                    session_id=conversation.session_id,
                    query="Extract research objective, methodology, datasets, results, and limitations"
                )
                analysis_results[db_pid] = result
            except Exception:
                pass

        # Stage 5: Comparing
        st.session_state.current_research_stage = ResearchStage.COMPARING
        if len(db_paper_ids) >= 2:
            try:
                cross_agent = CrossPaperAgent()
                comparison_results = cross_agent.compare_papers(
                    session_id=conversation.session_id,
                    paper_ids=db_paper_ids
                )
            except Exception:
                pass

        # Stage 6: Verifying
        st.session_state.current_research_stage = ResearchStage.VERIFYING
        await asyncio.sleep(0.1)

        # Stage 7: Gap Discovery
        st.session_state.current_research_stage = ResearchStage.GAP_DISCOVERY
        try:
            gap_agent = ResearchGapAgent()
            discovered_gaps = gap_agent.discover_gaps(
                session_id=conversation.session_id,
                min_evidence_strength=50,
                max_gaps=5
            )
        except Exception:
            pass

        # Stage 8: Report Generation
        st.session_state.current_research_stage = ResearchStage.REPORT_GENERATION
        try:
            generator = ReportGenerator()
            generated_report = generator.generate_full_report(
                session_id=conversation.session_id,
                include_gaps=True,
                min_gap_evidence=50,
                max_gaps=5
            )
        except Exception:
            pass

        # Build response
        response_parts = [
            f"## Research Summary\n",
            f"I found **{len(all_papers)} papers** related to your query. "
            f"Analyzed **{len(analysis_results)} papers** in detail.\n"
        ]
        
        if all_papers:
            response_parts.append("### 📚 Relevant Papers\n")
            for i, paper in enumerate(all_papers[:5], 1):
                authors = ", ".join(a.name for a in paper.authors[:3])
                if len(paper.authors) > 3:
                    authors += " et al."
                response_parts.append(
                    f"{i}. **{paper.title}** ({paper.year or 'N/A'})  \n"
                    f"   *{authors}* • {paper.citation_count} citations • {paper.source.value}\n"
                )
                if paper.doi:
                    response_parts.append(f"   DOI: {paper.doi}\n")
                response_parts.append("\n")
        
        if analysis_results:
            response_parts.append("### 🔬 Key Findings\n")
            for db_pid, analysis in list(analysis_results.items())[:3]:
                paper = next((p for p in all_papers if paper_id_map.get(p.source_specific_id) == db_pid), None)
                if paper:
                    response_parts.append(f"**{paper.title[:60]}...**\n")
                    for field, label in [
                        ("research_objective", "Objective"),
                        ("methodology", "Methodology"),
                        ("datasets", "Datasets"),
                        ("results", "Results"),
                        ("limitations", "Limitations"),
                    ]:
                        if field in analysis and analysis[field].get("claim"):
                            claim = analysis[field]["claim"]
                            if claim != "NOT MENTIONED IN PROVIDED TEXT":
                                response_parts.append(f"- **{label}:** {claim[:200]}...\n")
                    response_parts.append("\n")
        
        if comparison_results and comparison_results.conflicts:
            response_parts.append("### ⚠️ Conflicts Detected\n")
            for conflict in comparison_results.conflicts[:3]:
                response_parts.append(
                    f"- **{conflict.field}:** {conflict.paper1_title[:40]}... vs "
                    f"{conflict.paper2_title[:40]}... ({conflict.conflict_type}, {conflict.severity})\n"
                )
            response_parts.append("\n")
        
        if discovered_gaps:
            response_parts.append("### 💡 Candidate Research Gaps\n")
            for i, gap in enumerate(discovered_gaps[:3], 1):
                response_parts.append(
                    f"{i}. **{gap.gap_statement}** (Evidence: {gap.evidence_strength}/100)\n"
                    f"   *Direction:* {gap.potential_research_direction[:150]}...\n\n"
                )
        
        if generated_report:
            response_parts.append("### 📄 Full Report\n")
            response_parts.append("A comprehensive research report has been generated with full evidence traceability. ")
            response_parts.append("Use the actions below to view or download it.\n")
        
        # Build citations
        for paper in all_papers[:10]:
            citations.append({
                "title": paper.title,
                "authors": [a.name for a in paper.authors],
                "year": paper.year,
                "doi": paper.doi,
                "url": str(paper.url) if paper.url else None,
                "source": paper.source.value,
                "citations": paper.citation_count,
            })
        
        return ChatMessage(
            role=MessageRole.ASSISTANT,
            content="".join(response_parts),
            research_stages=list(ResearchStage),
            current_stage=ResearchStage.COMPLETED,
            citations=citations,
            papers=all_papers,
            report=generated_report,
            metadata={
                "papers_found": len(all_papers),
                "papers_analyzed": len(analysis_results),
                "gaps_found": len(discovered_gaps),
                "has_report": generated_report is not None,
            }
        )
        
    except Exception as e:
        return ChatMessage(
            role=MessageRole.ASSISTANT,
            content=f"Research encountered an error: {str(e)}",
            research_stages=list(ResearchStage),
            current_stage=ResearchStage.COMPLETED,
            error=str(e),
        )

# ═══════════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ═══════════════════════════════════════════════════════════════════
def save_conversation_to_db(conversation: Conversation) -> int:
    with get_session() as session:
        if conversation.session_id:
            rs = session.get(ResearchSession, conversation.session_id)
            if rs:
                rs.research_question = conversation.title
                rs.updated_at = datetime.utcnow()
                session.commit()
                return rs.id
        
        rs = ResearchSession(
            research_question=conversation.title,
            status=ResearchSessionStatus.IN_PROGRESS,
        )
        session.add(rs)
        session.commit()
        session.refresh(rs)
        return rs.id

def load_conversations_from_db() -> Dict[int, Conversation]:
    conversations = {}
    with get_session() as session:
        research_sessions = session.query(ResearchSession).order_by(ResearchSession.updated_at.desc()).all()
        for rs in research_sessions:
            conv = Conversation(
                id=rs.id,
                title=rs.research_question or f"Session {rs.id}",
                created_at=rs.created_at,
                updated_at=rs.updated_at,
                session_id=rs.id,
            )
            conversations[rs.id] = conv
    return conversations

def delete_conversation(conv_id: int):
    with get_session() as session:
        rs = session.get(ResearchSession, conv_id)
        if rs:
            session.delete(rs)
            session.commit()

def rename_conversation(conv_id: int, new_title: str):
    with get_session() as session:
        rs = session.get(ResearchSession, conv_id)
        if rs:
            rs.research_question = new_title
            rs.updated_at = datetime.utcnow()
            session.commit()

# ═══════════════════════════════════════════════════════════════════
# CONVERSATION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════
def start_new_conversation():
    with get_session() as session:
        rs = ResearchSession(
            research_question="New Research Session",
            status=ResearchSessionStatus.CREATED,
        )
        session.add(rs)
        session.commit()
        session.refresh(rs)
        new_session_id = rs.id
    
    new_conv = Conversation(
        id=new_session_id,
        title="New Research Session",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        session_id=new_session_id,
    )
    
    st.session_state.current_conversation_id = new_session_id
    st.session_state.conversations[new_session_id] = new_conv
    st.session_state.db_conversations = load_conversations_from_db()
    st.session_state.show_paper_explorer = False
    st.session_state.show_settings = False

def load_conversation_messages(conv: Conversation):
    st.session_state.conversations[conv.id] = conv
    if conv.messages:
        st.session_state.messages = conv.messages

# ═══════════════════════════════════════════════════════════════════
# UI RENDERING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def render_welcome_screen():
    """Render the elegant welcome screen with 4 prompt suggestions."""
    st.markdown("""
    <div class="welcome-screen">
        <div class="welcome-icon">🔬</div>
        <h1 class="welcome-title">Your research starts here.</h1>
        <p class="welcome-subtitle">
            Explore scientific literature. Compare evidence. Discover research gaps.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    suggestions = [
        {"icon": "📚", "title": "Literature Review", "prompt": "Analyze existing research on AI-based network intrusion detection systems."},
        {"icon": "⚖️", "title": "Paper Comparison", "prompt": "Compare the methodologies, datasets, and results of selected research papers."},
        {"icon": "🔍", "title": "Evidence Investigation", "prompt": "Find research evidence supporting or contradicting a scientific claim."},
        {"icon": "💡", "title": "Gap Discovery", "prompt": "Identify recurring limitations and potential research directions across multiple papers."},
    ]
    
    st.markdown('<div class="suggestion-cards">', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(
                f"{suggestion['icon']}  {suggestion['title']}\n\n{suggestion['prompt']}",
                key=f"suggestion_{i}",
                use_container_width=True,
            ):
                start_new_conversation()
                st.session_state.composer_value = suggestion['prompt']
                handle_user_message(suggestion['prompt'], st.session_state.search_settings)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def render_sidebar():
    """Render the compact, collapsible sidebar with conversation history."""
    with st.sidebar:
        # Sidebar Header
        st.markdown(f"""
        <div class="sidebar-header">
            <div class="sidebar-logo">🔬</div>
            <div class="sidebar-title">Research Assistant</div>
        </div>
        """, unsafe_allow_html=True)
        
        # New Research button
        if st.button("➕  New Research", use_container_width=True, type="primary", key="new_research_btn"):
            start_new_conversation()
            st.rerun()
        
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        # Conversation History
        if "db_conversations" not in st.session_state:
            st.session_state.db_conversations = load_conversations_from_db()
        
        conversations = st.session_state.db_conversations
        
        if conversations:
            today = datetime.now().date()
            week_ago = today.replace(day=today.day - 7) if today.day > 7 else today
            
            today_convs = []
            week_convs = []
            older_convs = []
            
            for conv in conversations.values():
                conv_date = conv.updated_at.date() if hasattr(conv.updated_at, 'date') else conv.updated_at
                if conv_date == today:
                    today_convs.append(conv)
                elif conv_date >= week_ago:
                    week_convs.append(conv)
                else:
                    older_convs.append(conv)
            
            def render_conv_section(title, convs):
                if convs:
                    st.markdown(f'<div class="sidebar-section-title">{title}</div>', unsafe_allow_html=True)
                    for conv in convs:
                        render_conversation_item(conv)
            
            render_conv_section("Today", today_convs)
            render_conv_section("Previous 7 Days", week_convs)
            render_conv_section("Older", older_convs[:10])
        else:
            st.markdown('<div style="padding: var(--space-4); color: var(--color-text-muted); font-size: var(--text-sm); text-align: center;">No conversations yet<br>Start a new research session!</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        # Settings Section
        with st.expander("⚙️ Settings", expanded=st.session_state.show_settings):
            st.session_state.show_settings = True
            
            st.markdown("**Model Configuration**")
            col1, col2 = st.columns(2)
            with col1:
                st.caption("Provider")
                st.write(settings.llm_provider.title())
            with col2:
                st.caption("Model")
                if settings.llm_provider == "nvidia":
                    st.write(settings.nvidia_model)
                else:
                    st.write(settings.ollama_model)
            
            st.markdown("**Academic APIs**")
            col1, col2 = st.columns(2)
            with col1:
                st.caption("OpenAlex")
                st.write("✅ Connected" if settings.openalex_api_key else "❌ Not configured")
            with col2:
                st.caption("Semantic Scholar")
                st.write("✅ Connected" if settings.semantic_scholar_api_key else "❌ Not configured")
            
            st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
            
            if st.button("🗑️ Clear All Conversations", use_container_width=True):
                if st.session_state.get("confirm_clear_all"):
                    for conv_id in list(st.session_state.db_conversations.keys()):
                        delete_conversation(conv_id)
                    st.session_state.db_conversations = {}
                    st.session_state.conversations = {}
                    st.session_state.current_conversation_id = None
                    st.session_state.confirm_clear_all = False
                    st.success("All conversations cleared")
                    st.rerun()
                else:
                    st.session_state.confirm_clear_all = True
                    st.warning("Click again to confirm deletion of all conversations")

def render_conversation_item(conv: Conversation):
    """Render a conversation item with three-dot menu."""
    is_active = st.session_state.current_conversation_id == conv.id
    show_menu = st.session_state.get(f"show_menu_{conv.id}", False)
    
    with st.container():
        col1, col2 = st.columns([1, 0.08])
        with col1:
            btn_label = f"{'● ' if is_active else ''}{conv.title[:35]}{'…' if len(conv.title) > 35 else ''}"
            if st.button(btn_label, key=f"conv_{conv.id}", use_container_width=True):
                st.session_state.current_conversation_id = conv.id
                st.session_state[f"show_menu_{conv.id}"] = False
                st.rerun()
            
            date_str = conv.updated_at.strftime("%b %d, %H:%M") if hasattr(conv.updated_at, 'strftime') else str(conv.updated_at)
            st.caption(date_str)
        
        with col2:
            if st.button("⋯", key=f"menu_toggle_{conv.id}", help="More options"):
                st.session_state[f"show_menu_{conv.id}"] = not st.session_state.get(f"show_menu_{conv.id}", False)
                st.rerun()
    
    if show_menu:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ Rename", key=f"rename_{conv.id}", use_container_width=True):
                new_title = st.text_input("New title", value=conv.title, key=f"rename_input_{conv.id}", label_visibility="collapsed")
                if st.button("Save", key=f"save_rename_{conv.id}"):
                    rename_conversation(conv.id, new_title)
                    st.session_state.db_conversations = load_conversations_from_db()
                    st.session_state[f"show_menu_{conv.id}"] = False
                    st.rerun()
        with col2:
            if st.button("🗑️ Delete", key=f"delete_{conv.id}", use_container_width=True, type="secondary"):
                if st.session_state.get(f"confirm_delete_{conv.id}"):
                    delete_conversation(conv.id)
                    st.session_state.db_conversations = load_conversations_from_db()
                    if st.session_state.current_conversation_id == conv.id:
                        st.session_state.current_conversation_id = None
                    st.session_state[f"confirm_delete_{conv.id}"] = False
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_{conv.id}"] = True
                    st.warning("Click again to confirm")

def render_welcome_screen():
    """Render the elegant welcome screen with 4 prompt suggestions."""
    st.markdown("""
    <div class="welcome-screen">
        <div class="welcome-icon">🔬</div>
        <h1 class="welcome-title">Your research starts here.</h1>
        <p class="welcome-subtitle">
            Explore scientific literature. Compare evidence. Discover research gaps.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    suggestions = [
        {"icon": "📚", "title": "Literature Review", "prompt": "Analyze existing research on AI-based network intrusion detection systems."},
        {"icon": "⚖️", "title": "Paper Comparison", "prompt": "Compare the methodologies, datasets, and results of selected research papers."},
        {"icon": "🔍", "title": "Evidence Investigation", "prompt": "Find research evidence supporting or contradicting a scientific claim."},
        {"icon": "💡", "title": "Gap Discovery", "prompt": "Identify recurring limitations and potential research directions across multiple papers."},
    ]
    
    st.markdown('<div class="suggestion-cards">', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(
                f"{suggestion['icon']}  {suggestion['title']}\n\n{suggestion['prompt']}",
                key=f"suggestion_{i}",
                use_container_width=True,
            ):
                start_new_conversation()
                st.session_state.composer_value = suggestion['prompt']
                handle_user_message(suggestion['prompt'], st.session_state.search_settings)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def render_progress_indicator(current_stage: Optional[ResearchStage]):
    """Render the research progress indicator with actual stages."""
    stages = list(ResearchStage)
    if not current_stage or current_stage not in stages:
        return
    
    current_idx = stages.index(current_stage)
    
    st.markdown('<div class="progress-container">', unsafe_allow_html=True)
    st.markdown('<div class="progress-header">Research Progress</div>', unsafe_allow_html=True)
    
    for i, stage in enumerate(stages):
        if i == current_idx:
            status_class = "active"
            icon = stage.icon
        elif i < current_idx:
            status_class = "completed"
            icon = "✓"
        else:
            status_class = "pending"
            icon = str(i + 1)
        
        st.markdown(f"""
        <div class="progress-step {status_class}">
            <span class="progress-icon">{icon}</span>
            <span>{stage.label}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_typing_indicator():
    st.markdown("""
    <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    </div>
    """, unsafe_allow_html=True)

def render_citations(citations: List[Dict]):
    """Render citations in an expandable section."""
    if not citations:
        return
    
    with st.expander(f"📖 Citations ({len(citations)})", expanded=False):
        for cite in citations:
            st.markdown(f"""
            <div class="citation-card">
                <div class="citation-title">{cite['title'][:120]}</div>
                <div class="citation-meta">
                    <span>{', '.join(cite['authors'][:3])}{' et al.' if len(cite['authors']) > 3 else ''}</span>
                    <span>({cite['year'] or 'N/A'})</span>
                    <span>{cite['source']}</span>
                    <span>{cite['citations']} citations</span>
                    <span class="citation-badge badge-supported">Supported</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if cite.get('doi'):
                st.markdown(f"[DOI: {cite['doi']}](https://doi.org/{cite['doi']})")
            if cite.get('url'):
                st.markdown(f"[Source]({cite['url']})")

def render_citation_card(cite: Dict) -> str:
    """Render a single citation card as HTML string."""
    return f"""
    <div class="citation-card">
        <div class="citation-title">{cite['title'][:120]}</div>
        <div class="citation-meta">
            <span>{', '.join(cite['authors'][:3])}{' et al.' if len(cite['authors']) > 3 else ''}</span>
            <span>({cite['year'] or 'N/A'})</span>
            <span>{cite['source']}</span>
            <span>{cite['citations']} citations</span>
            <span class="citation-badge badge-supported">Supported</span>
        </div>
    </div>
    """

def render_chat_message(message: ChatMessage, index: int):
    """Render a chat message with proper styling."""
    is_user = message.role == MessageRole.USER
    
    row_class = "user" if is_user else ""
    avatar_class = "user-avatar" if is_user else "assistant-avatar"
    avatar_text = "You" if is_user else "🔬"
    bubble_class = "user-bubble" if is_user else "assistant-bubble"
    
    avatar_html = f'<div class="message-avatar {avatar_class}">{avatar_text}</div>'
    
    if is_user:
        content_html = f'<div class="message-content">{message.content}</div>'
    else:
        content_html = f'<div class="message-content">{message.content}</div>'
        
        # Progress indicator if still generating
        if message.current_stage and message.current_stage != ResearchStage.COMPLETED:
            render_progress_indicator(message.current_stage)
        
        # Citations
        if message.citations:
            content_html += '<div class="citations-container">'
            content_html += '<div class="citations-header">📖 Citations</div>'
            for cite in message.citations:
                content_html += render_citation_card(cite)
            content_html += '</div>'
        
        # Action buttons for completed research
        if message.current_stage == ResearchStage.COMPLETED and message.metadata.get("has_report"):
            content_html += '<div style="margin-top: 16px; display: flex; gap: 8px;">'
            content_html += f'<button class="paper-card-btn primary" onclick="window.parent.download_report_{index}()">📥 Download Report</button>'
            content_html += f'<button class="paper-card-btn" onclick="window.parent.view_papers_{index}()">📄 View Papers</button>'
            content_html += f'<button class="paper-card-btn" onclick="window.parent.view_gaps_{index}()">🔍 View Gaps</button>'
            content_html += '</div>'
    
    bubble_html = f'<div class="message-bubble {bubble_class}">{content_html}</div>'
    
    if is_user:
        st.markdown(f"""
        <div class="message-row user">
            {bubble_html}
            {avatar_html}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="message-row">
            {avatar_html}
            {bubble_html}
        </div>
        """, unsafe_allow_html=True)
    
    # Action buttons for assistant messages
    if not is_user and message.current_stage == ResearchStage.COMPLETED and message.metadata.get("has_report"):
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📥 Download Report", key=f"dl_report_{index}", use_container_width=True):
                if message.report:
                    st.download_button(
                        "Download Markdown", data=message.report,
                        file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown", key=f"dl_btn_{index}"
                    )
        with col2:
            if st.button("📄 View Papers", key=f"view_papers_{index}", use_container_width=True):
                st.session_state.show_paper_explorer = True
                st.rerun()
        with col3:
            if st.button("🔍 View Gaps", key=f"view_gaps_{index}", use_container_width=True):
                st.session_state.show_gaps = True
                st.rerun()

def render_typing_indicator():
    st.markdown("""
    <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    </div>
    """, unsafe_allow_html=True)

def render_paper_explorer_panel(papers: List[Paper]):
    """Render the paper explorer side panel."""
    if not papers:
        return
    
    st.markdown(f"""
    <div class="paper-explorer-panel">
        <div class="paper-explorer-header">
            <div class="paper-explorer-title">📄 Papers ({len(papers)})</div>
            <button class="paper-explorer-close" onclick="window.parent.close_paper_explorer()">✕</button>
        </div>
        <div class="paper-explorer-tabs">
            <button class="explorer-tab active" onclick="window.parent.switch_explorer_tab('papers')">Papers</button>
            <button class="explorer-tab" onclick="window.parent.switch_explorer_tab('evidence')">Evidence</button>
            <button class="explorer-tab" onclick="window.parent.switch_explorer_tab('gaps')">Gaps</button>
            <button class="explorer-tab" onclick="window.parent.switch_explorer_tab('report')">Report</button>
        </div>
        <div class="paper-explorer-content">
    """, unsafe_allow_html=True)
    
    for paper in papers[:15]:
        authors = ", ".join(a.name for a in paper.authors[:3])
        if len(paper.authors) > 3:
            authors += " et al."
        
        abstract_preview = paper.abstract[:200] + "..." if paper.abstract and len(paper.abstract) > 200 else (paper.abstract or "No abstract available")
        
        st.markdown(f"""
        <div class="paper-card">
            <div class="paper-card-title">{paper.title}</div>
            <div class="paper-card-meta">
                <span>{authors}</span>
                <span>({paper.year or 'N/A'})</span>
                <span>{paper.source.value}</span>
                <span>{paper.citation_count} citations</span>
            </div>
            <div class="paper-card-abstract">{abstract_preview}</div>
            <div class="paper-card-actions">
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if paper.doi:
                st.markdown(f"[DOI](https://doi.org/{paper.doi})")
            if paper.pdf_url:
                st.markdown(f"[PDF]({paper.pdf_url})")
        with col2:
            if paper.url:
                st.markdown(f"[Source]({paper.url})")
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

def render_settings_panel():
    st.markdown("""
    <div class="settings-panel">
        <div class="settings-header">
            <h3 style="margin: 0; font-size: var(--text-base); font-weight: 600;">Settings</h3>
            <button class="paper-explorer-close" onclick="window.parent.close_settings()">✕</button>
        </div>
        <div class="settings-content">
    """, unsafe_allow_html=True)
    
    st.markdown("**Model Configuration**")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Provider")
        st.write(settings.llm_provider.title())
    with col2:
        st.caption("Model")
        if settings.llm_provider == "nvidia":
            st.write(settings.nvidia_model)
        else:
            st.write(settings.ollama_model)
    
    st.markdown("**Academic APIs**")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("OpenAlex")
        st.write("✅ Connected" if settings.openalex_api_key else "❌ Not configured")
    with col2:
        st.caption("Semantic Scholar")
        st.write("✅ Connected" if settings.semantic_scholar_api_key else "❌ Not configured")
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    
    if st.button("🗑️ Clear All Conversations", use_container_width=True):
        if st.session_state.get("confirm_clear_all"):
            for conv_id in list(st.session_state.db_conversations.keys()):
                delete_conversation(conv_id)
            st.session_state.db_conversations = {}
            st.session_state.conversations = {}
            st.session_state.current_conversation_id = None
            st.session_state.confirm_clear_all = False
            st.success("All conversations cleared")
            st.rerun()
        else:
            st.session_state.confirm_clear_all = True
            st.warning("Click again to confirm deletion of all conversations")
    
    st.markdown("</div></div>", unsafe_allow_html=True)

def render_message_composer():
    """Render the enhanced message composer with research settings."""
    st.markdown('<div class="composer-area">', unsafe_allow_html=True)
    st.markdown('<div class="composer-inner">', unsafe_allow_html=True)
    
    # Research settings (collapsible)
    with st.expander("⚙️ Research Settings", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            sources = st.multiselect(
                "Sources",
                ["OpenAlex", "Semantic Scholar", "Crossref", "arXiv"],
                default=st.session_state.search_settings["sources"],
                key="composer_sources"
            )
            max_papers = st.slider("Max Papers", 5, 50, st.session_state.search_settings["max_papers"])
        with col2:
            open_access_only = st.checkbox("Open Access Only", value=st.session_state.search_settings["open_access_only"])
            min_year = st.number_input("Min Year", 1990, 2025, st.session_state.search_settings["min_year"])
        
        # Update settings
        st.session_state.search_settings = {
            "sources": sources,
            "max_papers": max_papers,
            "open_access_only": open_access_only,
            "min_year": min_year,
        }
    
    # Composer input
    col1, col2 = st.columns([20, 1])
    with col1:
        user_input = st.text_area(
            "Research question",
            value=st.session_state.composer_value,
            placeholder="Ask a research question... (Shift+Enter for new line, Enter to send)",
            key="composer_input",
            height=56,
            label_visibility="collapsed",
            disabled=st.session_state.is_generating,
        )
    with col2:
        send_clicked = st.button(
            "➤",
            key="send_button",
            use_container_width=True,
            disabled=st.session_state.is_generating or not user_input.strip(),
            help="Send (Enter) • New line (Shift+Enter)"
        )
    
    st.caption("AI-generated findings require verification against their sources. Press Enter to send, Shift+Enter for new line.")
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Handle submission
    if send_clicked and user_input.strip():
        handle_user_message(user_input.strip(), st.session_state.search_settings)
        st.session_state.composer_value = ""
        st.rerun()

# ═══════════════════════════════════════════════════════════════════
# MESSAGE HANDLING
# ═══════════════════════════════════════════════════════════════════

def handle_user_message(user_input: str, search_settings: Dict):
    """Handle a user message by starting the research workflow."""
    if not st.session_state.current_conversation_id:
        start_new_conversation()
    
    conv = st.session_state.conversations[st.session_state.current_conversation_id]
    
    # Add user message
    user_msg = ChatMessage(role=MessageRole.USER, content=user_input)
    conv.messages.append(user_msg)
    
    # Update conversation title based on first message
    if len(conv.messages) == 1:
        conv.title = user_input[:60] + ("…" if len(user_input) > 60 else "")
        save_conversation_to_db(conv)
        st.session_state.db_conversations = load_conversations_from_db()
    
    # Create assistant message with typing state
    assistant_msg = ChatMessage(
        role=MessageRole.ASSISTANT,
        content="",
        research_stages=list(ResearchStage),
        current_stage=ResearchStage.PLANNING,
        is_typing=True,
    )
    conv.messages.append(assistant_msg)
    
    # Update state
    st.session_state.is_generating = True
    st.session_state.current_conv = conv
    
    # Run research workflow
    try:
        result = asyncio.run(run_research_workflow(user_input, conv, search_settings))
        conv.messages[-1] = result
        conv.updated_at = datetime.now()
        save_conversation_to_db(conv)
    except Exception as e:
        error_msg = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=f"Research failed: {str(e)}",
            research_stages=list(ResearchStage),
            current_stage=ResearchStage.COMPLETED,
            error=str(e),
        )
        conv.messages[-1] = error_msg
    finally:
        st.session_state.is_generating = False
    
    st.rerun()

# ═══════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════

def main():
    # Initialize sidebar state
    if "show_paper_explorer" not in st.session_state:
        st.session_state.show_paper_explorer = False
    if "show_settings" not in st.session_state:
        st.session_state.show_settings = False
    if "show_mobile_sidebar" not in st.session_state:
        st.session_state.show_mobile_sidebar = False
    
    # Load conversations from DB on first load
    if "db_conversations" not in st.session_state:
        st.session_state.db_conversations = load_conversations_from_db()
    
    # Mobile overlay
    if st.session_state.show_mobile_sidebar:
        st.markdown('<div class="mobile-overlay active" onclick="window.parent.close_mobile_sidebar()"></div>', unsafe_allow_html=True)
    
    # Render sidebar
    render_sidebar()
    
    # Mobile sidebar toggle
    if st.session_state.show_mobile_sidebar:
        st.markdown('<div class="mobile-overlay active"></div>', unsafe_allow_html=True)
    
    # Main layout
    if st.session_state.show_paper_explorer or st.session_state.show_settings:
        col_main, col_panel = st.columns([1, 0.35], gap="medium")
    else:
        col_main = st.container()
        col_panel = None
    
    with col_main:
        # Main chat area
        if st.session_state.current_conversation_id is None:
            # Welcome screen
            render_welcome_screen()
        else:
            # Chat conversation
            conv = st.session_state.conversations.get(st.session_state.current_conversation_id)
            if conv:
                # Chat header
                st.markdown(f"""
                <div class="chat-header">
                    <div class="chat-header-left">
                        <span class="chat-title">{conv.title}</span>
                    </div>
                    <div class="chat-status">
                        <span class="status-indicator {'offline' if not settings.nvidia_api_key else ''}"></span>
                        <span>{settings.llm_provider.title()}: {settings.nvidia_model if settings.llm_provider == 'nvidia' else settings.ollama_model}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Messages area
                st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
                
                for i, msg in enumerate(conv.messages):
                    render_chat_message(msg, i)
                    
                    # Show typing indicator for active generation
                    if msg.is_typing and msg.role == MessageRole.ASSISTANT:
                        render_typing_indicator()
                
                st.markdown('<div id="chat-bottom"></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Paper explorer trigger
                if conv.messages and conv.messages[-1].papers and not st.session_state.show_paper_explorer:
                    if st.button("📄 Open Paper Explorer", use_container_width=True):
                        st.session_state.show_paper_explorer = True
                        st.rerun()
    
    # Side panel (paper explorer or settings)
    if col_panel:
        with col_panel:
            if st.session_state.show_paper_explorer:
                conv = st.session_state.conversations.get(st.session_state.current_conversation_id)
                if conv and conv.messages:
                    last_msg = conv.messages[-1]
                    if last_msg.papers:
                        render_paper_explorer_panel(last_msg.papers)
                    else:
                        st.info("No papers to display")
                        if st.button("Close"):
                            st.session_state.show_paper_explorer = False
                            st.rerun()
                else:
                    if st.button("Close"):
                        st.session_state.show_paper_explorer = False
                        st.rerun()
            
            if st.session_state.show_settings:
                render_settings_panel()
    
    # Message composer (always at bottom)
    render_message_composer()

if __name__ == "__main__":
    main()