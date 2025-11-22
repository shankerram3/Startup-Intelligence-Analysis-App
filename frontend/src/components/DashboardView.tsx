import { useEffect, useState } from 'react';
import {
  fetchPipelineLogs,
  fetchPipelineStatus,
  PipelineStartRequest,
  PipelineStatus,
  startPipeline,
  stopPipeline
} from '../lib/api';

export function DashboardView() {
  // Load saved options from localStorage
  const loadSavedOptions = (): PipelineStartRequest => {
    try {
      const saved = localStorage.getItem('pipeline-options');
      if (saved) {
        const parsed = JSON.parse(saved);
        return {
          scrape_category: parsed.scrape_category || 'startups',
          scrape_max_pages: parsed.scrape_max_pages || 2,
          max_articles: parsed.max_articles || 10,
          skip_scraping: parsed.skip_scraping || false,
          skip_extraction: parsed.skip_extraction || false,
          skip_graph: parsed.skip_graph || false,
          no_resume: parsed.no_resume || false
        };
      }
    } catch (e) {
      console.error('Failed to load saved options:', e);
    }
    return {
      scrape_category: 'startups',
      scrape_max_pages: 2,
      max_articles: 10,
      skip_scraping: false,
      skip_extraction: false,
      skip_graph: false,
      no_resume: false
    };
  };

  const [opts, setOpts] = useState<PipelineStartRequest>(loadSavedOptions);
  const [status, setStatus] = useState<PipelineStatus>({ running: false });
  const [logs, setLogs] = useState<string>('');
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      const s = await fetchPipelineStatus();
      setStatus(s);
      const l = await fetchPipelineLogs(300);
      setLogs(l);
    } catch (e) {
      // ignore
    }
  }

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, []);

  async function onStart() {
    if (busy || status.running) return;
    setBusy(true);
    try {
      // Add timeout to prevent hanging
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timed out')), 10000)
      );
      await Promise.race([startPipeline(opts), timeoutPromise]);
      await refresh();
    } catch (e: any) {
      alert(e?.message || 'Failed to start pipeline');
    } finally {
      setBusy(false);
    }
  }

  async function onStop() {
    if (busy || !status.running) return;
    setBusy(true);
    try {
      // Add timeout to prevent hanging
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timed out')), 10000)
      );
      await Promise.race([stopPipeline(), timeoutPromise]);
      await refresh();
    } catch (e: any) {
      alert(e?.message || 'Failed to stop pipeline');
    } finally {
      setBusy(false);
    }
  }

  async function onRefresh() {
    // Allow refresh even when busy, but don't set busy state
    try {
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timed out')), 8000)
      );
      await Promise.race([refresh(), timeoutPromise]);
    } catch (e: any) {
      console.error('Refresh failed:', e);
      // Don't show alert for refresh failures, just log
    }
  }

  function update<K extends keyof PipelineStartRequest>(k: K, v: PipelineStartRequest[K]) {
    setOpts((o) => {
      const updated = { ...o, [k]: v };
      // Save to localStorage
      try {
        localStorage.setItem('pipeline-options', JSON.stringify(updated));
      } catch (e) {
        console.error('Failed to save options:', e);
      }
      return updated;
    });
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '420px 1fr', gap: 16 }}>
      <section style={styles.card}>
        <h3 style={{ marginTop: 0 }}>Pipeline Controls</h3>
        <div style={styles.grid2}>
          <label style={styles.label}>Category</label>
          <input value={opts.scrape_category || ''} onChange={(e) => update('scrape_category', e.target.value)} style={styles.input} />

          <label style={styles.label}>Max Pages</label>
          <input type="number" min={1} value={opts.scrape_max_pages || 1} onChange={(e) => update('scrape_max_pages', Number(e.target.value))} style={styles.input} />

          <label style={styles.label}>Max Articles</label>
          <input type="number" min={1} value={opts.max_articles || 10} onChange={(e) => update('max_articles', Number(e.target.value))} style={styles.input} />
        </div>

        <div style={{ display: 'grid', gap: 8, marginTop: 10 }}>
          <label style={styles.checkbox}><input type="checkbox" checked={!!opts.skip_scraping} onChange={(e) => update('skip_scraping', e.target.checked)} /> Skip scraping</label>
          <label style={styles.checkbox}><input type="checkbox" checked={!!opts.skip_extraction} onChange={(e) => update('skip_extraction', e.target.checked)} /> Skip extraction</label>
          <label style={styles.checkbox}><input type="checkbox" checked={!!opts.skip_graph} onChange={(e) => update('skip_graph', e.target.checked)} /> Skip graph</label>
          <label style={styles.checkbox}><input type="checkbox" checked={!!opts.no_resume} onChange={(e) => update('no_resume', e.target.checked)} /> No resume</label>
        </div>

        <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
          <button onClick={onStart} style={styles.primaryButton} disabled={busy || status.running}>Start</button>
          <button onClick={onStop} style={styles.stopButton} disabled={busy || !status.running}>Stop</button>
          <button onClick={onRefresh} style={styles.refreshButton}>🔄</button>
        </div>

        <div style={{ marginTop: 12, fontSize: 14 }}>
          <strong>Status:</strong> {status.running ? 'Running' : 'Idle'}
          {typeof status.returncode !== 'undefined' && status.returncode !== null && (
            <span> · exit {status.returncode}</span>
          )}
          {status.pid && <span> · pid {status.pid}</span>}
        </div>
      </section>

      <section style={{ ...styles.card, ...styles.logsCard }}>
        <h3 style={{ marginTop: 0 }}>Logs (last 300 lines)</h3>
        <pre style={styles.logs}>{logs || '(no logs yet)'}</pre>
      </section>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: 12,
    padding: 16,
    boxShadow: '0 1px 2px rgba(0,0,0,0.03)'
  },
  grid2: {
    display: 'grid',
    gridTemplateColumns: '140px 1fr',
    gap: 8
  },
  label: {
    alignSelf: 'center',
    fontWeight: 600
  },
  input: {
    borderRadius: 8,
    border: '1px solid #cbd5e1',
    padding: 8,
    fontSize: 14,
    background: '#f8fafc'
  },
  checkbox: {
    display: 'flex',
    alignItems: 'center',
    gap: 8
  },
  primaryButton: {
    padding: '8px 12px',
    borderRadius: 8,
    border: '1px solid #16a34a',
    background: '#22c55e',
    color: 'white',
    cursor: 'pointer'
  },
  stopButton: {
    padding: '8px 12px',
    borderRadius: 8,
    border: '1px solid #b91c1c',
    background: '#ef4444',
    color: 'white',
    cursor: 'pointer'
  },
  refreshButton: {
    padding: '8px 12px',
    borderRadius: 8,
    border: '1px solid #0284c7',
    background: '#f0f9ff',
    color: '#0284c7',
    cursor: 'pointer',
    fontSize: 16
  },
  logsCard: {
    height: 'calc(100vh - 300px)',
    maxHeight: 600,
    minHeight: 400,
    display: 'flex',
    flexDirection: 'column'
  },
  logs: {
    background: '#0b1220',
    color: '#e2e8f0',
    padding: 12,
    borderRadius: 8,
    flex: 1,
    overflow: 'auto',
    fontSize: 12,
    lineHeight: 1.4,
    height: '100%',
    maxHeight: '100%'
  }
};


