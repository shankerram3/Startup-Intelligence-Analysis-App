import { useEffect, useState } from 'react';
import { fetchRecurringThemes, fetchThemeDetails, generateThemeSummary, postJson, RecurringTheme, ThemeDetailsResponse, QueryRequest, QueryResponse } from '../lib/api';

export function ThemeExtractionView() {
  const [themes, setThemes] = useState<RecurringTheme[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTheme, setSelectedTheme] = useState<RecurringTheme | null>(null);
  const [themeDetails, setThemeDetails] = useState<ThemeDetailsResponse | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [llmSummary, setLlmSummary] = useState<string | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [showMoreDetails, setShowMoreDetails] = useState(false);
  const [queryText, setQueryText] = useState('');
  const [queryResult, setQueryResult] = useState<string | null>(null);
  const [loadingQuery, setLoadingQuery] = useState(false);
  const [filters, setFilters] = useState({
    minFrequency: 3,
    limit: 20,
    timeWindowDays: undefined as number | undefined,
    type: 'all' as 'all' | RecurringTheme['type']
  });

  async function loadThemes() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchRecurringThemes(
        filters.minFrequency,
        filters.limit,
        filters.timeWindowDays
      );
      let filteredThemes = response.themes;
      
      if (filters.type !== 'all') {
        filteredThemes = filteredThemes.filter(t => t.type === filters.type);
      }
      
      setThemes(filteredThemes);
    } catch (e: any) {
      setError(e?.message || 'Failed to load themes');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadThemes();
  }, []);

  async function handleThemeClick(theme: RecurringTheme) {
    setSelectedTheme(theme);
    setLoadingDetails(true);
    setLoadingSummary(true);
    setThemeDetails(null);
    setLlmSummary(null);
    setShowMoreDetails(false);
    setQueryText('');
    setQueryResult(null);
    
    try {
      console.log('Fetching theme details:', { theme: theme.theme, type: theme.type });
      const details = await fetchThemeDetails(theme.theme, theme.type);
      console.log('Theme details received:', details);
      
      let finalDetails: any;
      if (details && Object.keys(details).length > 0) {
        finalDetails = details;
      } else {
        // If no details, show the theme info we already have
        finalDetails = {
          theme_name: theme.theme,
          description: theme.description,
          frequency: theme.frequency,
          entities: theme.entities,
          message: 'Additional details not available, but here is the theme information:'
        };
      }
      setThemeDetails(finalDetails);
      
      // Generate LLM summary with combined theme and details data
      try {
        const summaryData = {
          theme_name: theme.theme,
          theme_type: theme.type,
          description: theme.description,
          frequency: theme.frequency,
          strength: theme.strength,
          entities: theme.entities,
          ...finalDetails
        };
        
        const summaryResponse = await generateThemeSummary(summaryData);
        setLlmSummary(summaryResponse.summary);
      } catch (summaryError: any) {
        console.error('Failed to generate LLM summary:', summaryError);
        // Don't fail the whole operation if summary fails
      }
    } catch (e: any) {
      console.error('Failed to load theme details:', e);
      // Show theme info even if details fetch fails
      setThemeDetails({
        theme_name: theme.theme,
        description: theme.description,
        error: e?.message || 'Failed to load additional details'
      });
    } finally {
      setLoadingDetails(false);
      setLoadingSummary(false);
    }
  }

  async function handleQuery() {
    if (!queryText.trim() || !selectedTheme) return;
    
    setLoadingQuery(true);
    setQueryResult(null);
    
    try {
      // Build comprehensive context about the theme for the query
      let themeContext = `You are analyzing a theme from a knowledge graph:\n\nTheme: ${selectedTheme.theme}\nType: ${selectedTheme.type}\nDescription: ${selectedTheme.description}\nFrequency: ${selectedTheme.frequency} occurrences\nStrength Score: ${selectedTheme.strength}`;
      
      // Add theme details if available
      if (themeDetails) {
        if (themeDetails.technology) {
          themeContext += `\n\nTechnology: ${themeDetails.technology}`;
        }
        if (themeDetails.investor) {
          themeContext += `\n\nInvestor: ${themeDetails.investor}`;
        }
        if (themeDetails.entity) {
          themeContext += `\n\nEntity: ${themeDetails.entity}`;
          if (themeDetails.mention_count) {
            themeContext += ` (mentioned ${themeDetails.mention_count} times)`;
          }
        }
        if (themeDetails.companies && themeDetails.companies.length > 0) {
          const companyNames = themeDetails.companies.slice(0, 10).map((c: any) => c.name).join(', ');
          themeContext += `\n\nRelated Companies: ${companyNames}`;
          if (themeDetails.total_companies && themeDetails.total_companies > 10) {
            themeContext += ` and ${themeDetails.total_companies - 10} more`;
          }
        }
        if (themeDetails.partnerships && themeDetails.partnerships.length > 0) {
          const partnerships = themeDetails.partnerships.slice(0, 5).map((p: any) => `${p.from} ↔ ${p.to}`).join('; ');
          themeContext += `\n\nKey Partnerships: ${partnerships}`;
        }
        if (themeDetails.entities && themeDetails.entities.length > 0) {
          themeContext += `\n\nRelated Entities: ${themeDetails.entities.slice(0, 10).join(', ')}`;
        }
      }
      
      // Construct the question with context
      const fullQuestion = `${queryText}\n\n${themeContext}\n\nPlease answer the question based on the knowledge graph data. If the question is not directly related to this theme, you can still answer it using the general knowledge graph context.`;
      
      const queryRequest: QueryRequest = {
        question: fullQuestion,
        use_llm: true,
        return_context: false
      };
      
      const response = await postJson<QueryRequest, QueryResponse>('/query', queryRequest);
      
      // Better handling of empty answers
      if (response.answer && response.answer.trim()) {
        setQueryResult(response.answer);
      } else {
        setQueryResult('I couldn\'t find enough relevant information in the knowledge graph to answer this question. Try asking about specific entities, relationships, or patterns related to this theme.');
      }
    } catch (e: any) {
      console.error('Query error:', e);
      const errorMsg = e?.message || 'Failed to process query';
      // Try to extract detail from error if it's a JSON error
      try {
        const errorJson = JSON.parse(errorMsg);
        setQueryResult(`Error: ${errorJson.detail || errorMsg}`);
      } catch {
        setQueryResult(`Error: ${errorMsg}`);
      }
    } finally {
      setLoadingQuery(false);
    }
  }

  function getThemeTypeColor(type: RecurringTheme['type']): string {
    switch (type) {
      case 'technology_trend':
        return 'rgba(59, 130, 246, 0.2)';
      case 'funding_pattern':
        return 'rgba(16, 185, 129, 0.2)';
      case 'partnership_pattern':
        return 'rgba(139, 92, 246, 0.2)';
      case 'industry_cluster':
        return 'rgba(245, 158, 11, 0.2)';
      default:
        return 'rgba(100, 116, 139, 0.2)';
    }
  }

  function getThemeTypeLabel(type: RecurringTheme['type']): string {
    switch (type) {
      case 'technology_trend':
        return '🔧 Technology';
      case 'funding_pattern':
        return '💰 Funding';
      case 'partnership_pattern':
        return '🤝 Partnership';
      case 'industry_cluster':
        return '🏭 Industry';
      default:
        return type;
    }
  }

  return (
    <div style={{ display: 'grid', gap: 24, minHeight: 0 }}>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .theme-card {
          transition: all 0.2s ease;
          cursor: pointer;
        }
        .theme-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3) !important;
        }
        .theme-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }
      `}</style>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 700, background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Recurring Themes
          </h1>
          <p style={{ margin: '8px 0 0', color: '#94a3b8', fontSize: 14 }}>
            Discover key patterns and trends across your knowledge graph
          </p>
        </div>
        <button
          onClick={loadThemes}
          disabled={loading}
          style={{
            padding: '10px 20px',
            background: loading ? 'rgba(100, 116, 139, 0.2)' : 'rgba(59, 130, 246, 0.2)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            borderRadius: 8,
            color: '#f1f5f9',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: 14,
            fontWeight: 500
          }}
        >
          {loading ? 'Loading...' : '🔄 Refresh'}
        </button>
      </div>

      {/* Filters */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 12,
        padding: 16,
        background: 'rgba(30, 41, 59, 0.5)',
        borderRadius: 12,
        border: '1px solid rgba(59, 130, 246, 0.2)'
      }}>
        <div>
          <label style={{ display: 'block', marginBottom: 6, fontSize: 12, color: '#94a3b8', fontWeight: 500 }}>
            Min Frequency
          </label>
          <input
            type="number"
            min="1"
            max="50"
            value={filters.minFrequency}
            onChange={(e) => setFilters({ ...filters, minFrequency: parseInt(e.target.value) || 1 })}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: 6,
              color: '#f1f5f9',
              fontSize: 14
            }}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: 6, fontSize: 12, color: '#94a3b8', fontWeight: 500 }}>
            Max Results
          </label>
          <input
            type="number"
            min="1"
            max="100"
            value={filters.limit}
            onChange={(e) => setFilters({ ...filters, limit: parseInt(e.target.value) || 20 })}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: 6,
              color: '#f1f5f9',
              fontSize: 14
            }}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: 6, fontSize: 12, color: '#94a3b8', fontWeight: 500 }}>
            Theme Type
          </label>
          <select
            value={filters.type}
            onChange={(e) => setFilters({ ...filters, type: e.target.value as any })}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: 6,
              color: '#f1f5f9',
              fontSize: 14
            }}
          >
            <option value="all">All Types</option>
            <option value="technology_trend">Technology Trends</option>
            <option value="funding_pattern">Funding Patterns</option>
            <option value="partnership_pattern">Partnership Patterns</option>
            <option value="industry_cluster">Industry Clusters</option>
          </select>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <button
            onClick={loadThemes}
            disabled={loading}
            style={{
              width: '100%',
              padding: '10px',
              background: 'rgba(59, 130, 246, 0.3)',
              border: '1px solid rgba(59, 130, 246, 0.5)',
              borderRadius: 6,
              color: '#f1f5f9',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: 14,
              fontWeight: 500
            }}
          >
            Apply Filters
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={{
          padding: 16,
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: 8,
          color: '#fca5a5'
        }}>
          ⚠️ {error}
        </div>
      )}

      {/* Themes Grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 48, color: '#94a3b8' }}>
          <div style={{ fontSize: 24, marginBottom: 12 }}>⏳</div>
          <div>Loading themes...</div>
        </div>
      ) : themes.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 48, color: '#94a3b8' }}>
          <div style={{ fontSize: 24, marginBottom: 12 }}>🔍</div>
          <div>No themes found. Try adjusting the filters.</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
          {themes.map((theme, idx) => (
            <div
              key={idx}
              className="theme-card"
              onClick={() => handleThemeClick(theme)}
              style={{
                padding: 20,
                background: 'rgba(30, 41, 59, 0.6)',
                border: '1px solid rgba(59, 130, 246, 0.2)',
                borderRadius: 12,
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: '#f1f5f9', flex: 1 }}>
                  {theme.theme}
                </h3>
                <span
                  className="theme-badge"
                  style={{
                    background: getThemeTypeColor(theme.type),
                    color: '#f1f5f9',
                    whiteSpace: 'nowrap',
                    marginLeft: 12
                  }}
                >
                  {getThemeTypeLabel(theme.type)}
                </span>
              </div>
              <p style={{ margin: '0 0 12px', fontSize: 13, color: '#cbd5e1', lineHeight: 1.5 }}>
                {theme.description}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12, paddingTop: 12, borderTop: '1px solid rgba(59, 130, 246, 0.1)' }}>
                <div style={{ fontSize: 12, color: '#94a3b8' }}>
                  <strong style={{ color: '#3b82f6' }}>{theme.frequency}</strong> occurrences
                </div>
                <div style={{ fontSize: 12, color: '#94a3b8' }}>
                  Strength: <strong style={{ color: '#10b981' }}>{theme.strength}</strong>
                </div>
              </div>
              {theme.entities && theme.entities.length > 0 && (
                <div style={{ marginTop: 12, fontSize: 12, color: '#64748b' }}>
                  <div style={{ marginBottom: 6, fontWeight: 500 }}>Sample entities:</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {theme.entities.slice(0, 3).map((entity, i) => (
                      <span
                        key={i}
                        style={{
                          padding: '2px 8px',
                          background: 'rgba(59, 130, 246, 0.1)',
                          borderRadius: 4,
                          fontSize: 11
                        }}
                      >
                        {entity}
                      </span>
                    ))}
                    {theme.entities.length > 3 && (
                      <span style={{ fontSize: 11, color: '#64748b' }}>
                        +{theme.entities.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Theme Details Modal */}
      {selectedTheme && (
        <div
          onClick={(e) => {
            if (e.target === e.currentTarget) setSelectedTheme(null);
          }}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 24
          }}
        >
          <div
            style={{
              background: '#1e293b',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: 12,
              padding: 24,
              maxWidth: 600,
              maxHeight: '80vh',
              overflowY: 'auto',
              width: '100%',
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600, color: '#f1f5f9' }}>
                {selectedTheme.theme}
              </h2>
              <button
                onClick={() => setSelectedTheme(null)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  fontSize: 24,
                  padding: 0,
                  width: 32,
                  height: 32,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                ×
              </button>
            </div>
            
            {loadingDetails ? (
              <div style={{ textAlign: 'center', padding: 48, color: '#94a3b8' }}>
                <div style={{ 
                  width: 40, 
                  height: 40, 
                  border: '3px solid rgba(59, 130, 246, 0.2)',
                  borderTop: '3px solid #3b82f6',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                  margin: '0 auto 16px'
                }}></div>
                <div>Loading theme details...</div>
              </div>
            ) : themeDetails ? (
              <div style={{ display: 'grid', gap: 20 }}>
                {/* LLM-Generated Summary Section */}
                {loadingSummary ? (
                  <div style={{
                    padding: 24,
                    background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
                    borderRadius: 12,
                    border: '1px solid rgba(59, 130, 246, 0.2)',
                    minHeight: 200,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <div style={{ 
                      width: 48, 
                      height: 48, 
                      border: '4px solid rgba(59, 130, 246, 0.2)',
                      borderTop: '4px solid #3b82f6',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite',
                      marginBottom: 16
                    }}></div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: '#f1f5f9', marginBottom: 8 }}>
                      🤖 Generating AI Summary
                    </div>
                    <div style={{ fontSize: 13, color: '#94a3b8', fontStyle: 'italic', textAlign: 'center' }}>
                      Analyzing theme patterns and generating insights...
                    </div>
                  </div>
                ) : llmSummary ? (
                  <div style={{
                    padding: 24,
                    background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
                    borderRadius: 12,
                    border: '1px solid rgba(59, 130, 246, 0.2)',
                    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.1)'
                  }}>
                    <div style={{ 
                      fontSize: 16, 
                      fontWeight: 700, 
                      color: '#f1f5f9', 
                      marginBottom: 16, 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: 10,
                      paddingBottom: 12,
                      borderBottom: '1px solid rgba(59, 130, 246, 0.2)'
                    }}>
                      <span style={{ fontSize: 20 }}>🤖</span>
                      <span>AI-Generated Analysis</span>
                    </div>
                    <div style={{ 
                      fontSize: 15, 
                      color: '#e2e8f0', 
                      lineHeight: 1.8, 
                      whiteSpace: 'pre-wrap',
                      letterSpacing: '0.01em'
                    }}>
                      {llmSummary}
                    </div>
                  </div>
                ) : (
                  <div style={{
                    padding: 24,
                    background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
                    borderRadius: 12,
                    border: '1px solid rgba(59, 130, 246, 0.2)'
                  }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: '#f1f5f9', marginBottom: 12 }}>
                      📊 Summary
                    </div>
                    <div style={{ fontSize: 13, color: '#cbd5e1', lineHeight: 1.6 }}>
                      {(() => {
                        if (themeDetails.technology) {
                          return `The technology "${themeDetails.technology}" is adopted by ${themeDetails.total_companies || themeDetails.companies?.length || 0} ${(themeDetails.total_companies || themeDetails.companies?.length || 0) === 1 ? 'entity' : 'entities'}. ${themeDetails.companies && themeDetails.companies.length > 0 ? `Key adopters include ${themeDetails.companies.slice(0, 3).map((c: any) => c.name).join(', ')}${(themeDetails.total_companies || 0) > 3 ? ` and ${(themeDetails.total_companies || 0) - 3} more` : ''}.` : ''}`;
                        } else if (themeDetails.investor) {
                          return `The investor "${themeDetails.investor}" has a portfolio of ${themeDetails.total_companies || themeDetails.companies?.length || 0} ${(themeDetails.total_companies || themeDetails.companies?.length || 0) === 1 ? 'company' : 'companies'}. ${themeDetails.companies && themeDetails.companies.length > 0 ? `Portfolio companies include ${themeDetails.companies.slice(0, 3).map((c: any) => c.name).join(', ')}${(themeDetails.total_companies || 0) > 3 ? ` and ${(themeDetails.total_companies || 0) - 3} more` : ''}.` : ''}`;
                        } else if (themeDetails.entity) {
                          return `"${themeDetails.entity}" is a prominent entity mentioned ${themeDetails.mention_count || selectedTheme?.frequency || 0} times in the knowledge graph. ${themeDetails.description ? themeDetails.description : ''} ${themeDetails.relationships && themeDetails.relationships.length > 0 ? `It has ${themeDetails.relationships.length} direct relationships with other entities.` : ''}`;
                        } else if (themeDetails.partnerships && themeDetails.partnerships.length > 0) {
                          return `This theme represents ${themeDetails.total_partnerships || themeDetails.partnerships.length} partnership ${(themeDetails.total_partnerships || themeDetails.partnerships.length) === 1 ? 'relationship' : 'relationships'} in the knowledge graph. Key partnerships include ${themeDetails.partnerships.slice(0, 3).map((p: any) => `${p.from} ↔ ${p.to}`).join(', ')}${(themeDetails.total_partnerships || 0) > 3 ? ` and ${(themeDetails.total_partnerships || 0) - 3} more` : ''}.`;
                        } else if (themeDetails.keyword) {
                          return `The keyword "${themeDetails.keyword}" appears in descriptions of ${themeDetails.total_companies || 0} ${(themeDetails.total_companies || 0) === 1 ? 'company' : 'companies'}, indicating a common industry focus or characteristic.`;
                        } else if (selectedTheme) {
                          return `${selectedTheme.description}. This theme has a strength score of ${selectedTheme.strength} and appears ${selectedTheme.frequency} times. ${selectedTheme.entities && selectedTheme.entities.length > 0 ? `Key entities: ${selectedTheme.entities.slice(0, 5).join(', ')}${selectedTheme.entities.length > 5 ? ` and ${selectedTheme.entities.length - 5} more` : ''}.` : ''}`;
                        } else {
                          return themeDetails.description || 'Theme details available below.';
                        }
                      })()}
                    </div>
                  </div>
                )}

                {/* Error messages */}
                {themeDetails.error && (
                  <div style={{ padding: 12, background: 'rgba(239, 68, 68, 0.1)', borderRadius: 8, fontSize: 13, color: '#fca5a5' }}>
                    Error: {themeDetails.error}
                  </div>
                )}

                {/* Query Bar */}
                <div style={{
                  padding: 16,
                  background: 'rgba(30, 41, 59, 0.6)',
                  borderRadius: 12,
                  border: '1px solid rgba(59, 130, 246, 0.2)'
                }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#f1f5f9', marginBottom: 12 }}>
                    💬 Ask about this theme
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <input
                      type="text"
                      value={queryText}
                      onChange={(e) => setQueryText(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && !loadingQuery && handleQuery()}
                      placeholder="e.g., What companies are involved? What are the key trends?"
                      style={{
                        flex: 1,
                        padding: '10px 14px',
                        background: 'rgba(15, 23, 42, 0.8)',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        borderRadius: 8,
                        color: '#f1f5f9',
                        fontSize: 14,
                        outline: 'none'
                      }}
                    />
                    <button
                      onClick={handleQuery}
                      disabled={loadingQuery || !queryText.trim()}
                      style={{
                        padding: '10px 20px',
                        background: loadingQuery || !queryText.trim() 
                          ? 'rgba(100, 116, 139, 0.2)' 
                          : 'rgba(59, 130, 246, 0.3)',
                        border: '1px solid rgba(59, 130, 246, 0.5)',
                        borderRadius: 8,
                        color: '#f1f5f9',
                        cursor: loadingQuery || !queryText.trim() ? 'not-allowed' : 'pointer',
                        fontSize: 14,
                        fontWeight: 500,
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {loadingQuery ? '...' : 'Ask'}
                    </button>
                  </div>
                  {loadingQuery ? (
                    <div style={{
                      marginTop: 12,
                      padding: 16,
                      background: 'rgba(15, 23, 42, 0.6)',
                      borderRadius: 8,
                      border: '1px solid rgba(59, 130, 246, 0.1)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12
                    }}>
                      <div style={{ 
                        width: 20, 
                        height: 20, 
                        border: '2px solid rgba(59, 130, 246, 0.2)',
                        borderTop: '2px solid #3b82f6',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite',
                        flexShrink: 0
                      }}></div>
                      <div style={{ fontSize: 13, color: '#94a3b8', fontStyle: 'italic' }}>
                        Processing your query...
                      </div>
                    </div>
                  ) : queryResult && (
                    <div style={{
                      marginTop: 12,
                      padding: 12,
                      background: 'rgba(15, 23, 42, 0.6)',
                      borderRadius: 8,
                      border: '1px solid rgba(59, 130, 246, 0.1)'
                    }}>
                      <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8, fontWeight: 500 }}>
                        Answer:
                      </div>
                      <div style={{ fontSize: 13, color: '#cbd5e1', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                        {queryResult}
                      </div>
                    </div>
                  )}
                </div>

                {/* Collapsible More Details Section */}
                <div>
                  <button
                    onClick={() => setShowMoreDetails(!showMoreDetails)}
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      background: 'rgba(30, 41, 59, 0.6)',
                      border: '1px solid rgba(59, 130, 246, 0.2)',
                      borderRadius: 12,
                      color: '#f1f5f9',
                      cursor: 'pointer',
                      fontSize: 14,
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <span>📋 {showMoreDetails ? 'Hide' : 'Show'} Detailed Information</span>
                    <span style={{ 
                      transform: showMoreDetails ? 'rotate(180deg)' : 'rotate(0deg)',
                      transition: 'transform 0.2s ease',
                      fontSize: 18
                    }}>
                      ▼
                    </span>
                  </button>
                  
                  {showMoreDetails && themeDetails && (
                    <div style={{
                      marginTop: 12,
                      padding: 16,
                      background: 'rgba(15, 23, 42, 0.4)',
                      borderRadius: 12,
                      border: '1px solid rgba(59, 130, 246, 0.1)',
                      display: 'grid',
                      gap: 16
                    }}>
                      {themeDetails.technology && (
                        <div>
                          <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8, fontWeight: 500 }}>
                            TECHNOLOGY
                          </div>
                          <div style={{ fontSize: 15, color: '#f1f5f9' }}>{themeDetails.technology}</div>
                        </div>
                      )}
                      {themeDetails.investor && (
                        <div>
                          <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8, fontWeight: 500 }}>
                            INVESTOR
                          </div>
                          <div style={{ fontSize: 15, color: '#f1f5f9' }}>{themeDetails.investor}</div>
                        </div>
                      )}
                      {themeDetails.entity && (
                        <div>
                          <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8, fontWeight: 500 }}>
                            ENTITY
                          </div>
                          <div style={{ fontSize: 15, color: '#f1f5f9', marginBottom: 8 }}>{themeDetails.entity}</div>
                          {themeDetails.description && (
                            <div style={{ fontSize: 13, color: '#cbd5e1' }}>{themeDetails.description}</div>
                          )}
                          {themeDetails.mention_count && (
                            <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 8 }}>
                              Mentioned {themeDetails.mention_count} times
                            </div>
                          )}
                        </div>
                      )}
                      {themeDetails.companies && themeDetails.companies.length > 0 && (
                        <div>
                          <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 12, fontWeight: 500 }}>
                            COMPANIES ({themeDetails.total_companies || themeDetails.companies.length})
                          </div>
                          <div style={{ display: 'grid', gap: 10 }}>
                            {themeDetails.companies.map((company, i) => (
                              <div
                                key={i}
                                style={{
                                  padding: 12,
                                  background: 'rgba(30, 41, 59, 0.6)',
                                  borderRadius: 8,
                                  border: '1px solid rgba(59, 130, 246, 0.1)'
                                }}
                              >
                                <div style={{ fontWeight: 600, color: '#f1f5f9', marginBottom: 4 }}>
                                  {company.name}
                                </div>
                                {company.description && (
                                  <div style={{ fontSize: 13, color: '#cbd5e1', marginBottom: 8 }}>
                                    {company.description}
                                  </div>
                                )}
                                {company.investors && company.investors.length > 0 && (
                                  <div style={{ fontSize: 12, color: '#94a3b8' }}>
                                    Investors: {company.investors.join(', ')}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {themeDetails.partnerships && themeDetails.partnerships.length > 0 && (
                        <div>
                          <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 12, fontWeight: 500 }}>
                            PARTNERSHIPS ({themeDetails.total_partnerships || themeDetails.partnerships.length})
                          </div>
                          <div style={{ display: 'grid', gap: 8 }}>
                            {themeDetails.partnerships.map((p: any, i: number) => (
                              <div
                                key={i}
                                style={{
                                  padding: 8,
                                  background: 'rgba(30, 41, 59, 0.6)',
                                  borderRadius: 6,
                                  fontSize: 13,
                                  color: '#cbd5e1'
                                }}
                              >
                                {p.from} ↔ {p.to}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {themeDetails.relationships && themeDetails.relationships.length > 0 && (
                        <div>
                          <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 12, fontWeight: 500 }}>
                            RELATED ENTITIES ({themeDetails.relationships.length})
                          </div>
                          <div style={{ display: 'grid', gap: 8 }}>
                            {themeDetails.relationships.map((rel: any, i: number) => (
                              <div
                                key={i}
                                style={{
                                  padding: 8,
                                  background: 'rgba(30, 41, 59, 0.6)',
                                  borderRadius: 6,
                                  fontSize: 13,
                                  color: '#cbd5e1'
                                }}
                              >
                                {rel.name} ({rel.relationship})
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {themeDetails.entities && themeDetails.entities.length > 0 && (
                        <div>
                          <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 12, fontWeight: 500 }}>
                            RELATED ENTITIES ({themeDetails.entities.length})
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                            {themeDetails.entities.map((entity: string, i: number) => (
                              <span
                                key={i}
                                style={{
                                  padding: '4px 10px',
                                  background: 'rgba(59, 130, 246, 0.2)',
                                  borderRadius: 6,
                                  fontSize: 12
                                }}
                              >
                                {entity}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div style={{ color: '#94a3b8', fontSize: 14 }}>
                No additional details available for this theme.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

