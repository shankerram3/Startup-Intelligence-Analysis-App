import { useState } from 'react';
import { QueryView } from './components/QueryView';
import { EnhancedQueryView } from './components/EnhancedQueryView';
import { SemanticSearchView } from './components/SemanticSearchView';
import { ChatView } from './components/ChatView';
import { DashboardView } from './components/DashboardView';
import { EnhancedDashboardView } from './components/EnhancedDashboardView';

type TabKey = 'query' | 'semantic' | 'chat' | 'dashboard' | 'pipeline';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('query');
  const [useEnhanced, setUseEnhanced] = useState(true);

  return (
    <div style={styles.appRoot}>
      <header style={styles.header}>
        <div style={styles.headerContent}>
          <div>
            <h1 style={{ margin: 0 }}>🚀 GraphRAG Knowledge Graph</h1>
            <p style={{ margin: '4px 0 0', opacity: 0.8 }}>
              TechCrunch Startup Intelligence Analysis with Company Enrichment
            </p>
          </div>
          <label style={styles.toggleLabel}>
            <input
              type="checkbox"
              checked={useEnhanced}
              onChange={(e) => setUseEnhanced(e.target.checked)}
            />
            <span>Enhanced UI</span>
          </label>
        </div>
      </header>

      <nav style={styles.tabs}>
        <button
          style={{ ...styles.tabButton, ...(activeTab === 'query' ? styles.tabButtonActive : {}) }}
          onClick={() => setActiveTab('query')}
        >
          🔍 Query
        </button>
        <button
          style={{ ...styles.tabButton, ...(activeTab === 'semantic' ? styles.tabButtonActive : {}) }}
          onClick={() => setActiveTab('semantic')}
        >
          🎯 Semantic Search
        </button>
        <button
          style={{ ...styles.tabButton, ...(activeTab === 'chat' ? styles.tabButtonActive : {}) }}
          onClick={() => setActiveTab('chat')}
        >
          💬 Chat
        </button>
        <button
          style={{ ...styles.tabButton, ...(activeTab === 'pipeline' ? styles.tabButtonActive : {}) }}
          onClick={() => setActiveTab('pipeline')}
        >
          ⚙️ Pipeline Control
        </button>
        <button
          style={{ ...styles.tabButton, ...(activeTab === 'dashboard' ? styles.tabButtonActive : {}) }}
          onClick={() => setActiveTab('dashboard')}
        >
          📊 Stats
        </button>
      </nav>

      <main style={activeTab === 'pipeline' ? styles.mainWide : styles.main}>
        {activeTab === 'query' && (useEnhanced ? <EnhancedQueryView /> : <QueryView />)}
        {activeTab === 'semantic' && <SemanticSearchView />}
        {activeTab === 'chat' && <ChatView />}
        {activeTab === 'pipeline' && (useEnhanced ? <EnhancedDashboardView /> : <DashboardView />)}
        {activeTab === 'dashboard' && <DashboardView />}
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  appRoot: {
    fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif',
    color: '#0f172a',
    background: '#f8fafc',
    minHeight: '100vh'
  },
  header: {
    padding: '20px 24px',
    background: 'white',
    borderBottom: '1px solid #e2e8f0'
  },
  headerContent: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 16
  },
  toggleLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '8px 12px',
    borderRadius: 8,
    background: '#f1f5f9',
    border: '1px solid #cbd5e1',
    cursor: 'pointer',
    fontSize: 14,
    fontWeight: 500
  },
  tabs: {
    display: 'flex',
    gap: 8,
    padding: '12px 24px',
    background: 'white',
    borderBottom: '1px solid #e2e8f0',
    position: 'sticky',
    top: 0,
    zIndex: 10
  },
  tabButton: {
    padding: '8px 16px',
    borderRadius: 8,
    borderWidth: '1px',
    borderStyle: 'solid',
    borderColor: '#cbd5e1',
    background: '#f1f5f9',
    cursor: 'pointer',
    fontSize: 14,
    fontWeight: 500,
    transition: 'all 0.2s'
  },
  tabButtonActive: {
    background: '#0ea5e9',
    borderColor: '#0284c7',
    color: 'white',
    boxShadow: '0 2px 4px rgba(14, 165, 233, 0.3)'
  },
  main: {
    padding: 24,
    maxWidth: 1100,
    margin: '0 auto'
  },
  mainWide: {
    padding: 24,
    maxWidth: 1400,
    margin: '0 auto'
  }
};


