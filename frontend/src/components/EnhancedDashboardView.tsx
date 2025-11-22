import { useEffect, useState } from 'react';
import {
  fetchPipelineLogs,
  fetchPipelineStatus,
  PipelineStartRequest,
  PipelineStatus,
  startPipeline,
  stopPipeline
} from '../lib/api';

type ConfigSection = 'scraping' | 'enrichment' | 'processing' | 'advanced';

export function EnhancedDashboardView() {
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
          skip_enrichment: parsed.skip_enrichment || false,
          skip_graph: parsed.skip_graph || false,
          skip_post_processing: parsed.skip_post_processing || false,
          max_companies_per_article: parsed.max_companies_per_article,
          no_resume: parsed.no_resume || false,
          no_validation: parsed.no_validation || false,
          no_cleanup: parsed.no_cleanup || false
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
      skip_enrichment: false,
      skip_graph: false,
      skip_post_processing: false,
      max_companies_per_article: undefined,
      no_resume: false,
      no_validation: false,
      no_cleanup: false
    };
  };

  const [activeSection, setActiveSection] = useState<ConfigSection>('scraping');
  const [opts, setOpts] = useState<PipelineStartRequest>(loadSavedOptions);
  const [status, setStatus] = useState<PipelineStatus>({ running: false });
  const [logs, setLogs] = useState<string>('');
  const [busy, setBusy] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [progress, setProgress] = useState<{
    phase: string;
    current: number;
    total: number;
    percentage: number;
  } | null>(null);

  async function refresh() {
    try {
      const s = await fetchPipelineStatus();
      setStatus(s);
      const l = await fetchPipelineLogs(500);
      setLogs(l);
    } catch (e) {
      // ignore
    }
  }

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 2000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (autoScroll) {
      const logPre = document.getElementById('pipeline-logs');
      if (logPre) {
        logPre.scrollTop = logPre.scrollHeight;
      }
    }
  }, [logs, autoScroll]);

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

  // Parse logs for progress indicators
  useEffect(() => {
    if (!logs) {
      setProgress(null);
      return;
    }

    // Extract last 50 lines for better performance
    const logLines = logs.split('\n').slice(-50).join('\n');

    // Parse phase progress patterns
    const phaseMatch = logLines.match(/PHASE\s+(\d+(?:\.\d+)?):\s+(.+?)(?:\n|$)/i);
    
    // Pattern 1: [X/Y] format (most common)
    const bracketMatch = logLines.match(/\[(\d+)\/(\d+)\]/);
    
    // Pattern 2: "Processing X of Y" or "X of Y"
    const processingMatch = logLines.match(/(?:Processing|Calculating|Scoring).*?(\d+)\s+(?:of|/)\s*(\d+)/i);
    
    // Pattern 3: "Relationship Strength" specific
    const relationshipMatch = logLines.match(/Relationship\s+Strength.*?(\d+)\s*\/\s*(\d+)/i);
    
    // Pattern 4: "Ingesting article: X" with count
    const ingestingMatch = logLines.match(/Ingesting\s+article.*?\[(\d+)\/(\d+)\]/);
    
    let current = 0;
    let total = 0;
    let phaseName = 'Processing';

    if (relationshipMatch) {
      current = parseInt(relationshipMatch[1]) || 0;
      total = parseInt(relationshipMatch[2]) || 0;
      phaseName = 'Relationship Strength Calculation';
    } else if (ingestingMatch) {
      current = parseInt(ingestingMatch[1]) || 0;
      total = parseInt(ingestingMatch[2]) || 0;
      phaseName = phaseMatch ? phaseMatch[2] : 'Graph Construction';
    } else if (bracketMatch) {
      current = parseInt(bracketMatch[1]) || 0;
      total = parseInt(bracketMatch[2]) || 0;
      phaseName = phaseMatch ? phaseMatch[2] : 'Processing';
    } else if (processingMatch) {
      current = parseInt(processingMatch[1]) || 0;
      total = parseInt(processingMatch[2]) || 0;
      phaseName = phaseMatch ? phaseMatch[2] : 'Processing';
    } else if (phaseMatch) {
      phaseName = phaseMatch[2];
      // Try to find any progress in the phase
      const phaseLogs = logLines.split(phaseMatch[0])[1] || '';
      const phaseProgress = phaseLogs.match(/\[(\d+)\/(\d+)\]/);
      if (phaseProgress) {
        current = parseInt(phaseProgress[1]) || 0;
        total = parseInt(phaseProgress[2]) || 0;
      }
    }

    // Check if pipeline is complete
    if (logLines.includes('COMPLETE') || logLines.includes('Complete') || 
        logLines.includes('Finished') || logLines.includes('Pipeline complete')) {
      setProgress({
        phase: 'Complete',
        current: 100,
        total: 100,
        percentage: 100
      });
    } else if (total > 0) {
      setProgress({
        phase: phaseName,
        current,
        total,
        percentage: Math.min(100, (current / total) * 100)
      });
    } else if (phaseMatch) {
      setProgress({
        phase: phaseName,
        current: 0,
        total: 0,
        percentage: 0
      });
    } else {
      setProgress(null);
    }
  }, [logs]);

  function loadPreset(preset: 'quick' | 'full' | 'enrichment-test') {
    switch (preset) {
      case 'quick':
        setOpts({
          scrape_category: 'startups',
          scrape_max_pages: 1,
          max_articles: 5,
          skip_scraping: false,
          skip_extraction: false,
          skip_enrichment: true,  // Skip for quick test
          skip_graph: false,
          skip_post_processing: false,
          no_resume: false
        });
        break;
      case 'full':
        setOpts({
          scrape_category: 'startups',
          scrape_max_pages: 5,
          max_articles: 50,
          skip_scraping: false,
          skip_extraction: false,
          skip_enrichment: false,
          skip_graph: false,
          skip_post_processing: false,
          max_companies_per_article: undefined,
          no_resume: false
        });
        break;
      case 'enrichment-test':
        setOpts({
          scrape_category: 'startups',
          scrape_max_pages: 1,
          max_articles: 3,
          skip_scraping: false,
          skip_extraction: false,
          skip_enrichment: false,
          max_companies_per_article: 3,  // Limit for testing
          skip_graph: false,
          skip_post_processing: false,
          no_resume: false
        });
        break;
    }
  }

  return (
    <div style={styles.root}>
      {/* Header with Presets */}
      <section style={styles.headerCard}>
        <div style={styles.headerContent}>
          <div>
            <h2 style={{ margin: 0 }}>Pipeline Control Center</h2>
            <p style={{ margin: '4px 0 0', opacity: 0.7 }}>
              Configure and run the knowledge graph pipeline
            </p>
          </div>
          <div style={styles.presets}>
            <span style={styles.presetsLabel}>Quick Presets:</span>
            <button onClick={() => loadPreset('quick')} style={styles.presetButton}>⚡ Quick Test</button>
            <button onClick={() => loadPreset('enrichment-test')} style={styles.presetButton}>🔍 Enrichment Test</button>
            <button onClick={() => loadPreset('full')} style={styles.presetButton}>🚀 Full Run</button>
          </div>
        </div>
      </section>

      <div style={styles.mainGrid}>
        {/* Left Panel: Configuration */}
        <div style={styles.leftPanel}>
          {/* Status Card */}
          <section style={{...styles.card, ...styles.statusCard}}>
            <div style={styles.statusHeader}>
              <h3 style={{ margin: 0 }}>Pipeline Status</h3>
              <div style={styles.statusIndicator}>
                <div style={{
                  ...styles.statusDot,
                  background: status.running ? '#22c55e' : '#94a3b8'
                }}></div>
                <span style={{ fontWeight: 600 }}>
                  {status.running ? 'Running' : 'Idle'}
                </span>
              </div>
            </div>
            {status.pid && <div style={styles.statusDetail}>PID: {status.pid}</div>}
            {typeof status.returncode !== 'undefined' && status.returncode !== null && (
              <div style={{
                ...styles.statusDetail,
                color: status.returncode === 0 ? '#16a34a' : '#dc2626'
              }}>
                Exit Code: {status.returncode} {status.returncode === 0 ? '✓' : '✗'}
              </div>
            )}
            
            {/* Progress Bar */}
            {progress && status.running && (
              <div style={styles.progressContainer}>
                <div style={styles.progressHeader}>
                  <span style={styles.progressLabel}>{progress.phase}</span>
                  {progress.total > 0 && (
                    <span style={styles.progressText}>
                      {progress.current}/{progress.total} ({Math.round(progress.percentage)}%)
                    </span>
                  )}
                </div>
                <div style={styles.progressBar}>
                  <div 
                    style={{
                      ...styles.progressFill,
                      width: `${progress.percentage}%`
                    }}
                  />
                </div>
              </div>
            )}
          </section>

          {/* Configuration Sections */}
          <section style={styles.card}>
            <div style={styles.sectionTabs}>
              {[
                { key: 'scraping' as ConfigSection, label: '📰 Scraping', icon: '📰' },
                { key: 'enrichment' as ConfigSection, label: '🔍 Enrichment', icon: '🔍' },
                { key: 'processing' as ConfigSection, label: '⚙️ Processing', icon: '⚙️' },
                { key: 'advanced' as ConfigSection, label: '🔧 Advanced', icon: '🔧' }
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setActiveSection(tab.key)}
                  style={{
                    ...styles.sectionTab,
                    ...(activeSection === tab.key ? styles.sectionTabActive : {})
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div style={styles.sectionContent}>
              {activeSection === 'scraping' && (
                <div style={styles.configSection}>
                  <h4 style={{ marginTop: 0 }}>Web Scraping (Phase 0)</h4>

                  <label style={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={!!opts.skip_scraping}
                      onChange={(e) => update('skip_scraping', e.target.checked)}
                    />
                    <span>Skip web scraping (use existing articles)</span>
                  </label>

                  {!opts.skip_scraping && (
                    <>
                      <div style={styles.formGroup}>
                        <label style={styles.label}>TechCrunch Category</label>
                        <select
                          value={opts.scrape_category || 'startups'}
                          onChange={(e) => update('scrape_category', e.target.value)}
                          style={styles.input}
                        >
                          <option value="startups">Startups</option>
                          <option value="ai">AI</option>
                          <option value="apps">Apps</option>
                          <option value="enterprise">Enterprise</option>
                          <option value="fintech">Fintech</option>
                          <option value="venture">Venture</option>
                        </select>
                      </div>

                      <div style={styles.formGroup}>
                        <label style={styles.label}>Maximum Pages to Scrape</label>
                        <input
                          type="number"
                          min={1}
                          max={100}
                          value={opts.scrape_max_pages || 2}
                          onChange={(e) => update('scrape_max_pages', Number(e.target.value))}
                          style={styles.input}
                        />
                        <small style={styles.hint}>Each page contains ~15-20 articles</small>
                      </div>

                      <div style={styles.formGroup}>
                        <label style={styles.label}>Maximum Articles to Process</label>
                        <input
                          type="number"
                          min={1}
                          max={1000}
                          value={opts.max_articles || 10}
                          onChange={(e) => update('max_articles', Number(e.target.value))}
                          style={styles.input}
                        />
                        <small style={styles.hint}>Limit total articles processed</small>
                      </div>
                    </>
                  )}
                </div>
              )}

              {activeSection === 'enrichment' && (
                <div style={styles.configSection}>
                  <h4 style={{ marginTop: 0 }}>🆕 Company Intelligence Enrichment (Phase 1.5)</h4>
                  <p style={styles.description}>
                    Scrape company websites with Playwright to extract detailed company data
                  </p>

                  <label style={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={!!opts.skip_enrichment}
                      onChange={(e) => update('skip_enrichment', e.target.checked)}
                    />
                    <span>Skip company enrichment (faster, less data)</span>
                  </label>

                  {!opts.skip_enrichment && (
                    <div style={styles.formGroup}>
                      <label style={styles.label}>Max Companies per Article</label>
                      <input
                        type="number"
                        min={1}
                        max={50}
                        value={opts.max_companies_per_article || ''}
                        onChange={(e) => update('max_companies_per_article', e.target.value ? Number(e.target.value) : undefined)}
                        style={styles.input}
                        placeholder="Unlimited"
                      />
                      <small style={styles.hint}>
                        Limit companies scraped per article (leave empty for all)
                      </small>
                    </div>
                  )}

                  <div style={styles.infoBox}>
                    <strong>What gets enriched:</strong>
                    <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
                      <li>Founded year, employee count, headquarters</li>
                      <li>Founders, executives, team information</li>
                      <li>Products, technology stack</li>
                      <li>Funding rounds and investment data</li>
                      <li>Website URLs and descriptions</li>
                    </ul>
                  </div>
                </div>
              )}

              {activeSection === 'processing' && (
                <div style={styles.configSection}>
                  <h4 style={{ marginTop: 0 }}>Graph Building & Processing</h4>

                  <label style={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={!!opts.skip_extraction}
                      onChange={(e) => update('skip_extraction', e.target.checked)}
                    />
                    <span>Skip entity extraction (Phase 1)</span>
                  </label>

                  <label style={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={!!opts.skip_graph}
                      onChange={(e) => update('skip_graph', e.target.checked)}
                    />
                    <span>Skip graph construction (Phase 2)</span>
                  </label>

                  <label style={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={!!opts.skip_post_processing}
                      onChange={(e) => update('skip_post_processing', e.target.checked)}
                    />
                    <span>Skip post-processing (Phase 4) ⚠️ NOT RECOMMENDED</span>
                  </label>

                  <div style={styles.warningBox}>
                    <strong>⚠️ Warning:</strong> Skipping post-processing will disable:
                    <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
                      <li>Vector embeddings (no semantic search!)</li>
                      <li>Entity deduplication</li>
                      <li>Community detection</li>
                      <li>Relationship scoring</li>
                    </ul>
                  </div>
                </div>
              )}

              {activeSection === 'advanced' && (
                <div style={styles.configSection}>
                  <h4 style={{ marginTop: 0 }}>Advanced Options</h4>

                  <label style={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={!!opts.no_resume}
                      onChange={(e) => update('no_resume', e.target.checked)}
                    />
                    <span>Don't resume from checkpoint (start fresh)</span>
                  </label>

                  <label style={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={!!opts.no_validation}
                      onChange={(e) => update('no_validation', e.target.checked)}
                    />
                    <span>Skip data validation</span>
                  </label>

                  <label style={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={!!opts.no_cleanup}
                      onChange={(e) => update('no_cleanup', e.target.checked)}
                    />
                    <span>Skip graph cleanup (Phase 3)</span>
                  </label>

                  <div style={styles.infoBox}>
                    <strong>ℹ️ About checkpoints:</strong>
                    <p style={{ margin: '8px 0' }}>
                      Checkpoints allow resuming interrupted pipeline runs.
                      Disable to force a clean start.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Action Buttons */}
          <section style={styles.card}>
            <div style={styles.actions}>
              <button
                onClick={onStart}
                style={styles.startButton}
                disabled={busy || status.running}
              >
                {status.running ? '⏸ Running...' : '▶ Start Pipeline'}
              </button>
              <button
                onClick={onStop}
                style={styles.stopButton}
                disabled={busy || !status.running}
              >
                ⏹ Stop
              </button>
              <button
                onClick={onRefresh}
                style={styles.refreshButton}
              >
                🔄 Refresh
              </button>
            </div>
          </section>
        </div>

        {/* Right Panel: Logs */}
        <section style={styles.logsCard}>
          <div style={styles.logsHeader}>
            <h3 style={{ margin: 0 }}>Pipeline Logs</h3>
            <label style={styles.checkbox}>
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
              />
              <span style={{ fontSize: 14 }}>Auto-scroll</span>
            </label>
          </div>
          <pre id="pipeline-logs" style={styles.logs}>
            {logs || '(Pipeline not started yet. Click "Start Pipeline" to begin.)'}
          </pre>
        </section>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  root: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16
  },
  headerCard: {
    background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
    borderRadius: 12,
    padding: 20,
    color: 'white',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
  },
  headerContent: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 16
  },
  presets: {
    display: 'flex',
    alignItems: 'center',
    gap: 8
  },
  presetsLabel: {
    fontSize: 14,
    opacity: 0.9
  },
  presetButton: {
    padding: '6px 12px',
    borderRadius: 6,
    border: '1px solid rgba(255,255,255,0.3)',
    background: 'rgba(255,255,255,0.2)',
    color: 'white',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 500,
    transition: 'all 0.2s'
  },
  mainGrid: {
    display: 'grid',
    gridTemplateColumns: '480px 1fr',
    gap: 16,
    alignItems: 'start'
  },
  leftPanel: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16
  },
  card: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: 12,
    padding: 16,
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
  },
  statusCard: {
    background: 'linear-gradient(to right, #f8fafc, white)'
  },
  statusHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12
  },
  statusIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: 8
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: '50%',
    boxShadow: '0 0 8px rgba(0,0,0,0.2)'
  },
  statusDetail: {
    fontSize: 14,
    marginTop: 4,
    opacity: 0.8
  },
  sectionTabs: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 4,
    marginBottom: 16
  },
  sectionTab: {
    padding: '8px 4px',
    border: '1px solid #e2e8f0',
    background: '#f8fafc',
    borderRadius: 8,
    cursor: 'pointer',
    fontSize: 12,
    fontWeight: 500,
    transition: 'all 0.2s'
  },
  sectionTabActive: {
    background: '#0ea5e9',
    borderColor: '#0284c7',
    color: 'white'
  },
  sectionContent: {
    minHeight: 320
  },
  configSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6
  },
  label: {
    fontWeight: 600,
    fontSize: 14
  },
  input: {
    borderRadius: 8,
    border: '1px solid #cbd5e1',
    padding: 8,
    fontSize: 14,
    background: '#f8fafc'
  },
  hint: {
    fontSize: 12,
    opacity: 0.7,
    fontStyle: 'italic'
  },
  checkbox: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '6px 0',
    cursor: 'pointer'
  },
  description: {
    fontSize: 14,
    opacity: 0.8,
    margin: '0 0 12px'
  },
  infoBox: {
    background: '#eff6ff',
    border: '1px solid #bfdbfe',
    borderRadius: 8,
    padding: 12,
    fontSize: 13,
    marginTop: 8
  },
  warningBox: {
    background: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: 8,
    padding: 12,
    fontSize: 13,
    marginTop: 8,
    color: '#991b1b'
  },
  actions: {
    display: 'flex',
    gap: 8
  },
  startButton: {
    flex: 1,
    padding: '12px 16px',
    borderRadius: 8,
    border: '1px solid #16a34a',
    background: '#22c55e',
    color: 'white',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: 15,
    transition: 'all 0.2s'
  },
  stopButton: {
    padding: '12px 16px',
    borderRadius: 8,
    border: '1px solid #b91c1c',
    background: '#ef4444',
    color: 'white',
    cursor: 'pointer',
    fontWeight: 600,
    transition: 'all 0.2s'
  },
  refreshButton: {
    padding: '12px 16px',
    borderRadius: 8,
    border: '1px solid #0284c7',
    background: '#f0f9ff',
    color: '#0284c7',
    cursor: 'pointer',
    fontWeight: 600,
    transition: 'all 0.2s'
  },
  logsCard: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: 12,
    padding: 16,
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
    display: 'flex',
    flexDirection: 'column',
    height: 'calc(100vh - 300px)',
    maxHeight: 800,
    minHeight: 400
  },
  logsHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12
  },
  logs: {
    background: '#0b1220',
    color: '#e2e8f0',
    padding: 16,
    borderRadius: 8,
    flex: 1,
    overflow: 'auto',
    fontSize: 12,
    lineHeight: 1.5,
    fontFamily: 'Consolas, Monaco, "Courier New", monospace',
    height: '100%',
    maxHeight: '100%'
  },
  progressContainer: {
    marginTop: 16,
    paddingTop: 16,
    borderTop: '1px solid #e2e8f0'
  },
  progressHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
    fontSize: 13
  },
  progressLabel: {
    fontWeight: 600,
    color: '#0f172a'
  },
  progressText: {
    color: '#64748b',
    fontSize: 12
  },
  progressBar: {
    width: '100%',
    height: 8,
    background: '#e2e8f0',
    borderRadius: 4,
    overflow: 'hidden'
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #0ea5e9, #0284c7)',
    borderRadius: 4,
    transition: 'width 0.3s ease'
  }
};
