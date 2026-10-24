import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/variables.css'
import './styles/ChatWorkspace.css'
import './styles/Sidebar.css'
import './styles/Message.css'
import './styles/MessageComposer.css'
import './styles/WelcomeScreen.css'
import './styles/ResearchStatus.css'
import './styles/TypingIndicator.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)