import { useEffect, useState, useRef, startTransition } from 'react';
import {
  fetchPipelineLogs,
  fetchPipelineStatus,
  PipelineStartRequest,
  PipelineStatus,
  startPipeline,
  stopPipeline,
  clearPipelineLogs
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
          no_cleanup: parsed.no_cleanup || false,
          enable_debug_logs: parsed.enable_debug_logs || false
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
      no_cleanup: false,
      enable_debug_logs: false
    };
  };

  // Load saved pipeline state from localStorage
  const loadSavedPipelineState = () => {
    try {
      const saved = localStorage.getItem('pipeline-state');
      if (saved) {
        const parsed = JSON.parse(saved);
        return {
          activeSection: parsed.activeSection || 'scraping',
          logs: parsed.logs || '',
          progress: parsed.progress || null,
          lastRunSummary: parsed.lastRunSummary || null,
          autoScroll: parsed.autoScroll !== undefined ? parsed.autoScroll : true,
          runStartTime: parsed.runStartTime ? new Date(parsed.runStartTime) : null,
          currentDuration: parsed.currentDuration || 0
        };
      }
    } catch (e) {
      console.error('Failed to load saved pipeline state:', e);
    }
    return {
      activeSection: 'scraping' as ConfigSection,
      logs: '',
      progress: null,
      lastRunSummary: null,
      autoScroll: true,
      runStartTime: null,
      currentDuration: 0
    };
  };

  const savedState = loadSavedPipelineState();
  const [activeSection, setActiveSection] = useState<ConfigSection>(savedState.activeSection);
  const [opts, setOpts] = useState<PipelineStartRequest>(loadSavedOptions);
  const [status, setStatus] = useState<PipelineStatus>({ running: false });
  const [presetKey, setPresetKey] = useState(0); // Force re-render key
  const [lastPresetLoaded, setLastPresetLoaded] = useState<string | null>(null);
  const [logs, setLogs] = useState<string>(savedState.logs);
  const [busy, setBusy] = useState(false);
  const [autoScroll, setAutoScroll] = useState<boolean>(savedState.autoScroll);
  const [progress, setProgress] = useState<{
    phase: string;
    current: number;
    total: number;
    percentage: number;
    subPhase?: string;
    subCurrent?: number;
    subTotal?: number;
    subPercentage?: number;
    detail?: string;
  } | null>(savedState.progress);
  const [lastRunSummary, setLastRunSummary] = useState<{
    phase: string;
    articlesProcessed?: number;
    companiesExtracted?: number;
    entitiesExtracted?: number;
    relationshipsCreated?: number;
    companiesEnriched?: number;
    nodesTotal?: number;
    relationshipsTotal?: number;
    errors?: number;
  } | null>(savedState.lastRunSummary);

  const [runHistory, setRunHistory] = useState<Array<{
    id: string;
    timestamp: Date;
    duration: number;
    status: 'completed' | 'stopped' | 'failed';
    summary: {
      phase: string;
      articlesProcessed?: number;
      companiesExtracted?: number;
      errors?: number;
    };
    logs: string;
  }>>(() => {
    try {
      // Check if history was manually cleared - if so, never restore it
      const clearedFlag = localStorage.getItem('pipeline-history-cleared');
      if (clearedFlag) {
        // History was manually cleared, don't restore it
        console.log('⏭️ Skipping history restore - was manually cleared');
        return [];
      }
      
      const saved = localStorage.getItem('pipeline-run-history');
      if (saved) {
        const parsed = JSON.parse(saved);
        return parsed.map((r: any) => ({
          ...r,
          timestamp: new Date(r.timestamp)
        }));
      }
    } catch (e) {
      console.error('Failed to load run history:', e);
    }
    return [];
  });
  const previousStatusRunningRef = useRef(false);
  // Restore run start time if pipeline was running when we left
  const currentRunStartTimeRef = useRef<Date | null>(savedState.runStartTime);
  const logsManuallyClearedRef = useRef(false);
  const manuallyStoppedRef = useRef(false);
  const historyManuallyClearedRef = useRef(false);
  const [currentRunDuration, setCurrentRunDuration] = useState(savedState.currentDuration);
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);

  // Save run history to localStorage
  function saveRunHistory(history: typeof runHistory) {
    try {
      localStorage.setItem('pipeline-run-history', JSON.stringify(history));
    } catch (e) {
      console.error('Failed to save run history:', e);
    }
  }

  // Save pipeline state to localStorage
  function savePipelineState() {
    try {
      localStorage.setItem('pipeline-state', JSON.stringify({
        activeSection,
        logs,
        progress,
        lastRunSummary,
        autoScroll,
        runStartTime: currentRunStartTimeRef.current ? currentRunStartTimeRef.current.toISOString() : null,
        currentDuration: currentRunDuration
      }));
    } catch (e) {
      console.error('Failed to save pipeline state:', e);
    }
  }

  async function refresh() {
    try {
      // Fetch status and logs with error handling for each
      let s: PipelineStatus;
      let l: string = '';
      
      try {
        s = await fetchPipelineStatus();
      } catch (err: any) {
        // Handle server errors (503/504) and timeouts gracefully
        const isServerError = err?.isServerError || err?.status === 503 || err?.status === 504;
        const isTimeout = err?.isTimeout;
        const errorText = err?.message || String(err);
        
        if (isServerError || isTimeout || errorText.includes('503') || errorText.includes('504') || 
            errorText.includes('no_healthy_upstream') || errorText.includes('temporarily unavailable')) {
          console.warn('⚠️ Server temporarily unavailable, using cached status');
          // Don't update status if server is down - keep last known status
          return;
        }
        // For other errors, re-throw to be caught by outer handler
        throw err;
      }
      
      try {
        l = await fetchPipelineLogs(500);
      } catch (err: any) {
        // Handle server errors (503/504) and timeouts gracefully for logs
        const isServerError = err?.isServerError || err?.status === 503 || err?.status === 504;
        const isTimeout = err?.isTimeout;
        const errorText = err?.message || String(err);
        
        if (isServerError || isTimeout || errorText.includes('503') || errorText.includes('504') || 
            errorText.includes('no_healthy_upstream') || errorText.includes('temporarily unavailable')) {
          console.warn('⚠️ Server temporarily unavailable, keeping existing logs');
          // Keep existing logs, don't update
          l = logs; // Use current logs state
        } else {
          // For other errors, just use empty logs
          l = '';
        }
      }
      
      const wasRunning = previousStatusRunningRef.current;
      const isRunning = s.running;
      
      // Track when pipeline starts
      if (isRunning && !wasRunning) {
        console.log('🚀 Pipeline started - tracking run');
        // Only set start time if we don't already have one (preserves across tab switches)
        if (!currentRunStartTimeRef.current) {
          currentRunStartTimeRef.current = new Date();
        }
        logsManuallyClearedRef.current = false; // Reset cleared flag when pipeline starts
        manuallyStoppedRef.current = false; // Reset manual stop flag when pipeline starts
        // Save state immediately when pipeline starts
        savePipelineState();
      }
      
      // Detect pipeline completion - check if status changed from running to stopped
      if (wasRunning && !isRunning && currentRunStartTimeRef.current) {
        console.log('✅ Pipeline stopped - saving to history', { 
          returncode: s.returncode, 
          manuallyStopped: manuallyStoppedRef.current 
        });
        // Pipeline just stopped
        const duration = (new Date().getTime() - currentRunStartTimeRef.current.getTime()) / 1000;
        
        // Determine status:
        // 1. If manually stopped, always mark as 'stopped'
        // 2. If returncode is non-zero, mark as 'failed'
        // 3. If returncode is 0 AND logs indicate completion, mark as 'completed'
        // 4. Otherwise mark as 'stopped'
        let runStatus: 'completed' | 'stopped' | 'failed';
        if (manuallyStoppedRef.current) {
          runStatus = 'stopped';
        } else if (s.returncode !== null && s.returncode !== 0) {
          runStatus = 'failed';
        } else {
          // Only mark as completed if returncode is 0 AND logs explicitly show FINAL pipeline completion
          // Look for final completion messages, not intermediate phase completions
          const hasFinalCompletion = l.includes('✅ PIPELINE COMPLETE!') ||
                                     l.includes('PIPELINE COMPLETE!') ||
                                     l.includes('Pipeline complete!') ||
                                     l.includes('✅ POST-PROCESSING COMPLETE') ||
                                     (l.includes('POST-PROCESSING COMPLETE') && !l.includes('PHASE'));
          // Don't rely on generic "COMPLETE" or "Complete" as these appear in intermediate phases
          // Also check that we've reached the final phases
          const hasReachedEnd = l.includes('POST-PROCESSING COMPLETE') || 
                                l.includes('Next steps:') ||
                                l.includes('Open Neo4j Browser:');
          runStatus = (s.returncode === 0 && (hasFinalCompletion || hasReachedEnd)) ? 'completed' : 'stopped';
        }
        
        // Create run summary
        const summary = extractRunSummary(l);
        
        // Store summary for status display
        setLastRunSummary(summary);
        
        // Fetch more logs for history (especially important for DEBUG logging)
        // Always try to fetch logs directly from server, even if initial fetch failed
        // Fetch more lines for failed runs to capture all DEBUG information
        const historyLogLines = runStatus === 'failed' ? 5000 : 2000; // More lines for failed runs
        let historyLogs = l; // Use current logs as fallback
        
        // Always attempt to fetch logs when saving to history, even if initial fetch failed
        // This ensures we get logs even if there were temporary server errors
        try {
          // Fetch more comprehensive logs for history - use longer timeout for large fetches
          const fullLogs = await fetchPipelineLogs(historyLogLines, 30000); // 30 second timeout
          if (fullLogs && fullLogs.length > 0) {
            historyLogs = fullLogs;
            console.log(`✅ Fetched ${fullLogs.length} chars of logs for history`);
          } else if (l && l.length > 0) {
            // If fetch returned empty but we have logs from earlier, use those
            historyLogs = l;
            console.log('⚠️ Fetched logs were empty, using cached logs');
          }
        } catch (err) {
          console.warn('Failed to fetch extended logs for history:', err);
          // If we have logs from the initial fetch, use those
          if (l && l.length > 0) {
            historyLogs = l;
            console.log('Using logs from initial fetch as fallback');
          } else {
            // Last resort: try a smaller fetch with shorter timeout
            try {
              const smallLogs = await fetchPipelineLogs(500, 5000);
              if (smallLogs && smallLogs.length > 0) {
                historyLogs = smallLogs;
                console.log('✅ Got logs from fallback fetch');
              }
            } catch (fallbackErr) {
              console.warn('Fallback log fetch also failed:', fallbackErr);
            }
          }
        }
        
        // Store more logs for failed runs to help with debugging
        const logLimit = runStatus === 'failed' ? 50000 : 10000; // 50k for failed, 10k for others
        // Ensure logs is always a string (even if empty)
        const logsString = (historyLogs || '').toString().trim();
        
        // Log what we're saving for debugging
        console.log(`💾 Saving logs to history: ${logsString.length} chars, status: ${runStatus}`);
        
        const savedLogs = logsString.length > 0 ? logsString.substring(Math.max(0, logsString.length - logLimit)) : '';
        
        const runRecord = {
          id: `run-${Date.now()}`,
          timestamp: currentRunStartTimeRef.current,
          duration,
          status: runStatus,
          summary,
          logs: savedLogs
        };
        
        console.log('📝 Saving run record:', {
          id: runRecord.id,
          status: runRecord.status,
          duration: runRecord.duration,
          logsLength: savedLogs.length,
          summary: runRecord.summary
        });
        
        // Warn if logs are empty but we expected them
        if (savedLogs.length === 0 && runStatus !== 'stopped') {
          console.warn('⚠️ Warning: Saving run to history with empty logs!', {
            runStatus,
            historyLogsLength: historyLogs?.length || 0,
            initialLogsLength: l?.length || 0
          });
        }
        
        // Add to history (keep last 50 runs)
        setRunHistory((prevHistory) => {
          const newHistory = [runRecord, ...prevHistory].slice(0, 50);
          saveRunHistory(newHistory);
          console.log('💾 Saved to history, total runs:', newHistory.length);
          return newHistory;
        });
        
        // Clear current run data
        currentRunStartTimeRef.current = null;
        setCurrentRunDuration(0);
        // Save state after clearing
        savePipelineState();
        // Clear logs and progress after a short delay to show completion message
        setTimeout(() => {
          setLogs('');
          setProgress(null);
        }, 2000);
      }
      
      // Also check if pipeline just finished (has returncode but was running)
      // This handles cases where we might have missed the transition
      if (isRunning && s.returncode !== null && s.returncode !== undefined && currentRunStartTimeRef.current) {
        console.log('⚠️ Pipeline has returncode but still marked as running - treating as stopped');
        // Force a stop detection
        previousStatusRunningRef.current = false;
        // This will trigger the detection on next refresh
      }
      
      setStatus(s);
      
      // Only update logs if pipeline is running OR logs were not manually cleared
      // This prevents refresh from overwriting manually cleared logs when pipeline is stopped
      // If pipeline is running, always show new logs (reset the cleared flag)
      if (isRunning) {
        logsManuallyClearedRef.current = false;
        setLogs(l);
      } else if (!logsManuallyClearedRef.current) {
        // Pipeline not running and logs weren't manually cleared, show logs
        setLogs(l);
        
        // Extract summary from logs if available and pipeline has completed
        if (l && l.length > 0 && s.returncode !== null && s.returncode !== undefined) {
          const summary = extractRunSummary(l);
          // Only update if we have meaningful data
          if (summary.articlesProcessed || summary.nodesTotal || summary.relationshipsTotal || 
              summary.companiesExtracted || summary.companiesEnriched) {
            setLastRunSummary(summary);
          }
        }
      }
      // If logs were manually cleared and pipeline is stopped, don't update logs
      
      previousStatusRunningRef.current = isRunning;
    } catch (e) {
      console.error('Refresh error:', e);
      // ignore
    }
  }

  function extractRunSummary(logs: string): { 
    phase: string; 
    articlesProcessed?: number; 
    companiesExtracted?: number; 
    entitiesExtracted?: number;
    relationshipsCreated?: number;
    companiesEnriched?: number;
    nodesTotal?: number;
    relationshipsTotal?: number;
    errors?: number;
    duration?: number;
  } {
    const summary: { 
      phase: string; 
      articlesProcessed?: number; 
      companiesExtracted?: number;
      entitiesExtracted?: number;
      relationshipsCreated?: number;
      companiesEnriched?: number;
      nodesTotal?: number;
      relationshipsTotal?: number;
      errors?: number;
      duration?: number;
    } = {
      phase: 'Unknown'
    };
    
    // Extract phase (look for final phase or most recent)
    const phaseMatches = [...logs.matchAll(/PHASE\s+(\d+(?:\.\d+)?):\s+(.+?)(?:\n|$)/gi)];
    if (phaseMatches.length > 0) {
      const lastPhase = phaseMatches[phaseMatches.length - 1];
      summary.phase = lastPhase[2].trim();
    }
    
    // Extract articles processed
    const articlesMatch = logs.match(/(\d+)\s+articles?\s+(?:processed|ingested)/i);
    if (articlesMatch) {
      summary.articlesProcessed = parseInt(articlesMatch[1]);
    }
    
    // Extract total nodes
    const nodesMatch = logs.match(/Total\s+Nodes?:\s*(\d+)/i);
    if (nodesMatch) {
      summary.nodesTotal = parseInt(nodesMatch[1]);
    }
    
    // Extract total relationships
    const relsMatch = logs.match(/Total\s+Relationships?:\s*(\d+)/i);
    if (relsMatch) {
      summary.relationshipsTotal = parseInt(relsMatch[1]);
    }
    
    // Extract companies enriched
    const enrichedMatch = logs.match(/(\d+)\s+companies?\s+enriched/i);
    if (enrichedMatch) {
      summary.companiesEnriched = parseInt(enrichedMatch[1]);
    }
    
    // Extract node breakdown
    const companyNodesMatch = logs.match(/Company:\s*(\d+)/i);
    if (companyNodesMatch) {
      summary.companiesExtracted = parseInt(companyNodesMatch[1]);
    }
    
    // Extract entity nodes from breakdown
    const entityNodesMatch = logs.match(/Person:\s*(\d+)/i);
    if (entityNodesMatch) {
      summary.entitiesExtracted = parseInt(entityNodesMatch[1]);
    }
    
    // Extract relationships created
    const relationshipsMatch = logs.match(/FUNDED_BY:\s*(\d+)/i) || logs.match(/FOUNDED_BY:\s*(\d+)/i);
    if (relationshipsMatch) {
      // Sum all relationship types
      const allRels = [...logs.matchAll(/(\w+):\s*(\d+)/g)];
      let totalRels = 0;
      for (const match of allRels) {
        if (match[1] !== 'Company' && match[1] !== 'Person' && match[1] !== 'Investor' && 
            match[1] !== 'Article' && match[1] !== 'Product' && match[1] !== 'Location' &&
            match[1] !== 'Technology' && match[1] !== 'Event' && match[1] !== 'Entity' &&
            match[1] !== 'FundingRound' && !isNaN(parseInt(match[2]))) {
          totalRels += parseInt(match[2]);
        }
      }
      if (totalRels > 0) {
        summary.relationshipsCreated = totalRels;
      }
    }
    
    // Count errors
    const errorCount = (logs.match(/\b(error|failed|exception|traceback|Error)\b/gi) || []).length;
    if (errorCount > 0) {
      summary.errors = errorCount;
    }
    
    // Extract duration if available
    const durationMatch = logs.match(/Duration:\s*(\d+(?:\.\d+)?)\s*(?:seconds?|s)/i);
    if (durationMatch) {
      summary.duration = parseFloat(durationMatch[1]);
    }
    
    return summary;
  }

  useEffect(() => {
    // Initial refresh
    refresh().then(() => {
      // After first refresh, initialize the previous status
      previousStatusRunningRef.current = status.running;
      console.log('🔍 Initial status:', { running: status.running, returncode: status.returncode });
    });
    
    const t = setInterval(() => {
      refresh();
    }, 2000);
    return () => clearInterval(t);
  }, []);

  // Initialize current run start time if pipeline is already running on mount
  useEffect(() => {
    if (status.running && !currentRunStartTimeRef.current) {
      // Pipeline is running but we don't have a start time
      // Check if we have a saved start time from localStorage
      if (savedState.runStartTime) {
        currentRunStartTimeRef.current = savedState.runStartTime;
        // Calculate current duration based on saved start time
        const duration = Math.round((new Date().getTime() - savedState.runStartTime.getTime()) / 1000);
        setCurrentRunDuration(duration);
        console.log('🔄 Restored pipeline run start time from saved state', { duration });
      } else {
        // No saved start time, estimate from now
        const now = new Date();
        currentRunStartTimeRef.current = now;
        setCurrentRunDuration(0);
        previousStatusRunningRef.current = true;
        console.log('🔄 Detected running pipeline on mount - initializing tracking');
      }
    }
    
    // Check if pipeline just completed (has returncode, not running, but we have logs)
    if (!status.running && status.returncode !== null && status.returncode !== undefined && logs) {
      // Pipeline completed but we might have missed tracking it
      // Check if this run is already in history
      const recentLogs = logs.toLowerCase();
      // Only check for final pipeline completion, not intermediate phase completions
      const hasCompletionIndicators = recentLogs.includes('✅ pipeline complete!') ||
                                       recentLogs.includes('pipeline complete!') ||
                                       recentLogs.includes('✅ post-processing complete') ||
                                       recentLogs.includes('next steps:') ||
                                       recentLogs.includes('open neo4j browser:');
      
      if (hasCompletionIndicators && !currentRunStartTimeRef.current && !historyManuallyClearedRef.current) {
        // Check if history was manually cleared (skip auto-restoration if it was)
        const clearedFlag = localStorage.getItem('pipeline-history-cleared');
        if (clearedFlag) {
          // History was manually cleared, don't auto-add runs
          console.log('⏭️ Skipping auto-add to history - was manually cleared');
          return;
        }
        
        // This looks like a recently completed run we missed
        // Try to extract info from logs and create a history entry
        console.log('🔍 Detected recently completed pipeline - attempting to save');
        const summary = extractRunSummary(logs);
        const estimatedStart = new Date(Date.now() - 300000); // Estimate 5 min ago
        const statusValue: 'completed' | 'failed' = status.returncode === 0 ? 'completed' : 'failed';
        // Store more logs for failed runs
        const logLimit = statusValue === 'failed' ? 50000 : 10000;
        // Ensure logs is always a string (even if empty)
        const logsString = (logs || '').toString();
        const runRecord = {
          id: `run-${Date.now()}`,
          timestamp: estimatedStart,
          duration: 300, // Estimated
          status: statusValue,
          summary,
          logs: logsString.length > 0 ? logsString.substring(Math.max(0, logsString.length - logLimit)) : ''
        };
        
        setRunHistory((prevHistory) => {
          // Check if we already have this run (by checking if logs are similar)
          const alreadyExists = prevHistory.some(r => 
            Math.abs(r.timestamp.getTime() - estimatedStart.getTime()) < 60000 // Within 1 minute
          );
          if (!alreadyExists) {
            const newHistory = [runRecord, ...prevHistory].slice(0, 50);
            saveRunHistory(newHistory);
            console.log('💾 Saved missed run to history');
            return newHistory;
          }
          return prevHistory;
        });
      }
    }
  }, [status.running, status.returncode, logs]);

  // Update current run duration every second when running
  useEffect(() => {
    if (status.running && currentRunStartTimeRef.current) {
      const updateDuration = () => {
        if (currentRunStartTimeRef.current) {
          const duration = Math.round((new Date().getTime() - currentRunStartTimeRef.current.getTime()) / 1000);
          setCurrentRunDuration(duration);
        }
      };
      updateDuration(); // Initial update
      const interval = setInterval(updateDuration, 1000);
      return () => clearInterval(interval);
    } else {
      setCurrentRunDuration(0);
    }
  }, [status.running]);

  // Save pipeline state to localStorage whenever it changes
  useEffect(() => {
    // Debounce saves to avoid excessive writes
    const timeoutId = setTimeout(() => {
      savePipelineState();
    }, 200);
    return () => clearTimeout(timeoutId);
  }, [activeSection, logs, progress, lastRunSummary, autoScroll, currentRunDuration]);

  // Listen for changes from other tabs/windows to sync pipeline state
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      // Sync pipeline state from other tabs
      if (e.key === 'pipeline-state' && e.newValue) {
        try {
          const parsed = JSON.parse(e.newValue);
          // Only update if different to avoid unnecessary re-renders
          if (parsed.activeSection && parsed.activeSection !== activeSection) {
            setActiveSection(parsed.activeSection);
          }
          if (parsed.logs !== undefined && parsed.logs !== logs && !status.running) {
            // Only sync logs if pipeline is not running (to avoid conflicts)
            setLogs(parsed.logs);
          }
          if (JSON.stringify(parsed.progress) !== JSON.stringify(progress)) {
            setProgress(parsed.progress);
          }
          if (JSON.stringify(parsed.lastRunSummary) !== JSON.stringify(lastRunSummary)) {
            setLastRunSummary(parsed.lastRunSummary);
          }
          if (parsed.autoScroll !== undefined && parsed.autoScroll !== autoScroll) {
            setAutoScroll(parsed.autoScroll);
          }
          // Sync run start time and duration if pipeline is running
          if (parsed.runStartTime && status.running) {
            const savedStartTime = new Date(parsed.runStartTime);
            if (!currentRunStartTimeRef.current || 
                currentRunStartTimeRef.current.getTime() !== savedStartTime.getTime()) {
              currentRunStartTimeRef.current = savedStartTime;
              const duration = Math.round((new Date().getTime() - savedStartTime.getTime()) / 1000);
              setCurrentRunDuration(duration);
            }
          }
          if (parsed.currentDuration !== undefined && status.running) {
            setCurrentRunDuration(parsed.currentDuration);
          }
        } catch (error) {
          console.error('Failed to sync pipeline state from other tab:', error);
        }
      }
      
      // Sync pipeline options from other tabs
      if (e.key === 'pipeline-options' && e.newValue) {
        try {
          const parsed = JSON.parse(e.newValue);
          setOpts(parsed);
        } catch (error) {
          console.error('Failed to sync pipeline options from other tab:', error);
        }
      }
      
      // Sync run history from other tabs
      if (e.key === 'pipeline-run-history' && e.newValue) {
        try {
          const parsed = JSON.parse(e.newValue);
          const history = parsed.map((r: any) => ({
            ...r,
            timestamp: new Date(r.timestamp)
          }));
          setRunHistory(history);
        } catch (error) {
          console.error('Failed to sync run history from other tab:', error);
        }
      }
    };

    // Listen for storage events (fires when localStorage changes in other tabs)
    window.addEventListener('storage', handleStorageChange);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [activeSection, logs, progress, lastRunSummary, autoScroll, status.running]);

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
      // Clear logs when starting a new pipeline run
      logsManuallyClearedRef.current = false; // Reset cleared flag
      setLogs(''); // Clear local logs state
      
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
    // Mark that pipeline was manually stopped
    manuallyStoppedRef.current = true;
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

  // Debug: Log when opts change
  useEffect(() => {
    console.log('📝 Options updated:', opts);
    console.log('📝 Max articles:', opts.max_articles);
    console.log('📝 Max pages:', opts.scrape_max_pages);
    console.log('📝 Category:', opts.scrape_category);
  }, [opts]);

  // Parse logs for progress indicators
  useEffect(() => {
    if (!logs) {
      setProgress(null);
      return;
    }

    // Extract last 100 lines for better granular progress detection
    const logLines = logs.split('\n').slice(-100).join('\n');
    const allLogLines = logs.split('\n');

    // Parse phase progress patterns
    const phaseMatch = logLines.match(/PHASE\s+(\d+(?:\.\d+)?):\s+(.+?)(?:\n|$)/i);
    
    // Pattern 1: [X/Y] format (most common) - find the LAST occurrence for current progress
    const bracketMatches = [...logLines.matchAll(/\[(\d+)\/(\d+)\]/g)];
    const lastBracketMatch = bracketMatches[bracketMatches.length - 1];
    
    // Pattern 2: "Processing X of Y" or "X of Y"
    const processingMatch = logLines.match(/(?:Processing|Calculating|Scoring).*?(\d+)\s+(?:of|\/)\s*(\d+)/i);
    
    // Pattern 3: "Relationship Strength" specific
    const relationshipMatch = logLines.match(/Relationship\s+Strength.*?(\d+)\s*\/\s*(\d+)/i);
    
    // Pattern 4: "Ingesting article: X" with count - most recent
    const ingestingMatches = [...logLines.matchAll(/Ingesting\s+article.*?\[(\d+)\/(\d+)\]/g)];
    const lastIngestingMatch = ingestingMatches[ingestingMatches.length - 1];
    
    // Pattern 5: Entity extraction progress
    const entityMatch = logLines.match(/(\d+)\s+entity\s+nodes?\s+created/i);
    
    // Pattern 6: Relationship creation progress
    const relMatch = logLines.match(/(\d+)\s+relationships?\s+created/i);
    
    // Pattern 7: Company enrichment progress
    const enrichmentMatch = logLines.match(/Enriched:\s+([^\s]+).*?\(confidence:\s+([\d.]+)\)/i);
    const enrichmentCountMatch = logLines.match(/(\d+)\s+companies?\s+enriched/i);
    
    // Pattern 8: Post-processing sub-steps
    const dedupMatch = logLines.match(/Merged:\s+(\d+).*?merged.*?(\d+).*?failed/i);
    const communityMatch = logLines.match(/(\d+)\s+communities?\s+detected/i);
    const embeddingMatch = logLines.match(/(\d+)\s+embeddings?\s+(?:generated|regenerated)/i);
    
    let current = 0;
    let total = 0;
    let phaseName = 'Processing';
    let subPhase: string | undefined;
    let subCurrent: number | undefined;
    let subTotal: number | undefined;
    let detail: string | undefined;

    // Determine main progress
    if (lastIngestingMatch) {
      current = parseInt(lastIngestingMatch[1]) || 0;
      total = parseInt(lastIngestingMatch[2]) || 0;
      phaseName = phaseMatch ? phaseMatch[2] : 'Graph Construction';
      
      // Get sub-progress from article ingestion details
      const articleLine = allLogLines.filter(l => l.includes(`[${current}/${total}]`)).pop();
      if (articleLine) {
        const entityCount = articleLine.match(/(\d+)\s+entity\s+nodes/i)?.[1];
        const relCount = articleLine.match(/(\d+)\s+relationships?/i)?.[1];
        if (entityCount || relCount) {
          subPhase = 'Current Article';
          detail = entityCount ? `${entityCount} entities` : '';
          if (relCount) detail += detail ? `, ${relCount} relationships` : `${relCount} relationships`;
        }
      }
    } else if (relationshipMatch) {
      current = parseInt(relationshipMatch[1]) || 0;
      total = parseInt(relationshipMatch[2]) || 0;
      phaseName = 'Relationship Strength Calculation';
    } else if (lastBracketMatch) {
      current = parseInt(lastBracketMatch[1]) || 0;
      total = parseInt(lastBracketMatch[2]) || 0;
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

    // Extract sub-progress based on phase
    if (phaseMatch) {
      const phaseNum = phaseMatch[1];
      const phaseText = phaseMatch[2];
      
      if (phaseNum.includes('0')) {
        // Phase 0: Web Scraping
        const pageMatch = logLines.match(/page\s+(\d+)/i);
        if (pageMatch) {
          subPhase = `Page ${pageMatch[1]}`;
        }
      } else if (phaseNum.includes('1') || phaseNum.includes('2')) {
        // Phase 1/2: Extraction/Graph Construction
        if (entityMatch) {
          subPhase = 'Entities Extracted';
          subCurrent = parseInt(entityMatch[1]);
        }
        if (relMatch) {
          subPhase = subPhase ? `${subPhase} / Relationships` : 'Relationships Created';
          subTotal = parseInt(relMatch[1]);
        }
      } else if (phaseNum.includes('2.5') || enrichmentCountMatch) {
        // Phase 2.5: Enrichment
        subPhase = 'Company Enrichment';
        subCurrent = parseInt(enrichmentCountMatch?.[1] || '0');
        if (enrichmentMatch) {
          detail = enrichmentMatch[1];
        }
      } else if (phaseNum.includes('3') || phaseNum.includes('4')) {
        // Phase 3/4: Post-processing
        if (dedupMatch) {
          subPhase = 'Deduplication';
          subCurrent = parseInt(dedupMatch[1]);
          subTotal = parseInt(dedupMatch[1]) + parseInt(dedupMatch[2]);
        } else if (communityMatch) {
          subPhase = 'Community Detection';
          subCurrent = parseInt(communityMatch[1]);
        } else if (embeddingMatch) {
          subPhase = 'Embedding Generation';
          subCurrent = parseInt(embeddingMatch[1]);
        }
      }
    }

    // Check if pipeline is complete - only check for final completion, not intermediate phases
    // Look for final pipeline completion messages
    if (logLines.includes('✅ PIPELINE COMPLETE!') || 
        logLines.includes('PIPELINE COMPLETE!') ||
        logLines.includes('✅ POST-PROCESSING COMPLETE') ||
        (logLines.includes('POST-PROCESSING COMPLETE') && !logLines.includes('PHASE')) ||
        logLines.includes('Next steps:') ||
        logLines.includes('Open Neo4j Browser:')) {
      setProgress({
        phase: 'Complete',
        current: 100,
        total: 100,
        percentage: 100
      });
    } else if (total > 0) {
      const mainPercentage = Math.min(100, (current / total) * 100);
      const subPercentage = (subCurrent !== undefined && subTotal !== undefined && subTotal > 0) 
        ? Math.min(100, (subCurrent / subTotal) * 100) 
        : undefined;
      
      setProgress({
        phase: phaseName,
        current,
        total,
        percentage: mainPercentage,
        subPhase,
        subCurrent,
        subTotal,
        subPercentage,
        detail
      });
    } else if (phaseMatch) {
      setProgress({
        phase: phaseName,
        current: 0,
        total: 0,
        percentage: 0,
        subPhase,
        subCurrent,
        subTotal,
        detail
      });
    } else {
      setProgress(null);
    }
  }, [logs]);

  function loadPreset(preset: 'quick' | 'full' | 'enrichment-test', e?: React.MouseEvent) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    console.log('🔄 Loading preset:', preset);
    
    let newOpts: PipelineStartRequest;
    
    // Get current opts to preserve some settings
    const currentOpts = opts;
    
    switch (preset) {
      case 'quick':
        newOpts = {
          scrape_category: 'startups',
          scrape_max_pages: 1,
          max_articles: 5,
          skip_scraping: false,
          skip_extraction: false,
          skip_enrichment: true,  // Skip for quick test
          skip_graph: false,
          skip_post_processing: false,
          no_resume: false,
          no_validation: currentOpts?.no_validation || false,
          no_cleanup: currentOpts?.no_cleanup || false,
          enable_debug_logs: currentOpts?.enable_debug_logs || false,
          max_companies_per_article: undefined
        };
        break;
      case 'full':
        newOpts = {
          scrape_category: 'startups',
          scrape_max_pages: 5,
          max_articles: 50,
          skip_scraping: false,
          skip_extraction: false,
          skip_enrichment: false,
          skip_graph: false,
          skip_post_processing: false,
          max_companies_per_article: undefined,
          no_resume: false,
          no_validation: currentOpts?.no_validation || false,
          no_cleanup: currentOpts?.no_cleanup || false,
          enable_debug_logs: currentOpts?.enable_debug_logs || false
        };
        break;
      case 'enrichment-test':
        newOpts = {
          scrape_category: 'startups',
          scrape_max_pages: 1,
          max_articles: 3,
          skip_scraping: false,
          skip_extraction: false,
          skip_enrichment: false,
          max_companies_per_article: 3,  // Limit for testing
          skip_graph: false,
          skip_post_processing: false,
          no_resume: false,
          no_validation: currentOpts?.no_validation || false,
          no_cleanup: currentOpts?.no_cleanup || false,
          enable_debug_logs: currentOpts?.enable_debug_logs || false
        };
        break;
      default:
        return;
    }
    
    console.log('📋 Previous opts:', JSON.stringify(currentOpts, null, 2));
    console.log('📋 New opts:', JSON.stringify(newOpts, null, 2));
    
    // Save to localStorage first
    try {
      localStorage.setItem('pipeline-options', JSON.stringify(newOpts));
      console.log('💾 Saved preset to localStorage');
    } catch (err) {
      console.error('Failed to save preset:', err);
    }
    
    // Update state with a completely new object reference - deep clone to ensure new reference
    const updatedOpts: PipelineStartRequest = JSON.parse(JSON.stringify(newOpts));
    
    console.log('🔄 Setting state...');
    console.log('  Current max_articles:', opts.max_articles);
    console.log('  New max_articles:', updatedOpts.max_articles);
    console.log('  Current scrape_max_pages:', opts.scrape_max_pages);
    console.log('  New scrape_max_pages:', updatedOpts.scrape_max_pages);
    
    // Update state - ensure we create a completely new object reference
    // Use JSON parse/stringify to force a deep clone with new reference
    const finalOpts: PipelineStartRequest = JSON.parse(JSON.stringify(updatedOpts));
    
    console.log('🔄 About to update state:');
    console.log('  Previous max_articles:', opts.max_articles);
    console.log('  New max_articles:', finalOpts.max_articles);
    console.log('  Previous scrape_max_pages:', opts.scrape_max_pages);
    console.log('  New scrape_max_pages:', finalOpts.scrape_max_pages);
    
    // Update all state together
    setOpts(finalOpts);
    setLastPresetLoaded(preset);
    setPresetKey(Date.now());
    
    console.log('✅ Preset loaded:', preset);
    console.log('✅ State updated with max_articles:', finalOpts.max_articles);
    console.log('✅ State updated with scrape_max_pages:', finalOpts.scrape_max_pages);
    
    // Verify the update worked
    setTimeout(() => {
      // This will use the new state value after re-render
      console.log('🔍 Post-update check - State should have:', {
        max_articles: finalOpts.max_articles,
        scrape_max_pages: finalOpts.scrape_max_pages
      });
    }, 100);
  }


  return (
    <div style={styles.root}>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        .pulse-dot {
          animation: pulse 2s infinite;
        }
      `}</style>
      {/* Header with Presets */}
      <section style={styles.headerCard}>
        <div style={styles.headerContent}>
          <div>
            <h2 style={{ margin: 0 }}>Pipeline Control Center</h2>
            <p style={{ margin: '4px 0 0', opacity: 0.7 }}>
              Configure and run the knowledge graph pipeline
              {lastPresetLoaded && (
                <span style={{ marginLeft: 8, fontSize: 12, opacity: 0.9 }}>
                  (Preset: {lastPresetLoaded})
                </span>
              )}
            </p>
          </div>
          <div style={styles.presets}>
            <span style={styles.presetsLabel}>Quick Presets:</span>
            <button 
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('🔘 Quick Test button clicked');
                loadPreset('quick', e);
              }} 
              style={styles.presetButton}
              onMouseDown={(e) => e.stopPropagation()}
            >
              ⚡ Quick Test
            </button>
            <button 
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('🔘 Enrichment Test button clicked');
                loadPreset('enrichment-test', e);
              }} 
              style={styles.presetButton}
              onMouseDown={(e) => e.stopPropagation()}
            >
              🔍 Enrichment Test
            </button>
            <button 
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('🔘 Full Run button clicked');
                loadPreset('full', e);
              }} 
              style={styles.presetButton}
              onMouseDown={(e) => e.stopPropagation()}
            >
              🚀 Full Run
            </button>
          </div>
        </div>
      </section>

      <div style={styles.mainGrid}>
        {/* Left Sidepanel: History */}
        <aside style={styles.historyPanel}>
          <div style={styles.historyHeader}>
            <h3 style={{ margin: 0 }}>📋 Run History</h3>
            {(runHistory.length > 0 || status.running) && (
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  if (confirm('Clear all run history? This cannot be undone.')) {
                    // Mark that history was manually cleared
                    historyManuallyClearedRef.current = true;
                    // Clear state
                    setRunHistory([]);
                    // Clear localStorage
                    try {
                      localStorage.removeItem('pipeline-run-history');
                      // Also set a flag in localStorage to prevent auto-restoration
                      localStorage.setItem('pipeline-history-cleared', Date.now().toString());
                      console.log('🗑️ Run history cleared from localStorage');
                    } catch (err) {
                      console.error('Failed to clear history from localStorage:', err);
                    }
                    // Also save empty array to ensure it's cleared
                    saveRunHistory([]);
                  }
                }}
                onMouseDown={(e) => e.stopPropagation()}
                style={styles.clearHistoryButton}
                title="Clear all run history"
              >
                🗑️ Clear
              </button>
            )}
          </div>
          {runHistory.length === 0 && !status.running ? (
            <div style={styles.emptyHistory}>
              <p>No pipeline runs yet.</p>
              <p style={{ fontSize: 12, opacity: 0.7 }}>Completed runs will appear here.</p>
            </div>
          ) : (
            <div style={styles.historyList}>
              {/* Current Running Pipeline */}
              {status.running && currentRunStartTimeRef.current && (
                <div style={{...styles.historyItem, ...styles.currentRunItem}}>
                  <div style={styles.historyItemHeader}>
                    <div style={styles.historyItemStatus}>
                      <span className="pulse-dot" style={{
                        ...styles.historyStatusDot,
                        background: '#0ea5e9'
                      }}></span>
                      <span style={{ fontWeight: 600 }}>Running...</span>
                    </div>
                    <span style={styles.historyTime}>
                      {currentRunStartTimeRef.current.toLocaleDateString()} {currentRunStartTimeRef.current.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div style={styles.historyItemDetails}>
                    <div style={styles.historyDetailRow}>
                      <strong>Duration:</strong> {currentRunDuration}s
                    </div>
                    {progress && (
                      <>
                        <div style={styles.historyDetailRow}>
                          <strong>Phase:</strong> {progress.phase}
                        </div>
                        {progress.total > 0 && (
                          <div style={styles.historyDetailRow}>
                            <strong>Progress:</strong> {progress.current}/{progress.total} ({Math.round(progress.percentage)}%)
                          </div>
                        )}
                      </>
                    )}
                    <div style={{...styles.historyDetailRow, fontSize: 11, color: '#0ea5e9', fontStyle: 'italic'}}>
                      ⏳ Pipeline is currently running...
                    </div>
                  </div>
                </div>
              )}
              {/* Past Runs */}
              {runHistory.map((run) => (
                <div key={run.id} style={styles.historyItem}>
                  <div style={styles.historyItemHeader}>
                    <div style={styles.historyItemStatus}>
                      <span style={{
                        ...styles.historyStatusDot,
                        background: run.status === 'completed' ? '#22c55e' : 
                                   run.status === 'failed' ? '#dc2626' : '#f59e0b'
                      }}></span>
                      <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                        {run.status}
                      </span>
                    </div>
                    <span style={styles.historyTime}>
                      {run.timestamp.toLocaleDateString()} {run.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div style={styles.historyItemDetails}>
                    <div style={styles.historyDetailRow}>
                      <strong>Phase:</strong> {run.summary.phase}
                    </div>
                    <div style={styles.historyDetailRow}>
                      <strong>Duration:</strong> {Math.round(run.duration)}s
                    </div>
                    {run.summary.articlesProcessed && (
                      <div style={styles.historyDetailRow}>
                        <strong>Articles:</strong> {run.summary.articlesProcessed}
                      </div>
                    )}
                    {run.summary.companiesExtracted && (
                      <div style={styles.historyDetailRow}>
                        <strong>Companies:</strong> {run.summary.companiesExtracted}
                      </div>
                    )}
                    {run.summary.errors && run.summary.errors > 0 && (
                      <div style={{...styles.historyDetailRow, color: '#dc2626'}}>
                        <strong>Errors:</strong> {run.summary.errors}
                      </div>
                    )}
                    {/* Always show logs button for failed runs, or if logs exist, or if we want to allow retry */}
                    {((run.status === 'failed') || (run.logs && run.logs.length > 0) || run.status === 'stopped') && (
                      <div style={{ marginTop: 8 }}>
                        <button
                          onClick={() => setExpandedRunId(expandedRunId === run.id ? null : run.id)}
                          style={{
                            padding: '6px 12px',
                            borderRadius: 6,
                            border: '1px solid rgba(71, 85, 105, 0.5)',
                            background: run.status === 'failed' ? 'rgba(220, 38, 38, 0.2)' : 'rgba(51, 65, 85, 0.4)',
                            color: '#f1f5f9',
                            cursor: 'pointer',
                            fontSize: 12,
                            fontWeight: 500,
                            width: '100%',
                            transition: 'all 0.2s'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = run.status === 'failed' ? 'rgba(220, 38, 38, 0.3)' : 'rgba(51, 65, 85, 0.6)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = run.status === 'failed' ? 'rgba(220, 38, 38, 0.2)' : 'rgba(51, 65, 85, 0.4)';
                          }}
                        >
                          {expandedRunId === run.id ? '▼ Hide Logs' : '▶ View Logs'}
                          {run.status === 'failed' && ' (Important for debugging)'}
                        </button>
                        {expandedRunId === run.id && (
                          <div style={{
                            marginTop: 8,
                            padding: 12,
                            background: '#0f172a',
                            borderRadius: 6,
                            border: '1px solid rgba(51, 65, 85, 0.5)',
                            maxHeight: '400px',
                            overflowY: 'auto',
                            fontFamily: 'monospace',
                            fontSize: 11,
                            lineHeight: 1.5,
                            color: '#e2e8f0',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word'
                          }}>
                            {run.logs && run.logs.length > 0 ? (
                              run.logs
                            ) : (
                              <div style={{ color: '#94a3b8', fontStyle: 'italic' }}>
                                No logs available for this run. This may indicate:
                                <ul style={{ marginTop: 8, paddingLeft: 20, textAlign: 'left' }}>
                                  <li>The pipeline was stopped before logs could be captured</li>
                                  <li>The server was unavailable when saving logs (503/504 error)</li>
                                  <li>Logs were cleared from the server</li>
                                </ul>
                                <div style={{ marginTop: 8, fontSize: 10, opacity: 0.7 }}>
                                  Run ID: {run.id} | Status: {run.status} | Duration: {Math.round(run.duration)}s
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </aside>

        {/* Middle Panel: Configuration */}
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
            
            {/* Show run summary instead of exit code when not running */}
            {!status.running && status.returncode !== null && status.returncode !== undefined && (
              <div style={styles.statusSummary}>
                {status.returncode === 0 ? (
                  lastRunSummary ? (
                    <div style={styles.summaryContent}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                        <span style={{ fontSize: 16, color: '#16a34a' }}>✓</span>
                        <span style={{ fontWeight: 600, color: '#16a34a' }}>Completed Successfully</span>
                      </div>
                      {(lastRunSummary.articlesProcessed || lastRunSummary.nodesTotal || lastRunSummary.relationshipsTotal) && (
                        <div style={styles.summaryStats}>
                          {lastRunSummary.articlesProcessed && (
                            <div style={styles.summaryStat}>
                              <strong>Articles:</strong> {lastRunSummary.articlesProcessed}
                            </div>
                          )}
                          {lastRunSummary.nodesTotal && (
                            <div style={styles.summaryStat}>
                              <strong>Nodes:</strong> {lastRunSummary.nodesTotal.toLocaleString()}
                            </div>
                          )}
                          {lastRunSummary.relationshipsTotal && (
                            <div style={styles.summaryStat}>
                              <strong>Relationships:</strong> {lastRunSummary.relationshipsTotal.toLocaleString()}
                            </div>
                          )}
                          {lastRunSummary.companiesExtracted && (
                            <div style={styles.summaryStat}>
                              <strong>Companies:</strong> {lastRunSummary.companiesExtracted.toLocaleString()}
                            </div>
                          )}
                          {lastRunSummary.companiesEnriched && (
                            <div style={styles.summaryStat}>
                              <strong>Enriched:</strong> {lastRunSummary.companiesEnriched}
                            </div>
                          )}
                          {lastRunSummary.errors && lastRunSummary.errors > 0 && (
                            <div style={{...styles.summaryStat, color: '#dc2626'}}>
                              <strong>Errors:</strong> {lastRunSummary.errors}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{...styles.statusDetail, color: '#16a34a'}}>
                      Exit Code: {status.returncode} ✓
                    </div>
                  )
                ) : (
                  <div style={{...styles.statusDetail, color: '#dc2626'}}>
                    Exit Code: {status.returncode} ✗ Failed
                  </div>
                )}
              </div>
            )}
            
            {/* Show exit code only when running (shouldn't happen, but just in case) */}
            {status.running && status.returncode !== null && status.returncode !== undefined && (
              <div style={styles.statusDetail}>
                Exit Code: {status.returncode}
              </div>
            )}
            
            {/* Progress Bar */}
            {progress && status.running && (
              <div style={styles.progressContainer}>
                <div style={styles.progressHeader}>
                  <span style={styles.progressLabel}>
                    {progress.phase}
                    {progress.detail && (
                      <span style={{ fontSize: 12, opacity: 0.8, marginLeft: 8 }}>
                        ({progress.detail})
                      </span>
                    )}
                  </span>
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
                
                {/* Sub-progress bar */}
                {progress.subPhase && progress.subCurrent !== undefined && progress.subTotal !== undefined && progress.subTotal > 0 && (
                  <>
                    <div style={{ ...styles.progressHeader, marginTop: 8, fontSize: 12 }}>
                      <span style={{ ...styles.progressLabel, fontSize: 12 }}>
                        {progress.subPhase}
                      </span>
                      <span style={{ ...styles.progressText, fontSize: 11 }}>
                        {progress.subCurrent}/{progress.subTotal} ({Math.round(progress.subPercentage || 0)}%)
                      </span>
                    </div>
                    <div style={{ ...styles.progressBar, height: 6, marginTop: 4 }}>
                      <div 
                        style={{
                          ...styles.progressFill,
                          width: `${progress.subPercentage || 0}%`,
                          background: 'linear-gradient(90deg, #10b981, #059669)',
                          height: '100%'
                        }}
                      />
                    </div>
                  </>
                )}
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

            <div style={styles.sectionContent} key={`content-${presetKey}`}>
              {activeSection === 'scraping' && (
                <div style={styles.configSection} key={`scraping-${presetKey}`}>
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
                          key={`category-${presetKey}`}
                          value={opts.scrape_category ?? 'startups'}
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
                          key={`pages-${presetKey}`}
                          type="number"
                          min={1}
                          max={100}
                          value={opts.scrape_max_pages !== undefined ? opts.scrape_max_pages : 2}
                          onChange={(e) => update('scrape_max_pages', Number(e.target.value))}
                          style={styles.input}
                        />
                        <small style={styles.hint}>Each page contains ~15-20 articles</small>
                      </div>

                      <div style={styles.formGroup}>
                        <label style={styles.label}>Maximum Articles to Process</label>
                        <input
                          key={`articles-${presetKey}`}
                          type="number"
                          min={1}
                          max={1000}
                          value={opts.max_articles !== undefined ? opts.max_articles : 10}
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
                        key={`companies-${presetKey}`}
                        value={opts.max_companies_per_article ?? ''}
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

                  <label style={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={!!opts.enable_debug_logs}
                      onChange={(e) => update('enable_debug_logs', e.target.checked)}
                    />
                    <span>Enable DEBUG level logging (shows detailed debugging information)</span>
                  </label>

                  <div style={styles.infoBox}>
                    <strong>ℹ️ About checkpoints:</strong>
                    <p style={{ margin: '8px 0' }}>
                      Checkpoints allow resuming interrupted pipeline runs.
                      Disable to force a clean start.
                    </p>
                  </div>

                  {opts.enable_debug_logs && (
                    <div style={styles.warningBox}>
                      <strong>🐛 Debug Logging Enabled:</strong>
                      <p style={{ margin: '8px 0' }}>
                        DEBUG level logs will be shown in the pipeline logs. This includes detailed information about processing steps, which can be helpful for troubleshooting but will produce more verbose output.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>

          {/* Action Buttons */}
          <section style={styles.card}>
            <div style={styles.actions}>
              <button
                onClick={onStart}
                style={{
                  ...styles.startButton,
                  ...((busy || status.running) && styles.buttonDisabled)
                }}
                disabled={busy || status.running}
              >
                {status.running ? '⏸ Running...' : '▶ Start Pipeline'}
              </button>
              <button
                onClick={onStop}
                style={{
                  ...styles.stopButton,
                  ...((busy || !status.running) && styles.buttonDisabled)
                }}
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
            <div style={styles.logsControls}>
              {logs && (
                <button
                  type="button"
                  onClick={async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (confirm('Clear pipeline logs? This will clear logs from the server.')) {
                      try {
                        // Call backend API to clear logs
                        await clearPipelineLogs();
                        // Clear local state
                        logsManuallyClearedRef.current = true;
                        setLogs('');
                        // Force scroll to top after clearing
                        setTimeout(() => {
                          const logPre = document.getElementById('pipeline-logs');
                          if (logPre) {
                            logPre.scrollTop = 0;
                          }
                        }, 0);
                        console.log('✅ Pipeline logs cleared from server');
                      } catch (err: any) {
                        console.error('Failed to clear logs:', err);
                        alert(err?.message || 'Failed to clear pipeline logs');
                      }
                    }
                  }}
                  onMouseDown={(e) => e.stopPropagation()}
                  style={styles.clearLogsButton}
                  title="Clear logs"
                >
                  🗑️ Clear
                </button>
              )}
              <label style={styles.checkbox}>
                <input
                  type="checkbox"
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                />
                <span style={{ fontSize: 14 }}>Auto-scroll</span>
              </label>
            </div>
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
    gap: 16,
    height: '100%',
    overflowY: 'auto',
    overflowX: 'hidden',
    position: 'relative' as const
  },
  headerCard: {
    background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
    borderRadius: 12,
    padding: 20,
    color: '#f1f5f9',
    boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    pointerEvents: 'auto' as const,
    position: 'sticky' as const,
    top: 0,
    zIndex: 100,
    marginBottom: 0,
    flexShrink: 0
  },
  headerContent: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 16,
    pointerEvents: 'auto' as const,
    minHeight: 'fit-content'
  },
  presets: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    pointerEvents: 'auto' as const,
    position: 'relative' as const,
    zIndex: 101,
    flexWrap: 'wrap' as const,
    minWidth: 0
  },
  presetsLabel: {
    fontSize: 14,
    opacity: 0.9
  },
  presetButton: {
    padding: '6px 12px',
    borderRadius: 6,
    border: '1px solid rgba(71, 85, 105, 0.5)',
    background: 'rgba(51, 65, 85, 0.4)',
    color: '#f1f5f9',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 500,
    transition: 'all 0.2s',
    pointerEvents: 'auto' as const,
    position: 'relative' as const,
    zIndex: 1,
    userSelect: 'none' as const,
    whiteSpace: 'nowrap' as const,
    flexShrink: 0
  },
  mainGrid: {
    display: 'grid',
    gridTemplateColumns: '280px 480px 1fr',
    gap: 16,
    alignItems: 'start'
  },
  historyPanel: {
    background: '#1e293b',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    borderRadius: 12,
    padding: 16,
    boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
    height: 'calc(100vh - 200px)',
    maxHeight: 800,
    minHeight: 400,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden'
  },
  historyHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 12,
    borderBottom: '1px solid rgba(51, 65, 85, 0.5)'
  },
  clearHistoryButton: {
    padding: '4px 8px',
    borderRadius: 6,
    border: '1px solid rgba(71, 85, 105, 0.5)',
    background: 'transparent',
    color: '#cbd5e1',
    cursor: 'pointer',
    fontSize: 16,
    lineHeight: 1,
    transition: 'all 0.2s'
  },
  emptyHistory: {
    textAlign: 'center',
    padding: '40px 20px',
    color: '#94a3b8',
    fontSize: 14
  },
  historyList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
    overflowY: 'auto',
    flex: 1,
    paddingRight: 4
  },
  historyItem: {
    background: '#334155',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    borderRadius: 8,
    padding: 12,
    transition: 'all 0.2s',
    cursor: 'pointer',
    color: '#f1f5f9'
  },
  historyItemHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8
  },
  historyItemStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 13
  },
  historyStatusDot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
    display: 'inline-block'
  },
  historyTime: {
    fontSize: 11,
    color: '#94a3b8'
  },
  historyItemDetails: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
    fontSize: 12
  },
  historyDetailRow: {
    display: 'flex',
    gap: 8
  },
  currentRunItem: {
    border: '2px solid #3b82f6',
    background: 'rgba(59, 130, 246, 0.1)',
    boxShadow: '0 0 0 3px rgba(59, 130, 246, 0.2)'
  },
  buttonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
    pointerEvents: 'none' as const
  },
  leftPanel: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16
  },
  card: {
    background: '#1e293b',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    borderRadius: 12,
    padding: 16,
    boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
    color: '#f1f5f9'
  },
  statusCard: {
    background: 'linear-gradient(to right, #1e293b, #334155)'
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
  statusSummary: {
    marginTop: 12,
    padding: 12,
    background: '#334155',
    borderRadius: 8,
    border: '1px solid rgba(51, 65, 85, 0.5)'
  },
  summaryContent: {
    fontSize: 13
  },
  summaryStats: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))',
    gap: 8,
    marginTop: 8,
    paddingTop: 8,
    borderTop: '1px solid rgba(51, 65, 85, 0.5)'
  },
  summaryStat: {
    fontSize: 12,
    color: '#cbd5e1'
  },
  sectionTabs: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 4,
    marginBottom: 16
  },
  sectionTab: {
    padding: '8px 4px',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    background: '#334155',
    borderRadius: 8,
    cursor: 'pointer',
    fontSize: 12,
    fontWeight: 500,
    transition: 'all 0.2s',
    color: '#cbd5e1'
  },
  sectionTabActive: {
    background: '#3b82f6',
    borderColor: '#2563eb',
    color: '#f1f5f9'
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
    fontSize: 14,
    color: '#f1f5f9'
  },
  input: {
    borderRadius: 8,
    border: '1px solid rgba(71, 85, 105, 0.5)',
    padding: 8,
    fontSize: 14,
    background: '#334155',
    color: '#f1f5f9'
  },
  hint: {
    fontSize: 12,
    opacity: 0.7,
    fontStyle: 'italic',
    color: '#94a3b8'
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
    margin: '0 0 12px',
    color: '#cbd5e1'
  },
  infoBox: {
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.3)',
    borderRadius: 8,
    padding: 12,
    fontSize: 13,
    marginTop: 8,
    color: '#cbd5e1'
  },
  warningBox: {
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: 8,
    padding: 12,
    fontSize: 13,
    marginTop: 8,
    color: '#fca5a5'
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
    border: '1px solid #3b82f6',
    background: 'rgba(59, 130, 246, 0.1)',
    color: '#60a5fa',
    cursor: 'pointer',
    fontWeight: 600,
    transition: 'all 0.2s'
  },
  logsCard: {
    background: '#1e293b',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    borderRadius: 12,
    padding: 16,
    boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
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
  logsControls: {
    display: 'flex',
    alignItems: 'center',
    gap: 12
  },
  clearLogsButton: {
    padding: '6px 12px',
    borderRadius: 6,
    border: '1px solid rgba(71, 85, 105, 0.5)',
    background: '#334155',
    color: '#cbd5e1',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 500,
    transition: 'all 0.2s',
    pointerEvents: 'auto' as const,
    position: 'relative' as const,
    zIndex: 10
  },
  logs: {
    background: '#0b1220',
    color: '#e2e8f0',
    padding: 16,
    borderRadius: 8,
    flex: 1,
    overflow: 'auto',
    overflowX: 'auto',
    overflowY: 'auto',
    width: '100%',
    maxWidth: '100%',
    boxSizing: 'border-box',
    fontSize: 12,
    lineHeight: 1.5,
    fontFamily: 'Consolas, Monaco, "Courier New", monospace',
    height: '100%',
    maxHeight: '100%',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word'
  },
  progressContainer: {
    marginTop: 16,
    paddingTop: 16,
    borderTop: '1px solid rgba(51, 65, 85, 0.5)'
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
    color: '#f1f5f9'
  },
  progressText: {
    color: '#94a3b8',
    fontSize: 12
  },
  progressBar: {
    width: '100%',
    height: 8,
    background: '#334155',
    borderRadius: 4,
    overflow: 'hidden'
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #3b82f6, #2563eb)',
    borderRadius: 4,
    transition: 'width 0.3s ease'
  }
};
