import { useState } from 'react';
import { QueryView } from './components/QueryView';
import { SemanticSearchView } from './components/SemanticSearchView';
import { ChatView } from './components/ChatView';
import { DashboardView } from './components/DashboardView';

type TabKey = 'query' | 'semantic' | 'chat' | 'dashboard';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('query');

  return (
    <div style={styles.appRoot}>
      <header style={styles.header}>
        <h1 style={{ margin: 0 }}>GraphRAG Dashboard</h1>
        <p style={{ margin: '4px 0 0', opacity: 0.8 }}>
          Web UI for queries and semantic search
        </p>
      </header>

      <nav style={styles.tabs}>
        <button
          style={{ ...styles.tabButton, ...(activeTab === 'query' ? styles.tabButtonActive : {}) }}
          onClick={() => setActiveTab('query')}
        >
          Query
        </button>
        <button
          style={{ ...styles.tabButton, ...(activeTab === 'semantic' ? styles.tabButtonActive : {}) }}
          onClick={() => setActiveTab('semantic')}
        >
          Semantic Search
        </button>
        <button
          style={{ ...styles.tabButton, ...(activeTab === 'chat' ? styles.tabButtonActive : {}) }}
          onClick={() => setActiveTab('chat')}
        >
          Chat
        </button>
        <button
          style={{ ...styles.tabButton, ...(activeTab === 'dashboard' ? styles.tabButtonActive : {}) }}
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>
      </nav>

      <main style={styles.main}>
        {activeTab === 'query' && <QueryView />}
        {activeTab === 'semantic' && <SemanticSearchView />}
        {activeTab === 'chat' && <ChatView />}
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
    padding: '8px 12px',
    borderRadius: 8,
    borderWidth: '1px',
    borderStyle: 'solid',
    borderColor: '#cbd5e1',
    background: '#f1f5f9',
    cursor: 'pointer'
  },
  tabButtonActive: {
    background: '#0ea5e9',
    borderColor: '#0284c7',
    color: 'white'
  },
  main: {
    padding: 24,
    maxWidth: 1100,
    margin: '0 auto'
  }
};


