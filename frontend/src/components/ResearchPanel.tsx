import { Check, Loader2, ChevronRight, ChevronLeft, FileText, Search, Brain, GitBranch, AlertTriangle, Lightbulb, FileCheck, Square, AlertCircle } from 'lucide-react';
import type { ResearchStage, ResearchProgress } from '../types';
import '../styles/ResearchPanel.css';

interface ResearchPanelProps {
  progress: ResearchProgress | null;
  isGenerating: boolean;
  polling: boolean;
  result?: {
    citations?: any[];
    papers?: any[];
    report?: string;
    metadata?: any;
    error?: string;
  };
  error?: string;
  onClose: () => void;
  setShowResearchPanel: (show: boolean) => void;
  onStop: () => void;
}

const STAGE_CONFIG: Record<ResearchStage, { label: string; icon: any; description: string }> = {
  planning: { label: 'Planning', icon: Brain, description: 'Planning research strategy' },
  searching: { label: 'Searching', icon: Search, description: 'Searching academic sources' },
  filtering: { label: 'Filtering', icon: GitBranch, description: 'Filtering relevant papers' },
  retrieving: { label: 'Retrieving', icon: FileText, description: 'Retrieving open-access PDFs' },
  processing: { label: 'Processing', icon: Brain, description: 'Processing paper content' },
  analyzing: { label: 'Analyzing', icon: Brain, description: 'Analyzing individual papers' },
  comparing: { label: 'Comparing', icon: GitBranch, description: 'Comparing findings across papers' },
  verifying: { label: 'Verifying', icon: AlertTriangle, description: 'Verifying evidence & citations' },
  gap_discovery: { label: 'Gap Discovery', icon: Lightbulb, description: 'Identifying research gaps' },
  report_generation: { label: 'Report Generation', icon: FileCheck, description: 'Generating final report' },
  completed: { label: 'Completed', icon: Check, description: 'Research complete' },
  failed: { label: 'Failed', icon: AlertTriangle, description: 'Research failed' },
};

const STAGE_ORDER: ResearchStage[] = [
  'planning', 'searching', 'filtering', 'retrieving', 'processing',
  'analyzing', 'comparing', 'verifying', 'gap_discovery', 'report_generation', 'completed'
];

export function ResearchPanel({ progress, isGenerating, polling, result, error, onClose, setShowResearchPanel, onStop }: ResearchPanelProps) {
  const currentStage = progress?.current_stage || 'planning';
  const completedStages = progress?.completed_stages || [];
  const progressPercent = progress?.progress_percent || 0;
  const isFailed = progress?.current_stage === 'failed';
  const errorMessage = error || result?.error;
  const isCompleted = progress?.current_stage === 'completed' && !polling;
  const failedSources = progress?.failed_sources || [];

  const getStageStatus = (stage: ResearchStage): 'pending' | 'active' | 'completed' => {
    if (isFailed) return 'completed';
    if (stage === currentStage && isGenerating) return 'active';
    if (completedStages.includes(stage)) return 'completed';
    if (STAGE_ORDER.indexOf(stage) < STAGE_ORDER.indexOf(currentStage)) return 'completed';
    return 'pending';
  };

  const hasResults = result && (result.citations?.length || result.papers?.length || result.report);
  const hasReport = result?.report;

  // Completed State View - shows when research is done
  const CompletedView = () => {
    const hasPartialResults = failedSources.length > 0 && (result?.papers?.length || 0) > 0;
    
    return (
      <div className="completed-view">
        <div className="completion-icon">
          {hasPartialResults ? (
            <AlertTriangle size={48} className="partial-completion" />
          ) : (
            <Check size={48} />
          )}
        </div>
        <h3>{hasPartialResults ? 'Research Partially Complete' : 'Research Complete'}</h3>
        <p className="completion-message">
          {result?.papers?.length || 0} papers analyzed · 
          {result?.citations?.length || 0} citations · 
          {result?.metadata?.gaps_found || 0} research gaps
        </p>
        {failedSources.length > 0 && (
          <div className="partial-results-notice">
            <AlertCircle size={16} />
            <span>Some sources failed ({failedSources.join(', ')}). Results may be incomplete.</span>
          </div>
        )}
        <div className="completed-actions">
          {hasReport && (
            <button 
              className="action-btn primary"
              onClick={() => setShowResearchPanel(false)}
            >
              <FileText size={18} />
              <span>View Full Report in Chat</span>
            </button>
          )}
          <button 
            className="action-btn secondary"
            onClick={() => setShowResearchPanel(false)}
          >
            <ChevronLeft size={18} />
            <span>Back to Chat</span>
          </button>
        </div>
    </div>
  );
  };

  return (
    <aside className="research-panel" role="complementary" aria-label="Research workflow">
      <header className="research-panel-header">
        <h2>Research Workflow</h2>
        <div className="header-actions">
          {isGenerating && !isCompleted && !isFailed && (
            <button 
              className="stop-btn" 
              onClick={onStop}
              aria-label="Stop research"
              title="Stop research"
            >
              <Square size={18} />
            </button>
          )}
          <button className="close-btn" onClick={onClose} aria-label="Close panel">
            <ChevronRight size={20} />
          </button>
        </div>
      </header>

      <div className="research-panel-content">
        {/* Progress Overview */}
        <div className="progress-overview">
          <div className="progress-bar">
            <div 
              className={`progress-fill ${isFailed ? 'failed' : ''}`} 
              style={{ width: `${progressPercent}%` }} 
            />
          </div>
          <div className="progress-text">
            <span>{progressPercent}% Complete</span>
            <span>{currentStage.replace('_', ' ').toUpperCase()}</span>
          </div>
        </div>

        {/* Error Display */}
        {isFailed && errorMessage && (
          <div className="research-error" role="alert">
            <AlertTriangle size={18} />
            <span>Research failed: {errorMessage}</span>
          </div>
        )}

        {/* Failed Sources Warning */}
        {failedSources.length > 0 && (
          <div className="failed-sources-warning" role="alert">
            <AlertCircle size={18} />
            <div className="failed-sources-content">
              <span className="failed-sources-label">Some sources failed:</span>
              <span className="failed-sources-list">{failedSources.join(', ')}</span>
              <span className="failed-sources-note">Results may be incomplete</span>
            </div>
          </div>
        )}

        {/* Completed State View */}
        {isCompleted && <CompletedView />}

        {/* Workflow Steps (only show when not completed) */}
        {!isCompleted && (
          <>
            {/* Workflow Steps */}
            <nav className="workflow-steps" aria-label="Research steps">
              {STAGE_ORDER.map((stage, index) => {
                const config = STAGE_CONFIG[stage];
                const status = getStageStatus(stage);
                const isLast = index === STAGE_ORDER.length - 1;
                
                return (
                  <div key={stage} className={`workflow-step ${status}`}>
                    <div className="step-connector">
                      {!isLast && <div className="connector-line" />}
                      <div className={`step-marker ${status}`}>
                        {status === 'completed' && <Check size={14} />}
                        {status === 'active' && <Loader2 size={14} className="spinning" />}
                        {status === 'pending' && <span className="step-number">{index + 1}</span>}
                      </div>
                    </div>
                    <div className="step-content">
                      <div className="step-header">
                        <config.icon size={16} className="step-icon" />
                        <span className="step-label">{config.label}</span>
                        {status === 'active' && <span className="step-badge">IN PROGRESS</span>}
                        {status === 'completed' && <Check size={14} className="step-done" />}
                      </div>
                      <p className="step-description">{config.description}</p>
                    </div>
                  </div>
                );
              })}
            </nav>

            {/* Report Generation Status */}
            {hasReport && currentStage === 'report_generation' && (
              <div className="report-generation-status">
                <FileCheck size={20} className="spinning" />
                <span>Generating final report...</span>
              </div>
            )}

            {/* Results Summary */}
            {hasResults && !isFailed && !isCompleted && (
              <div className="results-summary">
                <h3>Results</h3>
                <div className="result-items">
                  {result.citations?.length && (
                    <div className="result-item">
                      <FileText size={16} />
                      <span>{result.citations.length} citations</span>
                    </div>
                  )}
                  {result.papers?.length && (
                    <div className="result-item">
                      <GitBranch size={16} />
                      <span>{result.papers.length} papers analyzed</span>
                    </div>
                  )}
                  {result.report && (
                    <div className="result-item">
                      <FileCheck size={16} />
                      <span>Report generated</span>
                    </div>
                  )}
                  {result.metadata?.gaps_found && (
                    <div className="result-item">
                      <Lightbulb size={16} />
                      <span>{result.metadata.gaps_found} research gaps</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </aside>
  );
}