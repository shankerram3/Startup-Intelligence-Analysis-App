import { useState } from 'react';
import { CombinedQueryChatView } from './components/CombinedQueryChatView';
import { SemanticSearchView } from './components/SemanticSearchView';
import { DashboardView } from './components/DashboardView';
import { Neo4jDashboard } from './components/Neo4jDashboard';
import { EnhancedDashboardView } from './components/EnhancedDashboardView';

type TabKey = 'query' | 'semantic' | 'dashboard' | 'pipeline' | 'auradb';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('query');
  const [useEnhanced, setUseEnhanced] = useState(true);

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
              style={{ ...styles.navButton, ...(activeTab === 'query' ? styles.navButtonActive : {}) }}
              onClick={() => setActiveTab('query')}
            >
              <span style={styles.navIcon}>💬</span>
              <span>Query & Chat</span>
            </button>
            <button
              data-nav-button
              style={{ ...styles.navButton, ...(activeTab === 'semantic' ? styles.navButtonActive : {}) }}
              onClick={() => setActiveTab('semantic')}
            >
              <span style={styles.navIcon}>🎯</span>
              <span>Semantic Search</span>
            </button>
            <button
              data-nav-button
              style={{ ...styles.navButton, ...(activeTab === 'pipeline' ? styles.navButtonActive : {}) }}
              onClick={() => setActiveTab('pipeline')}
            >
              <span style={styles.navIcon}>⚙️</span>
              <span>Pipeline</span>
            </button>
            <button
              data-nav-button
              style={{ ...styles.navButton, ...(activeTab === 'dashboard' ? styles.navButtonActive : {}) }}
              onClick={() => setActiveTab('dashboard')}
            >
              <span style={styles.navIcon}>📊</span>
              <span>Stats</span>
            </button>
            <button
              data-nav-button
              style={{ ...styles.navButton, ...(activeTab === 'auradb' ? styles.navButtonActive : {}) }}
              onClick={() => setActiveTab('auradb')}
            >
              <span style={styles.navIcon}>🧠</span>
              <span>AuraDB</span>
            </button>
          </nav>
          <div style={styles.headerRight}>
            <label style={styles.toggleLabel} onClick={(e) => e.stopPropagation()}>
              <input
                type="checkbox"
                checked={useEnhanced}
                onChange={(e) => setUseEnhanced(e.target.checked)}
                style={styles.toggleInput}
              />
              <span style={{
                ...styles.toggleSwitch,
                background: useEnhanced ? 'rgba(255, 255, 255, 0.5)' : 'rgba(255, 255, 255, 0.3)'
              }}>
                <span style={{
                  ...styles.toggleKnob,
                  transform: useEnhanced ? 'translateX(18px)' : 'translateX(2px)'
                }}></span>
              </span>
              <span style={styles.toggleText}>Enhanced</span>
            </label>
          </div>
        </div>
      </header>

      <main style={activeTab === 'pipeline' ? styles.mainWide : activeTab === 'query' ? styles.mainFull : styles.main}>
        {activeTab === 'query' && <CombinedQueryChatView />}
        {activeTab === 'semantic' && <SemanticSearchView />}
        {activeTab === 'pipeline' && (useEnhanced ? <EnhancedDashboardView /> : <DashboardView />)}
        {activeTab === 'dashboard' && <DashboardView />}
        {activeTab === 'auradb' && <Neo4jDashboard />}
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
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    flexShrink: 0
  },
  toggleLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '8px 12px',
    borderRadius: 10,
    background: 'rgba(255, 255, 255, 0.15)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 500,
    color: 'white',
    backdropFilter: 'blur(10px)',
    transition: 'all 0.2s ease',
    userSelect: 'none' as const
  },
  toggleInput: {
    position: 'absolute',
    opacity: 0,
    width: 0,
    height: 0
  },
  toggleSwitch: {
    position: 'relative',
    width: 40,
    height: 22,
    background: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 11,
    transition: 'all 0.3s ease',
    cursor: 'pointer',
    display: 'inline-block'
  },
  toggleKnob: {
    position: 'absolute',
    top: 2,
    left: 2,
    width: 18,
    height: 18,
    background: 'white',
    borderRadius: '50%',
    transition: 'transform 0.3s ease',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)'
  },
  toggleText: {
    fontSize: 13,
    fontWeight: 500
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


