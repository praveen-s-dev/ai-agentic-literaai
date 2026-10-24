import { BookOpen, GitBranch, Search, Lightbulb } from 'lucide-react';
import '../styles/WelcomeScreen.css';

interface WelcomeScreenProps {
  onSuggestionClick: (prompt: string) => void;
}

const suggestions = [
  {
    icon: BookOpen,
    title: 'Literature Review',
    prompt: 'Review research on AI-based intrusion detection.',
    description: 'Analyze existing research on a specific topic across multiple papers.',
  },
  {
    icon: GitBranch,
    title: 'Paper Comparison',
    prompt: 'Compare methodologies and datasets across papers.',
    description: 'Systematically compare methods, datasets, and results across studies.',
  },
  {
    icon: Search,
    title: 'Evidence Investigation',
    prompt: 'Investigate evidence supporting a scientific claim.',
    description: 'Find and verify evidence supporting or contradicting a specific claim.',
  },
  {
    icon: Lightbulb,
    title: 'Gap Discovery',
    prompt: 'Identify potential research gaps from multiple papers.',
    description: 'Discover recurring limitations and unexplored research directions.',
  },
];

export function WelcomeScreen({ onSuggestionClick }: WelcomeScreenProps) {
  return (
    <div className="welcome-screen" role="main">
      <div className="welcome-content">
        <div className="welcome-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
        </div>
        
        <h1 className="welcome-title">Your research starts here.</h1>
        
        <p className="welcome-subtitle">
          Explore academic literature, compare scientific evidence, and discover potential research gaps.
        </p>

        <div className="suggestion-cards" role="list" aria-label="Suggested research tasks">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              className="suggestion-card"
              onClick={() => onSuggestionClick(suggestion.prompt)}
              role="listitem"
            >
              <div className="suggestion-icon">
                <suggestion.icon size={24} />
              </div>
              <h3 className="suggestion-title">{suggestion.title}</h3>
              <p className="suggestion-description">{suggestion.description}</p>
              <div className="suggestion-prompt">
                <kbd>"{suggestion.prompt}"</kbd>
              </div>
            </button>
          ))}
        </div>

        <div className="welcome-footer">
          <p>Powered by NVIDIA Nemotron-3-Ultra • Evidence-grounded research with full traceability</p>
        </div>
      </div>
    </div>
  );
}