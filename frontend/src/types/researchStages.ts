export const researchStageLabels: Record<string, string> = {
  planning: 'Planning research strategy',
  searching: 'Searching academic sources',
  filtering: 'Filtering relevant papers',
  retrieving: 'Retrieving open-access documents',
  processing: 'Processing paper content',
  analyzing: 'Analyzing papers',
  comparing: 'Comparing findings',
  verifying: 'Verifying evidence',
  gap_discovery: 'Discovering research gaps',
  report_generation: 'Generating final report',
  completed: 'Research complete',
  failed: 'Research failed',
};

export const researchStageIcons: Record<string, string> = {
  planning: '🎯',
  searching: '🔍',
  filtering: '📋',
  retrieving: '📥',
  processing: '⚙️',
  analyzing: '🔬',
  comparing: '⚖️',
  verifying: '✅',
  gap_discovery: '💡',
  report_generation: '📄',
  completed: '✨',
  failed: '❌',
};

export type ResearchStage = 
  | 'planning'
  | 'searching'
  | 'filtering'
  | 'retrieving'
  | 'processing'
  | 'analyzing'
  | 'comparing'
  | 'verifying'
  | 'gap_discovery'
  | 'report_generation'
  | 'completed'
  | 'failed';