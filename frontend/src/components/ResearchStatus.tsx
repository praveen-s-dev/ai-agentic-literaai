import { researchStageLabels, researchStageIcons, type ResearchStage } from '../types/researchStages';
import type { ResearchProgress } from '../types';
import '../styles/ResearchStatus.css';

interface ResearchStatusProps {
  progress: ResearchProgress;
}

export function ResearchStatus({ progress }: ResearchStatusProps) {
  const allStages: ResearchStage[] = [
    'planning', 'searching', 'filtering', 'retrieving', 'processing',
    'analyzing', 'comparing', 'verifying', 'gap_discovery', 'report_generation', 'completed'
  ];

  return (
    <div className="research-status" role="status" aria-live="polite">
      <div className="status-header">
        <div className="status-title">
          <span className="status-icon">{researchStageIcons[progress.current_stage]}</span>
          <span>{researchStageLabels[progress.current_stage]}</span>
        </div>
        <div className="status-progress">
          {progress.progress_percent}%
        </div>
      </div>

      <div className="status-bar">
        <div 
          className="status-bar-fill" 
          style={{ width: `${progress.progress_percent}%` }}
        />
      </div>

      <div className="status-steps">
        {allStages.map((stage, index) => {
          const isCompleted = progress.completed_stages.includes(stage);
          const isCurrent = stage === progress.current_stage;
          const isPending = !isCompleted && !isCurrent;

          return (
            <div 
              key={stage} 
              className={`status-step ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''} ${isPending ? 'pending' : ''}`}
            >
              <div className="step-marker">
                {isCompleted ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                ) : isCurrent ? (
                  <div className="spinner" />
                ) : (
                  <span className="step-number">{index + 1}</span>
                )}
              </div>
              <span className="step-label">{researchStageLabels[stage]}</span>
            </div>
          );
        })}
      </div>

      <div className="status-message">
        {progress.message}
      </div>
    </div>
  );
}