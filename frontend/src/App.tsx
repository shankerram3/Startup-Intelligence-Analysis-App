import { useState, useEffect } from 'react';
import { CombinedQueryChatView } from './components/CombinedQueryChatView';
import { SemanticSearchView } from './components/SemanticSearchView';
import { Neo4jDashboard } from './components/Neo4jDashboard';
import { EnhancedDashboardView } from './components/EnhancedDashboardView';
import { LandingPage } from './components/LandingPage';
import DocumentationPage from './components/DocumentationPage';
import { AuraDBAnalyticsDashboard } from './components/AuraDBAnalyticsDashboard';
import { ThemeExtractionView } from './components/ThemeExtractionView';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import { EvaluationDashboard } from './components/EvaluationDashboard';

type TabKey = 'home' | 'query' | 'semantic' | 'pipeline' | 'auradb' | 'themes' | 'analytics' | 'evaluation' | 'docs';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('home');

  // Handle hash routing
  useEffect(() => {
    const hash = window.location.hash.slice(1);
    if (hash && ['home', 'query', 'semantic', 'pipeline', 'auradb', 'themes', 'analytics', 'evaluation', 'docs'].includes(hash)) {
      setActiveTab(hash as TabKey);
    }

    const handleHashChange = () => {
      const newHash = window.location.hash.slice(1);
      if (newHash && ['home', 'query', 'semantic', 'pipeline', 'auradb', 'themes', 'analytics', 'evaluation', 'docs'].includes(newHash)) {
        setActiveTab(newHash as TabKey);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  return (
    <div style={styles.appRoot}>
      <style>{`
        /* Hide scrollbar for nav */
        nav::-webkit-scrollbar {
          display: none;
        }
        /* Hover effects for nav buttons */
        [data-nav-button]:hover {
          background: rgba(59, 130, 246, 0.15) !important;
          color: #60a5fa !important;
          box-shadow: 0 0 20px rgba(59, 130, 246, 0.3), inset 0 0 20px rgba(59, 130, 246, 0.1) !important;
          transform: translateY(-1px) !important;
        }
        [data-nav-button]:active {
          transform: scale(0.98) translateY(0) !important;
        }
        
        /* Futuristic header glow animation */
        @keyframes pulseGlow {
          0%, 100% {
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.2), 0 0 40px rgba(59, 130, 246, 0.1);
          }
          50% {
            box-shadow: 0 0 30px rgba(59, 130, 246, 0.4), 0 0 60px rgba(59, 130, 246, 0.2);
          }
        }
        
        @keyframes scanLine {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
        
        /* Minimal scrollbar styling for all elements */
        * {
          scrollbar-width: thin;
          scrollbar-color: rgba(100, 116, 139, 0.3) transparent;
        }
        
        *::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        
        *::-webkit-scrollbar-track {
          background: transparent;
        }
        
        *::-webkit-scrollbar-thumb {
          background: rgba(100, 116, 139, 0.3);
          border-radius: 3px;
        }
        
        *::-webkit-scrollbar-thumb:hover {
          background: rgba(100, 116, 139, 0.5);
        }
        
        *::-webkit-scrollbar-corner {
          background: transparent;
        }
      `}</style>
      <header style={styles.header}>
        <div style={styles.headerGlow}></div>
        <div style={styles.headerContainer}>
          <div style={styles.headerLeft}>
            <div style={styles.logoContainer}>
              <div style={styles.logoIcon}>🚀</div>
              <div style={styles.logoText}>
                <h1 style={styles.title}>TrendScout AI</h1>
                <p style={styles.subtitle}>powered by Graphrag engine RAGPiper</p>
              </div>
            </div>
          </div>
          <nav style={styles.nav}>
            <button
              data-nav-button
              style={{ ...styles.navButton, ...(activeTab === 'home' ? styles.navButtonActive : {}) }}
              onClick={() => { setActiveTab('home'); window.location.hash = 'home'; }}
            >
              <span style={styles.navIcon}>🏠</span>
              <span>Home</span>
            </button>
            <button
              data-nav-button
              style={{ ...styles.navButton, ...(activeTab === 'query' ? styles.navButtonActive : {}) }}
              onClick={() => { setActiveTab('query'); window.location.hash = 'query'; }}
            >
              <span style={styles.navIcon}>💬</span>
              <span>Query & Chat</span>
            </button>
            <button
              data-nav-button
              style={{ ...styles.navButton, ...(activeTab === 'semantic' ? styles.navButtonActive : {}) }}
              onClick={() => { setActiveTab('semantic'); window.location.hash = 'semantic'; }}
            >
              <span style={styles.navIcon}>🎯</span>
              <span>Semantic Search</span>
            </button>
            <button
              data-nav-button
              style={{ ...styles.navButton, ...(activeTab === 'pipeline' ? styles.navButtonActive : {}) }}
              onClick={() => { setActiveTab('pipeline'); window.location.hash = 'pipeline'; }}
            >
              <span style={styles.navIcon}>⚙️</span>
              <span>Pipeline</span>
            </button>
            <button
              data-nav-button
              style={{ ...styles.navButton, ...(activeTab === 'auradb' ? styles.navButtonActive : {}) }}
              onClick={() => { setActiveTab('auradb'); window.location.hash = 'auradb'; }}
            >
              <span style={styles.navIcon}>📊</span>
              <span>AuraDB Analytics</span>
            </button>
            <button
              data-nav-button
              style={{ ...styles.navButton, ...(activeTab === 'themes' ? styles.navButtonActive : {}) }}
              onClick={() => { setActiveTab('themes'); window.location.hash = 'themes'; }}
            >
              <span style={styles.navIcon}>🎨</span>
              <span>Recurring Themes</span>
            </button>
            <button
              data-nav-button
              style={{ ...styles.navButton, ...(activeTab === 'analytics' ? styles.navButtonActive : {}) }}
              onClick={() => { setActiveTab('analytics'); window.location.hash = 'analytics'; }}
            >
              <span style={styles.navIcon}>📈</span>
              <span>Analytics</span>
            </button>
            <button
              data-nav-button
              style={{ ...styles.navButton, ...(activeTab === 'evaluation' ? styles.navButtonActive : {}) }}
              onClick={() => { setActiveTab('evaluation'); window.location.hash = 'evaluation'; }}
            >
              <span style={styles.navIcon}>🧪</span>
              <span>Evaluation</span>
            </button>
            <button
              data-nav-button
              style={{ ...styles.navButton, ...(activeTab === 'docs' ? styles.navButtonActive : {}) }}
              onClick={() => { setActiveTab('docs'); window.location.hash = 'docs'; }}
            >
              <span style={styles.navIcon}>📚</span>
              <span>Docs</span>
            </button>
          </nav>
        </div>
      </header>

      <main style={
        activeTab === 'docs' ? styles.mainFull : 
        activeTab === 'home' ? styles.mainFull :
        activeTab === 'pipeline' ? styles.mainWide : 
        activeTab === 'query' ? styles.mainFull : 
        activeTab === 'auradb' ? styles.mainFull :
        activeTab === 'themes' ? styles.mainFull :
        activeTab === 'analytics' ? styles.mainFull :
        activeTab === 'evaluation' ? styles.mainFull :
        styles.main
      }>
        {activeTab === 'home' && <LandingPage />}
        {activeTab === 'query' && <CombinedQueryChatView />}
        {activeTab === 'semantic' && <SemanticSearchView />}
        {activeTab === 'pipeline' && <EnhancedDashboardView />}
        {activeTab === 'auradb' && <AuraDBAnalyticsDashboard />}
        {activeTab === 'themes' && <ThemeExtractionView />}
        {activeTab === 'analytics' && <AnalyticsDashboard />}
        {activeTab === 'evaluation' && <EvaluationDashboard />}
        {activeTab === 'docs' && <DocumentationPage />}
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  appRoot: {
    fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif',
    color: '#f1f5f9',
    background: '#0f172a',
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden'
  },
  header: {
    background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 50%, rgba(15, 23, 42, 0.95) 100%)',
    borderBottom: '1px solid rgba(59, 130, 246, 0.2)',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(59, 130, 246, 0.1) inset, 0 0 60px rgba(59, 130, 246, 0.1)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
    flexShrink: 0,
    backdropFilter: 'blur(20px) saturate(180%)',
    WebkitBackdropFilter: 'blur(20px) saturate(180%)',
    overflow: 'hidden'
  },
  headerContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 32px',
    gap: 32,
    maxWidth: '100%',
    position: 'relative',
    zIndex: 1
  },
  headerGlow: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '2px',
    background: 'linear-gradient(90deg, transparent 0%, rgba(59, 130, 246, 0.8) 50%, transparent 100%)',
    animation: 'scanLine 3s linear infinite',
    zIndex: 0
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    flexShrink: 0,
    position: 'relative',
    zIndex: 1
  },
  logoContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: 12
  },
  logoIcon: {
    fontSize: 36,
    lineHeight: 1,
    filter: 'drop-shadow(0 0 10px rgba(59, 130, 246, 0.5)) drop-shadow(0 0 20px rgba(59, 130, 246, 0.3))',
    animation: 'pulseGlow 3s ease-in-out infinite',
    transform: 'perspective(1000px) rotateY(-5deg)',
    transition: 'all 0.3s ease'
  },
  logoText: {
    display: 'flex',
    flexDirection: 'column',
    gap: 0
  },
  title: {
    margin: 0,
    fontSize: 24,
    fontWeight: 800,
    background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #2563eb 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    lineHeight: 1.2,
    letterSpacing: '-0.03em',
    textShadow: '0 0 30px rgba(59, 130, 246, 0.3)',
    fontFamily: 'system-ui, -apple-system, "SF Pro Display", "Segoe UI", Roboto, sans-serif'
  },
  subtitle: {
    margin: 0,
    fontSize: 11,
    color: 'rgba(148, 163, 184, 0.9)',
    fontWeight: 500,
    lineHeight: 1.2,
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    fontFamily: 'system-ui, -apple-system, "SF Mono", "Monaco", monospace'
  },
  nav: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    flex: 1,
    overflowX: 'auto',
    scrollbarWidth: 'none',
    msOverflowStyle: 'none'
  },
  navButton: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '10px 18px',
    borderRadius: 12,
    border: '1px solid rgba(59, 130, 246, 0.1)',
    background: 'rgba(15, 23, 42, 0.3)',
    color: 'rgba(203, 213, 225, 0.9)',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 600,
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    whiteSpace: 'nowrap',
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    position: 'relative',
    overflow: 'hidden',
    letterSpacing: '0.01em',
    fontFamily: 'system-ui, -apple-system, "SF Pro Display", sans-serif'
  },
  navButtonActive: {
    background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.25) 0%, rgba(37, 99, 235, 0.15) 100%)',
    color: '#60a5fa',
    fontWeight: 700,
    boxShadow: '0 4px 16px rgba(59, 130, 246, 0.3), 0 0 0 1px rgba(59, 130, 246, 0.2) inset, 0 0 30px rgba(59, 130, 246, 0.15)',
    border: '1px solid rgba(59, 130, 246, 0.4)',
    transform: 'translateY(-1px)'
  },
  navIcon: {
    fontSize: 18,
    lineHeight: 1,
    display: 'inline-flex',
    alignItems: 'center',
    filter: 'drop-shadow(0 0 4px rgba(59, 130, 246, 0.3))',
    transition: 'all 0.3s ease'
  },
  main: {
    padding: 24,
    maxWidth: 1100,
    margin: '0 auto',
    width: '100%',
    height: '100%',
    overflow: 'auto',
    flex: 1,
    minHeight: 0,
    background: '#0f172a',
    color: '#f1f5f9'
  },
  mainFull: {
    padding: 24,
    width: '100%',
    maxWidth: '100%',
    boxSizing: 'border-box',
    overflowX: 'hidden',
    overflowY: 'auto',
    flex: 1,
    minHeight: 0,
    maxHeight: '100%',
    background: '#0f172a',
    color: '#f1f5f9',
    WebkitOverflowScrolling: 'touch',
    position: 'relative'
  },
  mainWide: {
    padding: 24,
    maxWidth: 1400,
    margin: '0 auto',
    width: '100%',
    height: '100%',
    overflow: 'auto',
    flex: 1,
    minHeight: 0,
    background: '#0f172a',
    color: '#f1f5f9'
  }
};


