import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import { Send, Settings, Mic, Paperclip, Cpu, Zap, Thermometer, Sparkles } from 'lucide-react';
import '../styles/MessageComposer.css';

interface MessageComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSend: (content: string, isResearch: boolean) => void;
  disabled?: boolean;
  placeholder?: string;
}

const MODEL_PROVIDERS = [
  { id: 'nvidia', name: 'NVIDIA', icon: Cpu, models: ['nemotron-3-ultra', 'nemotron-4-340b', 'llama-3.1-405b', 'llama-3.1-70b', 'mixtral-8x22b'] },
  { id: 'ollama', name: 'Ollama (Local)', icon: Cpu, models: ['llama3.2', 'llama3.2:70b', 'mistral', 'codellama', 'gemma2'] },
  { id: 'openai', name: 'OpenAI', icon: Zap, models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'] },
];

const DEFAULT_MODELS = {
  nvidia: 'nemotron-3-ultra',
  ollama: 'llama3.2',
  openai: 'gpt-4o-mini',
};

export function MessageComposer({ value, onChange, onSend, disabled, placeholder }: MessageComposerProps) {
  const [showSettings, setShowSettings] = useState(false);
  const [sources, setSources] = useState(['OpenAlex']);
  const [maxPapers, setMaxPapers] = useState(3);
  const [openAccessOnly, setOpenAccessOnly] = useState(true);
  const [minYear, setMinYear] = useState(2022);
  
  // Fast Mode state
  const [fastMode, setFastMode] = useState(true);
  
  // Research mode state
  const [isResearchMode, setIsResearchMode] = useState(false);
  
  // Model settings
  const [provider, setProvider] = useState('nvidia');
  const [model, setModel] = useState(DEFAULT_MODELS.nvidia);
  const [temperature, setTemperature] = useState(0.3);
  const [topP, setTopP] = useState(0.9);
  const [maxTokens, setMaxTokens] = useState(2048);

const textareaRef = useRef<HTMLTextAreaElement>(null);
  const settingsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: globalThis.KeyboardEvent) => {
      if (e.key === 'Escape' && showSettings) {
        setShowSettings(false);
      }
    };
    const handleClickOutside = (e: globalThis.MouseEvent) => {
      if (showSettings && settingsRef.current && !settingsRef.current.contains(e.target as Node)) {
        setShowSettings(false);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showSettings]);

  const handleTextareaKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled) {
        const isResearch = value.trim().startsWith('@research') || isResearchMode;
        const content = isResearch ? value.trim().replace(/^@research\s*/, '') : value.trim();
        onSend(content, isResearch);
      }
    }
  };
  
  const handleSubmit = () => {
    if (value.trim() && !disabled) {
      const isResearch = value.trim().startsWith('@research') || isResearchMode;
      const content = isResearch ? value.trim().replace(/^@research\s*/, '') : value.trim();
      onSend(content, isResearch);
    }
  };
  
  const handleResearchClick = () => {
    if (value.trim() && !disabled) {
      const isResearch = true;
      const content = value.trim().replace(/^@research\s*/, '');
      onSend(content, isResearch);
    }
  };

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const availableSources = ['OpenAlex', 'Semantic Scholar', 'Crossref', 'arXiv'];
  const currentProvider = MODEL_PROVIDERS.find(p => p.id === provider);
  const availableModels = currentProvider?.models || [];

  return (
    <div className="message-composer">
      {showSettings && (
        <div ref={settingsRef} className="composer-settings">
          {/* Fast Mode Toggle */}
          <div className="fast-mode-toggle">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={fastMode}
                onChange={e => {
                  const enabled = e.target.checked;
                  setFastMode(enabled);
                  if (enabled) {
                    setSources(['OpenAlex']);
                    setMaxPapers(3);
                    setMinYear(2022);
                    setOpenAccessOnly(true);
                    setProvider('nvidia');
                    setModel('nemotron-3-ultra');
                    setTemperature(0.1);
                    setTopP(0.9);
                    setMaxTokens(1024);
                    setIsResearchMode(false);
                  }
                }}
              />
              <span>⚡ Fast Mode (OpenAlex only, 3 papers, recent years, low temperature)</span>
            </label>
          </div>

          {/* Model Selection */}
          <div className="settings-section">
            <h4>
              <Cpu size={16} />
              <span>Model</span>
            </h4>
            <div className="settings-grid">
              <div className="settings-field">
                <label>
                  <span>Provider</span>
                  <select
                    value={provider}
                    onChange={e => {
                      const newProvider = e.target.value;
                      setProvider(newProvider);
                      setModel(DEFAULT_MODELS[newProvider as keyof typeof DEFAULT_MODELS]);
                    }}
                    disabled={disabled}
                  >
                    {MODEL_PROVIDERS.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="settings-field">
                <label>
                  <span>Model</span>
                  <select
                    value={model}
                    onChange={e => setModel(e.target.value)}
                    disabled={disabled}
                  >
                    {availableModels.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </label>
              </div>
            </div>

            <div className="settings-grid">
              <div className="settings-field">
                <label>
                  <span>Temperature <span className="value-badge">{temperature.toFixed(1)}</span></span>
                  <input
                    type="range"
                    min={0}
                    max={2}
                    step={0.1}
                    value={temperature}
                    onChange={e => setTemperature(parseFloat(e.target.value))}
                    disabled={disabled}
                  />
                </label>
              </div>
              <div className="settings-field">
                <label>
                  <span>Top-p <span className="value-badge">{topP.toFixed(1)}</span></span>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={topP}
                    onChange={e => setTopP(parseFloat(e.target.value))}
                    disabled={disabled}
                  />
                </label>
              </div>
            </div>

            <div className="settings-field full-width">
              <label>
                <span>Max Tokens</span>
                <input
                  type="number"
                  min={100}
                  max={8192}
                  step={100}
                  value={maxTokens}
                  onChange={e => setMaxTokens(Math.max(100, Math.min(8192, parseInt(e.target.value) || 100)))}
                  disabled={disabled}
                />
              </label>
            </div>
          </div>

          {/* Research Settings */}
          <div className="settings-section">
            <h4>
              <Zap size={16} />
              <span>Research Settings</span>
            </h4>
            <div className="settings-grid">
              <div className="settings-field">
                <label>
                  <span>Sources</span>
                  <div className="source-chips">
                    {availableSources.map(source => (
                      <label key={source} className="chip">
                        <input
                          type="checkbox"
                          checked={sources.includes(source)}
                          onChange={e => setSources(prev => 
                            e.target.checked 
                              ? [...prev, source] 
                              : prev.filter(s => s !== source)
                          )}
                          disabled={disabled}
                        />
                        {source}
                      </label>
                    ))}
                  </div>
                </label>
              </div>
            </div>

            <div className="settings-grid">
              <div className="settings-field">
                <label>
                  <span>Max Papers</span>
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={maxPapers}
                    onChange={e => setMaxPapers(Math.max(1, Math.min(100, parseInt(e.target.value) || 1)))}
                    disabled={disabled}
                  />
                </label>
              </div>
              <div className="settings-field">
                <label>
                  <span>Min Year</span>
                  <input
                    type="number"
                    min={1900}
                    max={new Date().getFullYear()}
                    value={minYear}
                    onChange={e => setMinYear(Math.max(1900, Math.min(new Date().getFullYear(), parseInt(e.target.value) || 1900)))}
                    disabled={disabled}
                  />
                </label>
              </div>
            </div>

            <div className="settings-field checkbox-field">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={openAccessOnly}
                  onChange={e => setOpenAccessOnly(e.target.checked)}
                  disabled={disabled}
                />
                <span>Open Access Only</span>
              </label>
            </div>
          </div>

          {/* Quick model indicator */}
          <div className="model-indicator">
            <span className="model-badge">
              {currentProvider && <currentProvider.icon size={12} />}
              {currentProvider?.name}: {model}
            </span>
            <span className="model-params">
              <Thermometer size={12} /> {temperature} • <Zap size={12} /> {topP} • {maxTokens} tokens
            </span>
          </div>
        </div>
      )}

      <div className="composer-input-wrapper">
        <div className="composer-textarea-wrapper">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={e => onChange(e.target.value)}
            onKeyDown={handleTextareaKeyDown}
            placeholder={isResearchMode ? "Research topic... (or type @research to start research)" : placeholder}
            disabled={disabled}
            rows={1}
            className="composer-textarea"
            aria-label={isResearchMode ? "Research topic" : "Chat message"}
          />
          {value.startsWith('@research') && (
            <span className="research-indicator">🔬 Research mode active</span>
          )}
        </div>

        <div className="composer-actions">
          <button
            className="action-btn"
            onClick={() => setShowSettings(!showSettings)}
            aria-label={showSettings ? 'Hide settings' : 'Show settings'}
            title={showSettings ? 'Hide settings' : 'Settings (model, research, parameters)'}
          >
            <Settings size={20} />
          </button>

          <button
            className="action-btn attach-btn"
            disabled
            aria-label="Attach files (coming soon)"
            title="Attach files (coming soon)"
          >
            <Paperclip size={20} />
          </button>

          <button
            className="action-btn mic-btn"
            disabled
            aria-label="Voice input (coming soon)"
            title="Voice input (coming soon)"
          >
            <Mic size={20} />
          </button>

          {/* Research Button */}
          <button
            className={`action-btn research-btn ${isResearchMode ? 'active' : ''}`}
            onClick={handleResearchClick}
            disabled={disabled || !value.trim()}
            aria-label="Start research workflow"
            title="Start full research workflow (search, analyze, compare, gaps, report)"
          >
            <Sparkles size={20} />
          </button>

          <button
            className="send-btn"
            onClick={handleSubmit}
            disabled={disabled || !value.trim()}
            aria-label={isResearchMode ? "Start research" : "Send message"}
          >
            <Send size={20} />
          </button>
        </div>
      </div>

      <div className="composer-hint">
        {isResearchMode 
          ? "Enter: Start research workflow | Shift+Enter: New line | Type @research to trigger"
          : "Enter: Send message | Shift+Enter: New line | Type @research for research | Click ⚡ for workflow"}
      </div>
    </div>
  );
}