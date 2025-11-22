export function LandingPage() {
  return (
    <div style={styles.container}>
      {/* Hero Section */}
      <section style={styles.hero}>
        <div style={styles.heroContent}>
          <div style={styles.heroIcon}>🚀</div>
          <h1 style={styles.heroTitle}>Startup Intelligence Analysis</h1>
          <p style={styles.heroSubtitle}>
            A comprehensive knowledge graph and GraphRAG system that extracts entities and relationships 
            from TechCrunch articles, stores them in Neo4j, and provides intelligent querying capabilities.
          </p>
          <div style={styles.heroButtons}>
            <button style={styles.primaryButton} onClick={() => window.location.hash = '#query'}>
              <span>Get Started</span>
              <span>→</span>
            </button>
            <button style={styles.secondaryButton} onClick={() => window.location.hash = '#docs'}>
              <span>📚</span>
              <span>Documentation</span>
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section style={styles.features}>
        <h2 style={styles.sectionTitle}>Powerful Features</h2>
        <div style={styles.featuresGrid}>
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🔍</div>
            <h3 style={styles.featureTitle}>Natural Language Queries</h3>
            <p style={styles.featureDescription}>
              Ask questions in plain English and get intelligent answers powered by GPT-4o and your knowledge graph.
            </p>
          </div>
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🧠</div>
            <h3 style={styles.featureTitle}>Semantic Search</h3>
            <p style={styles.featureDescription}>
              Find entities using vector similarity search with sentence transformers for superior discovery.
            </p>
          </div>
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>📊</div>
            <h3 style={styles.featureTitle}>Knowledge Graph</h3>
            <p style={styles.featureDescription}>
              Build rich knowledge graphs with entities, relationships, and communities stored in Neo4j.
            </p>
          </div>
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>⚡</div>
            <h3 style={styles.featureTitle}>Company Intelligence</h3>
            <p style={styles.featureDescription}>
              Automatically enrich company data with funding, founders, technologies, and more via web scraping.
            </p>
          </div>
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🔗</div>
            <h3 style={styles.featureTitle}>Multi-hop Reasoning</h3>
            <p style={styles.featureDescription}>
              Explore complex relationships and connections across your knowledge graph with graph traversal.
            </p>
          </div>
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🎯</div>
            <h3 style={styles.featureTitle}>Advanced Analytics</h3>
            <p style={styles.featureDescription}>
              Community detection, relationship scoring, and graph analytics powered by Aura Graph Analytics.
            </p>
          </div>
        </div>
      </section>

      {/* Pipeline Section */}
      <section style={styles.pipeline}>
        <h2 style={styles.sectionTitle}>How It Works</h2>
        <div style={styles.pipelineFlow}>
          <div style={styles.pipelineStep}>
            <div style={styles.stepNumber}>1</div>
            <h3 style={styles.stepTitle}>Web Scraping</h3>
            <p style={styles.stepDescription}>Extract articles from TechCrunch</p>
          </div>
          <div style={styles.pipelineArrow}>→</div>
          <div style={styles.pipelineStep}>
            <div style={styles.stepNumber}>2</div>
            <h3 style={styles.stepTitle}>Entity Extraction</h3>
            <p style={styles.stepDescription}>GPT-4o extracts entities and relationships</p>
          </div>
          <div style={styles.pipelineArrow}>→</div>
          <div style={styles.pipelineStep}>
            <div style={styles.stepNumber}>3</div>
            <h3 style={styles.stepTitle}>Enrichment</h3>
            <p style={styles.stepDescription}>Deep company intelligence via web scraping</p>
          </div>
          <div style={styles.pipelineArrow}>→</div>
          <div style={styles.pipelineStep}>
            <div style={styles.stepNumber}>4</div>
            <h3 style={styles.stepTitle}>Graph Building</h3>
            <p style={styles.stepDescription}>Build Neo4j knowledge graph</p>
          </div>
          <div style={styles.pipelineArrow}>→</div>
          <div style={styles.pipelineStep}>
            <div style={styles.stepNumber}>5</div>
            <h3 style={styles.stepTitle}>Query</h3>
            <p style={styles.stepDescription}>Ask questions and get answers</p>
          </div>
        </div>
      </section>

      {/* Quick Start Section */}
      <section style={styles.quickStart}>
        <h2 style={styles.sectionTitle}>Quick Start</h2>
        <div style={styles.quickStartContent}>
          <div style={styles.codeBlock}>
            <div style={styles.codeHeader}>
              <span>Install & Setup</span>
            </div>
            <pre style={styles.code}>
              <code>{`# Install dependencies
pip install -r requirements.txt

# Configure environment
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-key
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
EOF

# Run pipeline
python pipeline.py \\
  --scrape-category startups \\
  --scrape-max-pages 2 \\
  --max-articles 10`}</code>
            </pre>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section style={styles.cta}>
        <h2 style={styles.ctaTitle}>Ready to Get Started?</h2>
        <p style={styles.ctaSubtitle}>
          Start exploring your knowledge graph with natural language queries
        </p>
        <button style={styles.ctaButton} onClick={() => window.location.hash = '#query'}>
          Start Querying
        </button>
      </section>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
    maxWidth: 1200,
    margin: '0 auto',
    padding: '40px 24px',
    background: '#ffffff'
  },
  hero: {
    textAlign: 'center' as const,
    padding: '80px 24px 60px',
    background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
    borderRadius: 20,
    marginBottom: 60,
    color: 'white'
  },
  heroContent: {
    maxWidth: 800,
    margin: '0 auto'
  },
  heroIcon: {
    fontSize: 64,
    marginBottom: 20,
    filter: 'drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2))'
  },
  heroTitle: {
    fontSize: 48,
    fontWeight: 700,
    margin: '0 0 16px 0',
    lineHeight: 1.2,
    letterSpacing: '-0.02em'
  },
  heroSubtitle: {
    fontSize: 20,
    margin: '0 0 32px 0',
    opacity: 0.95,
    lineHeight: 1.6,
    fontWeight: 400
  },
  heroButtons: {
    display: 'flex',
    gap: 16,
    justifyContent: 'center',
    flexWrap: 'wrap' as const
  },
  primaryButton: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '14px 28px',
    fontSize: 16,
    fontWeight: 600,
    background: 'white',
    color: '#0284c7',
    border: 'none',
    borderRadius: 12,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
  },
  secondaryButton: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '14px 28px',
    fontSize: 16,
    fontWeight: 600,
    background: 'rgba(255, 255, 255, 0.2)',
    color: 'white',
    border: '2px solid rgba(255, 255, 255, 0.3)',
    borderRadius: 12,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    backdropFilter: 'blur(10px)'
  },
  features: {
    marginBottom: 80
  },
  sectionTitle: {
    fontSize: 36,
    fontWeight: 700,
    textAlign: 'center' as const,
    margin: '0 0 40px 0',
    color: '#0f172a',
    letterSpacing: '-0.02em'
  },
  featuresGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: 24,
    marginTop: 40
  },
  featureCard: {
    padding: 32,
    background: '#ffffff',
    borderRadius: 16,
    border: '1px solid #e2e8f0',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
    transition: 'all 0.2s ease',
    cursor: 'default'
  },
  featureIcon: {
    fontSize: 40,
    marginBottom: 16
  },
  featureTitle: {
    fontSize: 20,
    fontWeight: 600,
    margin: '0 0 12px 0',
    color: '#0f172a'
  },
  featureDescription: {
    fontSize: 15,
    lineHeight: 1.6,
    color: '#64748b',
    margin: 0
  },
  pipeline: {
    marginBottom: 80,
    padding: 40,
    background: '#f8fafc',
    borderRadius: 20
  },
  pipelineFlow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
    flexWrap: 'wrap' as const,
    marginTop: 40
  },
  pipelineStep: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    textAlign: 'center' as const,
    minWidth: 140
  },
  stepNumber: {
    width: 48,
    height: 48,
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 20,
    fontWeight: 700,
    marginBottom: 12,
    boxShadow: '0 4px 12px rgba(14, 165, 233, 0.3)'
  },
  stepTitle: {
    fontSize: 16,
    fontWeight: 600,
    margin: '0 0 8px 0',
    color: '#0f172a'
  },
  stepDescription: {
    fontSize: 13,
    color: '#64748b',
    margin: 0
  },
  pipelineArrow: {
    fontSize: 24,
    color: '#94a3b8',
    fontWeight: 300
  },
  quickStart: {
    marginBottom: 80
  },
  quickStartContent: {
    maxWidth: 800,
    margin: '0 auto'
  },
  codeBlock: {
    background: '#1e293b',
    borderRadius: 12,
    overflow: 'hidden',
    boxShadow: '0 4px 16px rgba(0, 0, 0, 0.1)'
  },
  codeHeader: {
    padding: '12px 20px',
    background: '#0f172a',
    color: '#94a3b8',
    fontSize: 13,
    fontWeight: 500,
    borderBottom: '1px solid #334155'
  },
  code: {
    margin: 0,
    padding: 20,
    fontSize: 14,
    lineHeight: 1.6,
    color: '#e2e8f0',
    fontFamily: '"Fira Code", "Monaco", "Consolas", monospace',
    overflowX: 'auto' as const
  },
  cta: {
    textAlign: 'center' as const,
    padding: '60px 24px',
    background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
    borderRadius: 20,
    marginBottom: 40
  },
  ctaTitle: {
    fontSize: 32,
    fontWeight: 700,
    margin: '0 0 12px 0',
    color: '#0f172a'
  },
  ctaSubtitle: {
    fontSize: 18,
    color: '#64748b',
    margin: '0 0 32px 0'
  },
  ctaButton: {
    padding: '16px 40px',
    fontSize: 18,
    fontWeight: 600,
    background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
    color: 'white',
    border: 'none',
    borderRadius: 12,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    boxShadow: '0 4px 12px rgba(14, 165, 233, 0.3)'
  }
};

