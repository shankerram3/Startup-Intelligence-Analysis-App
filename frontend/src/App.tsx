import { useState, useEffect } from 'react';
import { CombinedQueryChatView } from './components/CombinedQueryChatView';
import { SemanticSearchView } from './components/SemanticSearchView';
import { DashboardView } from './components/DashboardView';
import { Neo4jDashboard } from './components/Neo4jDashboard';
import { EnhancedDashboardView } from './components/EnhancedDashboardView';
import { LandingPage } from './components/LandingPage';
import DocumentationPage from './components/DocumentationPage';

type TabKey = 'home' | 'query' | 'semantic' | 'dashboard' | 'pipeline' | 'auradb' | 'docs';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('home');

  // Handle hash routing
  useEffect(() => {
    const hash = window.location.hash.slice(1);
    if (hash && ['home', 'query', 'semantic', 'dashboard', 'pipeline', 'auradb', 'docs'].includes(hash)) {
      setActiveTab(hash as TabKey);
    }

    const handleHashChange = () => {
      const newHash = window.location.hash.slice(1);
      if (newHash && ['home', 'query', 'semantic', 'dashboard', 'pipeline', 'auradb', 'docs'].includes(newHash)) {
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
          background: rgba(255, 255, 255, 0.15) !important;
        }
        [data-nav-button]:active {
          transform: scale(0.98);
        }
      `}</style>
      <header style={styles.header}>
        <div style={styles.headerContainer}>
          <div style={styles.headerLeft}>
            <div style={styles.logoContainer}>
              <div style={styles.logoIcon}>🚀</div>
              <div style={styles.logoText}>
                <h1 style={styles.title}>GraphRAG</h1>
                <p style={styles.subtitle}>Knowledge Graph Platform</p>
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
              style={{ ...styles.navButton, ...(activeTab === 'dashboard' ? styles.navButtonActive : {}) }}
              onClick={() => { setActiveTab('dashboard'); window.location.hash = 'dashboard'; }}
            >
              <span style={styles.navIcon}>📊</span>
              <span>Stats</span>
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
        styles.main
      }>
        {activeTab === 'home' && <LandingPage />}
        {activeTab === 'query' && <CombinedQueryChatView />}
        {activeTab === 'semantic' && <SemanticSearchView />}
        {activeTab === 'pipeline' && <EnhancedDashboardView />}
        {activeTab === 'dashboard' && <DashboardView />}
        {activeTab === 'auradb' && <Neo4jDashboard />}
        {activeTab === 'docs' && <DocumentationPage />}
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  appRoot: {
    fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif',
    color: '#0f172a',
    background: '#f8fafc',
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden'
  },
  header: {
    background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
    flexShrink: 0
  },
  headerContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 24px',
    gap: 24,
    maxWidth: '100%'
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    flexShrink: 0
  },
  logoContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: 12
  },
  logoIcon: {
    fontSize: 32,
    lineHeight: 1,
    filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2))'
  },
  logoText: {
    display: 'flex',
    flexDirection: 'column',
    gap: 0
  },
  title: {
    margin: 0,
    fontSize: 22,
    fontWeight: 700,
    color: 'white',
    lineHeight: 1.2,
    letterSpacing: '-0.02em'
  },
  subtitle: {
    margin: 0,
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.9)',
    fontWeight: 400,
    lineHeight: 1.2
  },
  nav: {
    display: 'flex',
    alignItems: 'center',
    gap: 4,
    flex: 1,
    justifyContent: 'center',
    overflowX: 'auto',
    scrollbarWidth: 'none',
    msOverflowStyle: 'none'
  },
  navButton: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '10px 16px',
    borderRadius: 10,
    border: 'none',
    background: 'rgba(255, 255, 255, 0.1)',
    color: 'rgba(255, 255, 255, 0.9)',
    cursor: 'pointer',
    fontSize: 14,
    fontWeight: 500,
    transition: 'all 0.2s ease',
    whiteSpace: 'nowrap',
    backdropFilter: 'blur(10px)',
    position: 'relative'
  },
  navButtonActive: {
    background: 'rgba(255, 255, 255, 0.2)',
    color: 'white',
    fontWeight: 600,
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.2)'
  },
  navIcon: {
    fontSize: 16,
    lineHeight: 1,
    display: 'inline-flex',
    alignItems: 'center'
  },
  main: {
    padding: 24,
    maxWidth: 1100,
    margin: '0 auto',
    width: '100%',
    height: '100%',
    overflow: 'auto',
    flex: 1,
    minHeight: 0
  },
  mainFull: {
    padding: 24,
    width: '100%',
    maxWidth: '100%',
    boxSizing: 'border-box',
    overflowX: 'hidden',
    height: '100%',
    overflowY: 'auto',
    flex: 1,
    minHeight: 0
  },
  mainWide: {
    padding: 24,
    maxWidth: 1400,
    margin: '0 auto',
    width: '100%',
    height: '100%',
    overflow: 'auto',
    flex: 1,
    minHeight: 0
  }
};


