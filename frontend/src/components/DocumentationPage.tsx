import React, { useState, useEffect } from 'react';

interface Section {
  id: string;
  title: string;
  icon: string;
}

const DocumentationPage: React.FC = () => {
  const [activeSection, setActiveSection] = useState<string>('overview');
  const [scanlineOffset, setScanlineOffset] = useState(0);

  // Animated scanline effect
  useEffect(() => {
    const interval = setInterval(() => {
      setScanlineOffset((prev) => (prev + 1) % 100);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  const sections: Section[] = [
    { id: 'overview', title: 'OVERVIEW', icon: '◆' },
    { id: 'architecture', title: 'ARCHITECTURE', icon: '▣' },
    { id: 'pipeline', title: 'PIPELINE', icon: '▶' },
    { id: 'graphrag', title: 'GRAPHRAG', icon: '◈' },
    { id: 'entities', title: 'ENTITIES', icon: '◉' },
    { id: 'api', title: 'API', icon: '◐' },
    { id: 'deployment', title: 'DEPLOY', icon: '◇' },
    { id: 'quickstart', title: 'START', icon: '▸' },
  ];

  const scrollToSection = (sectionId: string) => {
    setActiveSection(sectionId);
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  };

  return (
    <div style={styles.container}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=VT323&family=Press+Start+2P&display=swap');
        
        @keyframes flicker {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.95; }
        }
        
        @keyframes glow {
          0%, 100% { text-shadow: 0 0 10px #66d9ef, 0 0 20px #66d9ef, 0 0 30px #66d9ef; }
          50% { text-shadow: 0 0 5px #66d9ef, 0 0 10px #66d9ef, 0 0 15px #66d9ef; }
        }
        
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
        
        @keyframes slideIn {
          from { transform: translateX(-20px); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        
        .retro-button:hover {
          background: linear-gradient(45deg, #c084fc, #66d9ef) !important;
          box-shadow: 0 0 20px #c084fc, 0 0 40px #66d9ef !important;
          transform: scale(1.05) !important;
        }
        
        .retro-card:hover {
          transform: translateY(-5px) !important;
          box-shadow: 0 10px 30px rgba(192, 132, 252, 0.3), 0 0 50px rgba(102, 217, 239, 0.2) !important;
        }
        
        .scanline {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: linear-gradient(
            to bottom,
            transparent 50%,
            rgba(102, 217, 239, 0.02) 51%
          );
          background-size: 100% 4px;
          pointer-events: none;
          z-index: 9999;
          animation: flicker 0.15s infinite;
        }
        
        .crt-effect {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: radial-gradient(ellipse at center, transparent 0%, rgba(0, 0, 0, 0.3) 100%);
          pointer-events: none;
          z-index: 9998;
        }
      `}</style>

      {/* CRT Effects */}
      <div className="scanline" />
      <div className="crt-effect" />

      {/* Sidebar Navigation */}
      <aside style={styles.sidebar}>
        <div style={styles.sidebarHeader}>
          <div style={styles.terminalTop}>
            <span style={styles.terminalDot}></span>
            <span style={styles.terminalDot}></span>
            <span style={styles.terminalDot}></span>
          </div>
          <h2 style={styles.sidebarTitle}>
            <span style={styles.blinkingCursor}>▮</span> SYSTEM.DOCS
          </h2>
          <div style={styles.statusBar}>
            <span style={styles.statusText}>STATUS: ONLINE</span>
          </div>
        </div>
        <nav style={styles.nav}>
          {sections.map((section, idx) => (
            <button
              key={section.id}
              onClick={() => scrollToSection(section.id)}
              className="retro-button"
              style={{
                ...styles.navItem,
                ...(activeSection === section.id ? styles.navItemActive : {}),
                animationDelay: `${idx * 0.1}s`,
              }}
            >
              <span style={styles.navIcon}>{section.icon}</span>
              <span style={styles.navText}>{section.title}</span>
              {activeSection === section.id && <span style={styles.activeIndicator}>◀</span>}
            </button>
          ))}
        </nav>
        <div style={styles.sidebarFooter}>
          <div style={styles.pixelBorder}></div>
          <div style={styles.versionInfo}>v2.0.25</div>
        </div>
      </aside>

      {/* Main Content */}
      <main style={styles.content}>
        {/* Overview Section */}
        <section id="overview" style={styles.section}>
          <div style={styles.glitchContainer}>
            <h1 style={styles.h1} data-text="◢ STARTUP INTELLIGENCE ◣">
              ◢ STARTUP INTELLIGENCE ◣
            </h1>
          </div>
          <div style={styles.subtitleBar}>
            <span style={styles.subtitle}>GRAPHRAG ANALYSIS PLATFORM</span>
          </div>
          
          <div style={styles.terminalBox}>
            <div style={styles.terminalHeader}>
              <span>SYSTEM_INFO.TXT</span>
            </div>
            <p style={styles.terminalText}>
              {'> '}<span style={styles.typingText}>INITIALIZING KNOWLEDGE GRAPH SYSTEM...</span><br/>
              {'> '}GPT-4O ENTITY EXTRACTION: [<span style={{color: '#4ade80'}}>ACTIVE</span>]<br/>
              {'> '}NEO4J AURA DATABASE: [<span style={{color: '#4ade80'}}>CONNECTED</span>]<br/>
              {'> '}HYBRID RAG SEARCH: [<span style={{color: '#4ade80'}}>READY</span>]<br/>
              {'> '}38+ API ENDPOINTS: [<span style={{color: '#4ade80'}}>ONLINE</span>]<br/>
            </p>
          </div>

          <div style={styles.statsGrid}>
            <div className="retro-card" style={styles.statCard}>
              <div style={styles.statIcon}>◈</div>
              <div style={styles.statNumber}>38+</div>
              <div style={styles.statLabel}>API ENDPOINTS</div>
              <div style={styles.statBar}></div>
            </div>
            <div className="retro-card" style={styles.statCard}>
              <div style={styles.statIcon}>◉</div>
              <div style={styles.statNumber}>08</div>
              <div style={styles.statLabel}>ENTITY TYPES</div>
              <div style={styles.statBar}></div>
            </div>
            <div className="retro-card" style={styles.statCard}>
              <div style={styles.statIcon}>◐</div>
              <div style={styles.statNumber}>15+</div>
              <div style={styles.statLabel}>RELATIONSHIPS</div>
              <div style={styles.statBar}></div>
            </div>
            <div className="retro-card" style={styles.statCard}>
              <div style={styles.statIcon}>▶</div>
              <div style={styles.statNumber}>06</div>
              <div style={styles.statLabel}>PIPELINE PHASES</div>
              <div style={styles.statBar}></div>
            </div>
          </div>

          <div style={styles.featureGrid}>
            {[
              { icon: '◆', title: 'GPT-4O EXTRACTION', desc: 'ADVANCED NER WITH LANGCHAIN' },
              { icon: '◈', title: 'NEO4J AURA CLOUD', desc: 'MANAGED GRAPH DATABASE + GDS' },
              { icon: '◉', title: 'HYBRID RAG SEARCH', desc: 'SEMANTIC + KEYWORD MATCHING' },
              { icon: '◐', title: 'MULTI-HOP REASONING', desc: 'COMPLEX GRAPH TRAVERSAL' },
              { icon: '▣', title: 'COMPANY INTEL', desc: 'PLAYWRIGHT DEEP SCRAPING' },
              { icon: '▶', title: '38 REST ENDPOINTS', desc: 'FASTAPI + SWAGGER UI' },
              { icon: '◇', title: 'AUTO PROCESSING', desc: 'EMBEDDINGS + COMMUNITIES' },
              { icon: '▸', title: 'PRODUCTION READY', desc: 'CHECKPOINTS + VALIDATION' },
            ].map((feature, idx) => (
              <div key={idx} className="retro-card" style={styles.featureCard}>
                <div style={styles.featureIcon}>{feature.icon}</div>
                <div style={styles.featureTitle}>{feature.title}</div>
                <div style={styles.featureLine}></div>
                <div style={styles.featureDesc}>{feature.desc}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Architecture Section */}
        <section id="architecture" style={styles.section}>
          <h1 style={styles.h1}>◢ SYSTEM ARCHITECTURE ◣</h1>
          
          <div style={styles.retroBox}>
            <div style={styles.retroBoxHeader}>
              <span>LAYER_DIAGRAM.SYS</span>
            </div>
            <div style={styles.architectureDiagram}>
              {[
                { layer: 'FRONTEND LAYER', components: ['REACT UI', 'CHAT INTERFACE', 'DASHBOARD'], color: '#c084fc' },
                { layer: 'API LAYER', components: ['FASTAPI', 'QUERY ROUTER', 'RAG ENGINE'], color: '#66d9ef' },
                { layer: 'PROCESSING LAYER', components: ['WEB SCRAPER', 'ENTITY EXTRACTOR', 'GRAPH BUILDER'], color: '#facc15' },
                { layer: 'DATA LAYER', components: ['NEO4J AURA', 'VECTOR INDEX', 'FILE STORAGE'], color: '#4ade80' },
              ].map((layer, idx) => (
                <div key={idx} style={styles.architectureLayer}>
                  <div style={{...styles.layerTitle, borderColor: layer.color, color: layer.color}}>
                    {layer.layer}
                  </div>
                  <div style={styles.componentRow}>
                    {layer.components.map((comp, cidx) => (
                      <div key={cidx} className="retro-card" style={{...styles.component, borderColor: layer.color}}>
                        <div style={styles.componentText}>{comp}</div>
                      </div>
                    ))}
                  </div>
                  {idx < 3 && <div style={styles.layerArrow}>▼ ▼ ▼</div>}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Pipeline Section */}
        <section id="pipeline" style={styles.section}>
          <h1 style={styles.h1}>◢ DATA PIPELINE FLOW ◣</h1>
          
          <div style={styles.retroBox}>
            <div style={styles.retroBoxHeader}>
              <span>PIPELINE_EXEC.SYS</span>
            </div>
            <div style={styles.pipelineFlow}>
              {[
                { phase: 'PHASE_0', title: 'WEB SCRAPING', tech: 'CRAWL4AI', color: '#c084fc' },
                { phase: 'PHASE_1', title: 'ENTITY EXTRACTION', tech: 'GPT-4O', color: '#66d9ef' },
                { phase: 'PHASE_1.5', title: 'COMPANY INTEL', tech: 'PLAYWRIGHT', color: '#facc15' },
                { phase: 'PHASE_2', title: 'GRAPH BUILD', tech: 'NEO4J', color: '#4ade80' },
                { phase: 'PHASE_3', title: 'CLEANUP', tech: 'DEDUP', color: '#fb923c' },
                { phase: 'PHASE_4', title: 'POST-PROCESS', tech: 'EMBEDDINGS', color: '#f472b6' },
              ].map((step, idx) => (
                <React.Fragment key={idx}>
                  <div className="retro-card" style={{...styles.pipelineStep, borderColor: step.color}}>
                    <div style={{...styles.pipelinePhase, backgroundColor: step.color}}>{step.phase}</div>
                    <div style={styles.pipelineTitle}>{step.title}</div>
                    <div style={styles.pipelineTech}>[{step.tech}]</div>
                  </div>
                  {idx < 5 && (
                    <div style={styles.pipelineArrowContainer}>
                      <div style={styles.pipelineArrow}>→</div>
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div style={styles.codeBox}>
            <div style={styles.codeHeader}>
              <span>EXECUTE_PIPELINE.SH</span>
            </div>
            <pre style={styles.codeContent}>
{`$ python pipeline.py \\
    --scrape-category startups \\
    --scrape-max-pages 2 \\
    --max-articles 10

[INFO] Initializing pipeline...
[OK] Phase 0: Web Scraping
[OK] Phase 1: Entity Extraction  
[OK] Phase 1.5: Company Intelligence
[OK] Phase 2: Graph Construction
[OK] Phase 3: Graph Cleanup
[OK] Phase 4: Post-Processing
[SUCCESS] Pipeline complete!`}
            </pre>
          </div>
        </section>

        {/* GraphRAG Section */}
        <section id="graphrag" style={styles.section}>
          <h1 style={styles.h1}>◢ GRAPHRAG QUERY SYSTEM ◣</h1>
          
          <div style={styles.retroBox}>
            <div style={styles.retroBoxHeader}>
              <span>QUERY_FLOW.DAT</span>
            </div>
            <div style={styles.queryFlow}>
              {[
                { num: '01', title: 'USER QUERY', desc: 'Natural language input', color: '#c084fc' },
                { num: '02', title: 'QUERY ROUTING', desc: 'Classify & select strategy', color: '#66d9ef' },
                { num: '03', title: 'HYBRID SEARCH', desc: 'Semantic + keyword match', color: '#facc15' },
                { num: '04', title: 'CONTEXT RETRIEVAL', desc: 'Extract entities & relations', color: '#4ade80' },
                { num: '05', title: 'LLM GENERATION', desc: 'Generate natural answer', color: '#fb923c' },
              ].map((step, idx) => (
                <React.Fragment key={idx}>
                  <div style={styles.queryStep}>
                    <div style={{...styles.queryNum, backgroundColor: step.color}}>{step.num}</div>
                    <div style={styles.queryContent}>
                      <div style={styles.queryTitle}>{step.title}</div>
                      <div style={styles.queryDesc}>{step.desc}</div>
                    </div>
                  </div>
                  {idx < 4 && (
                    <div style={styles.queryArrowContainer}>
                      <div style={styles.queryArrow}>▼</div>
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        </section>

        {/* Entities Section */}
        <section id="entities" style={styles.section}>
          <h1 style={styles.h1}>◢ ENTITY & RELATIONSHIP MODEL ◣</h1>
          
          <div style={styles.retroBox}>
            <div style={styles.retroBoxHeader}>
              <span>ENTITY_SCHEMA.DB</span>
            </div>
            <div style={styles.entityGrid}>
              {[
                { type: 'COMPANY', icon: '◆', color: '#c084fc' },
                { type: 'PERSON', icon: '◈', color: '#66d9ef' },
                { type: 'INVESTOR', icon: '◉', color: '#facc15' },
                { type: 'TECHNOLOGY', icon: '◐', color: '#4ade80' },
                { type: 'PRODUCT', icon: '▣', color: '#fb923c' },
                { type: 'FUNDING', icon: '▶', color: '#f472b6' },
                { type: 'LOCATION', icon: '◇', color: '#a78bfa' },
                { type: 'EVENT', icon: '▸', color: '#f87171' },
              ].map((entity, idx) => (
                <div key={idx} className="retro-card" style={{...styles.entityCard, borderColor: entity.color}}>
                  <div style={{...styles.entityIcon, color: entity.color}}>{entity.icon}</div>
                  <div style={styles.entityType}>{entity.type}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={styles.relationshipBox}>
            <div style={styles.relationshipHeader}>RELATIONSHIP_TYPES.DAT</div>
            <div style={styles.relationshipGrid}>
              {[
                'FUNDED_BY', 'FOUNDED_BY', 'WORKS_AT', 'ACQUIRED', 'PARTNERS_WITH',
                'COMPETES_WITH', 'USES_TECHNOLOGY', 'LOCATED_IN', 'ANNOUNCED_AT',
                'INVESTS_IN', 'ADVISES', 'LEADS', 'COLLABORATES_WITH', 'REGULATES',
                'OPPOSES', 'SUPPORTS', 'MENTIONED_IN'
              ].map((rel, idx) => (
                <div key={idx} style={styles.relationshipBadge}>
                  <span style={styles.relationshipText}>{rel}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* API Section */}
        <section id="api" style={styles.section}>
          <h1 style={styles.h1}>◢ API REFERENCE ◣</h1>
          
          <div style={styles.apiGrid}>
            {[
              { method: 'POST', endpoint: '/query', desc: 'Execute GraphRAG query' },
              { method: 'POST', endpoint: '/search/semantic', desc: 'Vector similarity search' },
              { method: 'POST', endpoint: '/search/hybrid', desc: 'Combined search' },
              { method: 'GET', endpoint: '/company/{name}', desc: 'Get company details' },
              { method: 'GET', endpoint: '/investors/top', desc: 'Top investors' },
              { method: 'GET', endpoint: '/health', desc: 'System health check' },
            ].map((api, idx) => (
              <div key={idx} className="retro-card" style={styles.apiCard}>
                <div style={styles.apiMethod}>[{api.method}]</div>
                <div style={styles.apiEndpoint}>{api.endpoint}</div>
                <div style={styles.apiDesc}>{api.desc}</div>
              </div>
            ))}
          </div>

          <div style={styles.linkGrid}>
            <a href="http://localhost:5173" target="_blank" rel="noopener noreferrer" className="retro-card" style={styles.linkCard}>
              <div style={styles.linkIcon}>◆</div>
              <div style={styles.linkTitle}>FRONTEND</div>
              <div style={styles.linkUrl}>:5173</div>
            </a>
            <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="retro-card" style={styles.linkCard}>
              <div style={styles.linkIcon}>◈</div>
              <div style={styles.linkTitle}>API DOCS</div>
              <div style={styles.linkUrl}>:8000/docs</div>
            </a>
            <a href="https://console.neo4j.io/" target="_blank" rel="noopener noreferrer" className="retro-card" style={styles.linkCard}>
              <div style={styles.linkIcon}>◉</div>
              <div style={styles.linkTitle}>NEO4J AURA</div>
              <div style={styles.linkUrl}>console.neo4j.io</div>
            </a>
            <a href="http://localhost:8000/health" target="_blank" rel="noopener noreferrer" className="retro-card" style={styles.linkCard}>
              <div style={styles.linkIcon}>◐</div>
              <div style={styles.linkTitle}>HEALTH</div>
              <div style={styles.linkUrl}>:8000/health</div>
            </a>
          </div>
        </section>

        {/* Deployment Section */}
        <section id="deployment" style={styles.section}>
          <h1 style={styles.h1}>◢ DEPLOYMENT & CONFIG ◣</h1>
          
          <div style={styles.deployGrid}>
            {[
              { icon: '◆', title: 'LOCAL DEV', desc: 'Docker Compose setup' },
              { icon: '◈', title: 'NEO4J AURA', desc: 'Cloud database' },
              { icon: '◉', title: 'REMOTE SERVER', desc: 'VM deployment' },
            ].map((deploy, idx) => (
              <div key={idx} className="retro-card" style={styles.deployCard}>
                <div style={styles.deployIcon}>{deploy.icon}</div>
                <div style={styles.deployTitle}>{deploy.title}</div>
                <div style={styles.deployDesc}>{deploy.desc}</div>
              </div>
            ))}
          </div>

          <div style={styles.codeBox}>
            <div style={styles.codeHeader}>
              <span>CONFIG.ENV</span>
            </div>
            <pre style={styles.codeContent}>
{`OPENAI_API_KEY=sk-your-key
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
API_HOST=0.0.0.0
API_PORT=8000
RAG_EMBEDDING_BACKEND=sentence-transformers
SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5`}
            </pre>
          </div>
        </section>

        {/* Quick Start Section */}
        <section id="quickstart" style={styles.section}>
          <h1 style={styles.h1}>◢ QUICK START GUIDE ◣</h1>
          
          <div style={styles.startGrid}>
            {[
              { num: '01', title: 'INSTALL DEPS', cmd: 'pip install -r requirements.txt' },
              { num: '02', title: 'CONFIGURE ENV', cmd: 'cp .env.example .env' },
              { num: '03', title: 'START NEO4J', cmd: 'docker-compose up -d' },
              { num: '04', title: 'RUN PIPELINE', cmd: 'python pipeline.py' },
              { num: '05', title: 'START SERVICES', cmd: './start_all.sh' },
              { num: '06', title: 'ACCESS APP', cmd: 'open http://localhost:5173' },
            ].map((step, idx) => (
              <div key={idx} className="retro-card" style={styles.startCard}>
                <div style={styles.startNum}>{step.num}</div>
                <div style={styles.startTitle}>{step.title}</div>
                <div style={styles.startCmd}>$ {step.cmd}</div>
      </div>
            ))}
          </div>
        </section>

        {/* Footer */}
        <footer style={styles.footer}>
          <div style={styles.footerBorder}></div>
          <div style={styles.footerContent}>
            <div style={styles.footerText}>
              ◢◣ STARTUP INTELLIGENCE ANALYSIS PLATFORM ◢◣
            </div>
            <div style={styles.footerTech}>
              POWERED BY: PYTHON • NEO4J • FASTAPI • REACT • GPT-4O • LANGCHAIN
            </div>
            <div style={styles.footerVersion}>
              SYSTEM VERSION 2.0.25 • BUILD 20251122
        </div>
      </div>
          <div style={styles.footerBorder}></div>
        </footer>
      </main>
    </div>
  );
};

// Retro Styles
const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: 'flex',
    minHeight: '100vh',
    backgroundColor: '#0a0a0a',
    fontFamily: "'VT323', monospace",
    color: '#0ff',
    position: 'relative',
  },
  sidebar: {
    width: '200px',
    backgroundColor: '#000',
    borderRight: '2px solid #66d9ef',
    position: 'sticky' as const,
    top: 0,
    height: '100vh',
    overflowY: 'auto' as const,
    flexShrink: 0,
    boxShadow: '0 0 15px rgba(102, 217, 239, 0.3)',
  },
  sidebarHeader: {
    padding: '12px',
    borderBottom: '2px solid #66d9ef',
    backgroundColor: '#000',
  },
  terminalTop: {
    display: 'flex',
    gap: '8px',
    marginBottom: '15px',
  },
  terminalDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#66d9ef',
    boxShadow: '0 0 6px #66d9ef',
  },
  sidebarTitle: {
    margin: '0 0 8px 0',
    fontSize: '14px',
    fontWeight: 'bold',
    color: '#66d9ef',
    textShadow: '0 0 8px #66d9ef',
    fontFamily: "'Press Start 2P', monospace",
    letterSpacing: '1px',
  },
  blinkingCursor: {
    animation: 'blink 1s infinite',
    color: '#ff00ff',
  },
  statusBar: {
    padding: '5px',
    backgroundColor: '#0a0a0a',
    border: '1px solid #0ff',
    marginTop: '6px',
  },
  statusText: {
    fontSize: '9px',
    color: '#4ade80',
    textShadow: '0 0 4px #4ade80',
  },
  nav: {
    padding: '8px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '4px',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 10px',
    border: '1px solid #66d9ef',
    backgroundColor: '#000',
    color: '#66d9ef',
    fontSize: '12px',
    fontWeight: 'bold',
    cursor: 'pointer',
    transition: 'all 0.3s',
    textAlign: 'left' as const,
    position: 'relative' as const,
    animation: 'slideIn 0.5s ease-out',
  },
  navItemActive: {
    backgroundColor: '#66d9ef',
    color: '#000',
    boxShadow: '0 0 20px #66d9ef',
  },
  navIcon: {
    fontSize: '14px',
    fontWeight: 'bold',
  },
  navText: {
    flex: 1,
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '9px',
  },
  activeIndicator: {
    color: '#c084fc',
    fontSize: '12px',
    animation: 'blink 1s infinite',
  },
  sidebarFooter: {
    padding: '12px',
    borderTop: '2px solid #66d9ef',
    marginTop: 'auto',
  },
  pixelBorder: {
    height: '6px',
    background: 'repeating-linear-gradient(90deg, #0ff 0px, #0ff 3px, transparent 3px, transparent 6px)',
    marginBottom: '6px',
  },
  versionInfo: {
    textAlign: 'center' as const,
    fontSize: '9px',
    color: '#66d9ef',
    fontFamily: "'Press Start 2P', monospace",
  },
  content: {
    flex: 1,
    padding: '20px 30px',
    maxWidth: '1400px',
    margin: '0 auto',
    width: '100%',
    overflowY: 'auto' as const,
  },
  section: {
    marginBottom: '40px',
  },
  glitchContainer: {
    position: 'relative' as const,
    marginBottom: '20px',
  },
  h1: {
    fontSize: '20px',
    fontWeight: 'bold',
    color: '#66d9ef',
    marginBottom: '12px',
    marginTop: 0,
    fontFamily: "'Press Start 2P', monospace",
    textShadow: '0 0 8px #66d9ef, 0 0 15px #66d9ef, 2px 2px 0 #c084fc',
    animation: 'glow 2s infinite',
    letterSpacing: '1px',
  },
  subtitleBar: {
    padding: '8px',
    backgroundColor: '#000',
    border: '2px solid #c084fc',
    marginBottom: '15px',
    textAlign: 'center' as const,
    boxShadow: '0 0 15px rgba(192, 132, 252, 0.3)',
  },
  subtitle: {
    fontSize: '11px',
    color: '#c084fc',
    fontFamily: "'Press Start 2P', monospace",
    textShadow: '0 0 8px #c084fc',
    letterSpacing: '1px',
  },
  terminalBox: {
    backgroundColor: '#000',
    border: '2px solid #66d9ef',
    padding: '12px',
    marginBottom: '15px',
    boxShadow: '0 0 20px rgba(102, 217, 239, 0.2)',
  },
  terminalHeader: {
    color: '#66d9ef',
    fontSize: '11px',
    marginBottom: '8px',
    paddingBottom: '6px',
    borderBottom: '1px solid #66d9ef',
    fontFamily: "'Press Start 2P', monospace",
  },
  terminalText: {
    fontSize: '12px',
    lineHeight: 1.5,
    color: '#66d9ef',
    margin: 0,
  },
  typingText: {
    color: '#facc15',
    textShadow: '0 0 5px #facc15',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
    gap: '10px',
    marginBottom: '20px',
  },
  statCard: {
    backgroundColor: '#000',
    border: '2px solid #c084fc',
    padding: '12px',
    textAlign: 'center' as const,
    transition: 'all 0.3s',
    position: 'relative' as const,
  },
  statIcon: {
    fontSize: '20px',
    color: '#c084fc',
    marginBottom: '6px',
    textShadow: '0 0 8px #c084fc',
  },
  statNumber: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#66d9ef',
    marginBottom: '6px',
    fontFamily: "'Press Start 2P', monospace",
    textShadow: '0 0 10px #66d9ef',
  },
  statLabel: {
    fontSize: '9px',
    color: '#facc15',
    fontFamily: "'Press Start 2P', monospace",
    letterSpacing: '0.5px',
  },
  statBar: {
    height: '3px',
    backgroundColor: '#c084fc',
    marginTop: '8px',
    boxShadow: '0 0 8px #c084fc',
  },
  featureGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '10px',
  },
  featureCard: {
    backgroundColor: '#000',
    border: '1px solid #66d9ef',
    padding: '12px',
    textAlign: 'center' as const,
    transition: 'all 0.3s',
  },
  featureIcon: {
    fontSize: '22px',
    color: '#c084fc',
    marginBottom: '8px',
    textShadow: '0 0 8px #c084fc',
  },
  featureTitle: {
    fontSize: '9px',
    fontWeight: 'bold',
    color: '#66d9ef',
    marginBottom: '6px',
    fontFamily: "'Press Start 2P', monospace",
    letterSpacing: '0.5px',
  },
  featureLine: {
    height: '1px',
    backgroundColor: '#66d9ef',
    margin: '6px 0',
    boxShadow: '0 0 3px #66d9ef',
  },
  featureDesc: {
    fontSize: '10px',
    color: '#facc15',
    lineHeight: 1.4,
  },
  retroBox: {
    backgroundColor: '#000',
    border: '2px solid #c084fc',
    marginBottom: '15px',
    boxShadow: '0 0 20px rgba(192, 132, 252, 0.2)',
    display: 'block',
    visibility: 'visible',
    opacity: 1,
  },
  retroBoxHeader: {
    padding: '8px',
    backgroundColor: '#c084fc',
    color: '#000',
    fontSize: '10px',
    fontWeight: 'bold',
    fontFamily: "'Press Start 2P', monospace",
    letterSpacing: '1px',
  },
  architectureDiagram: {
    padding: '15px',
    display: 'block',
    visibility: 'visible',
  },
  architectureLayer: {
    marginBottom: '15px',
  },
  layerTitle: {
    fontSize: '10px',
    fontWeight: 'bold',
    padding: '6px',
    border: '1px solid',
    marginBottom: '8px',
    textAlign: 'center' as const,
    fontFamily: "'Press Start 2P', monospace",
    letterSpacing: '1px',
    textShadow: '0 0 8px currentColor',
  },
  componentRow: {
    display: 'flex',
    gap: '8px',
    justifyContent: 'center',
    flexWrap: 'wrap' as const,
    marginBottom: '6px',
  },
  component: {
    flex: '1 1 100px',
    minWidth: '100px',
    maxWidth: '130px',
    padding: '10px',
    border: '1px solid',
    backgroundColor: '#000',
    textAlign: 'center' as const,
    transition: 'all 0.3s',
  },
  componentText: {
    fontSize: '8px',
    color: '#66d9ef',
    fontFamily: "'Press Start 2P', monospace",
    lineHeight: 1.3,
    textShadow: '0 0 4px #66d9ef',
  },
  layerArrow: {
    textAlign: 'center' as const,
    fontSize: '14px',
    color: '#facc15',
    margin: '8px 0',
    textShadow: '0 0 8px #facc15',
  },
  pipelineFlow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '15px',
    overflowX: 'auto' as const,
    flexWrap: 'nowrap' as const,
    minWidth: '100%',
  },
  pipelineStep: {
    minWidth: '110px',
    maxWidth: '120px',
    padding: '10px',
    backgroundColor: '#000',
    border: '1px solid',
    textAlign: 'center' as const,
    transition: 'all 0.3s',
    flexShrink: 0,
  },
  pipelineArrowContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '0 10px',
    flexShrink: 0,
  },
  pipelinePhase: {
    padding: '4px 6px',
    fontSize: '8px',
    fontWeight: 'bold',
    color: '#000',
    marginBottom: '6px',
    fontFamily: "'Press Start 2P', monospace",
    letterSpacing: '0.5px',
  },
  pipelineTitle: {
    fontSize: '9px',
    fontWeight: 'bold',
    color: '#0ff',
    marginBottom: '4px',
    fontFamily: "'Press Start 2P', monospace",
  },
  pipelineTech: {
    fontSize: '9px',
    color: '#ffff00',
  },
  pipelineArrow: {
    fontSize: '24px',
    color: '#ff00ff',
    textShadow: '0 0 10px #ff00ff, 0 0 15px #ff00ff',
    fontWeight: 'bold',
    animation: 'blink 1.5s infinite',
  },
  codeBox: {
    backgroundColor: '#000',
    border: '2px solid #4ade80',
    marginBottom: '15px',
    boxShadow: '0 0 20px rgba(74, 222, 128, 0.2)',
  },
  codeHeader: {
    padding: '8px',
    backgroundColor: '#4ade80',
    color: '#000',
    fontSize: '10px',
    fontWeight: 'bold',
    fontFamily: "'Press Start 2P', monospace",
  },
  codeContent: {
    padding: '12px',
    fontSize: '11px',
    lineHeight: 1.5,
    color: '#4ade80',
    margin: 0,
    overflowX: 'auto' as const,
    textShadow: '0 0 4px #4ade80',
  },
  queryFlow: {
    padding: '15px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
    alignItems: 'center' as const,
  },
  queryStep: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    width: '100%',
    maxWidth: '600px',
  },
  queryNum: {
    width: '35px',
    height: '35px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '12px',
    fontWeight: 'bold',
    color: '#000',
    fontFamily: "'Press Start 2P', monospace",
    flexShrink: 0,
    boxShadow: '0 0 12px currentColor',
  },
  queryContent: {
    flex: 1,
    padding: '10px',
    border: '1px solid #66d9ef',
    backgroundColor: '#000',
  },
  queryTitle: {
    fontSize: '10px',
    fontWeight: 'bold',
    color: '#66d9ef',
    marginBottom: '4px',
    fontFamily: "'Press Start 2P', monospace",
  },
  queryDesc: {
    fontSize: '10px',
    color: '#facc15',
  },
  queryArrowContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
    maxWidth: '800px',
    padding: '5px 0',
  },
  queryArrow: {
    fontSize: '20px',
    color: '#c084fc',
    textAlign: 'center' as const,
    textShadow: '0 0 10px #c084fc, 0 0 15px #c084fc',
    fontWeight: 'bold',
    animation: 'blink 1.5s infinite',
  },
  entityGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))',
    gap: '8px',
    padding: '15px',
  },
  entityCard: {
    padding: '12px',
    backgroundColor: '#000',
    border: '1px solid',
    textAlign: 'center' as const,
    transition: 'all 0.3s',
  },
  entityIcon: {
    fontSize: '22px',
    marginBottom: '6px',
    textShadow: '0 0 8px currentColor',
  },
  entityType: {
    fontSize: '9px',
    color: '#66d9ef',
    fontFamily: "'Press Start 2P', monospace",
  },
  relationshipBox: {
    backgroundColor: '#000',
    border: '2px solid #facc15',
    padding: '12px',
    marginTop: '15px',
    boxShadow: '0 0 20px rgba(250, 204, 21, 0.2)',
  },
  relationshipHeader: {
    fontSize: '10px',
    fontWeight: 'bold',
    color: '#facc15',
    marginBottom: '10px',
    fontFamily: "'Press Start 2P', monospace",
    textShadow: '0 0 8px #facc15',
  },
  relationshipGrid: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '6px',
  },
  relationshipBadge: {
    padding: '5px 8px',
    border: '1px solid #facc15',
    backgroundColor: '#000',
  },
  relationshipText: {
    fontSize: '8px',
    color: '#facc15',
    fontFamily: "'Press Start 2P', monospace",
  },
  apiGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: '10px',
    marginBottom: '20px',
  },
  apiCard: {
    backgroundColor: '#000',
    border: '1px solid #66d9ef',
    padding: '12px',
    transition: 'all 0.3s',
  },
  apiMethod: {
    fontSize: '9px',
    color: '#4ade80',
    marginBottom: '6px',
    fontFamily: "'Press Start 2P', monospace",
    textShadow: '0 0 4px #4ade80',
  },
  apiEndpoint: {
    fontSize: '11px',
    color: '#66d9ef',
    marginBottom: '6px',
    fontWeight: 'bold',
  },
  apiDesc: {
    fontSize: '10px',
    color: '#facc15',
  },
  linkGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
    gap: '10px',
  },
  linkCard: {
    backgroundColor: '#000',
    border: '1px solid #c084fc',
    padding: '12px',
    textAlign: 'center' as const,
    textDecoration: 'none',
    transition: 'all 0.3s',
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
  },
  linkIcon: {
    fontSize: '22px',
    color: '#c084fc',
    marginBottom: '6px',
    textShadow: '0 0 8px #c084fc',
  },
  linkTitle: {
    fontSize: '9px',
    color: '#66d9ef',
    marginBottom: '4px',
    fontFamily: "'Press Start 2P', monospace",
  },
  linkUrl: {
    fontSize: '9px',
    color: '#facc15',
  },
  deployGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '10px',
    marginBottom: '15px',
  },
  deployCard: {
    backgroundColor: '#000',
    border: '2px solid #4ade80',
    padding: '15px',
    textAlign: 'center' as const,
    transition: 'all 0.3s',
  },
  deployIcon: {
    fontSize: '28px',
    color: '#4ade80',
    marginBottom: '8px',
    textShadow: '0 0 10px #4ade80',
  },
  deployTitle: {
    fontSize: '9px',
    fontWeight: 'bold',
    color: '#66d9ef',
    marginBottom: '6px',
    fontFamily: "'Press Start 2P', monospace",
  },
  deployDesc: {
    fontSize: '10px',
    color: '#facc15',
  },
  startGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: '10px',
  },
  startCard: {
    backgroundColor: '#000',
    border: '1px solid #c084fc',
    padding: '12px',
    transition: 'all 0.3s',
  },
  startNum: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#c084fc',
    marginBottom: '6px',
    fontFamily: "'Press Start 2P', monospace",
    textShadow: '0 0 8px #c084fc',
  },
  startTitle: {
    fontSize: '9px',
    fontWeight: 'bold',
    color: '#66d9ef',
    marginBottom: '6px',
    fontFamily: "'Press Start 2P', monospace",
  },
  startCmd: {
    fontSize: '10px',
    color: '#4ade80',
    padding: '6px',
    backgroundColor: '#0a0a0a',
    border: '1px solid #4ade80',
    textShadow: '0 0 4px #4ade80',
  },
  footer: {
    marginTop: '40px',
    paddingBottom: '20px',
  },
  footerBorder: {
    height: '3px',
    background: 'repeating-linear-gradient(90deg, #66d9ef 0px, #66d9ef 6px, #c084fc 6px, #c084fc 12px, #facc15 12px, #facc15 18px)',
    marginBottom: '10px',
    boxShadow: '0 0 8px rgba(102, 217, 239, 0.3)',
  },
  footerContent: {
    textAlign: 'center' as const,
    padding: '15px',
    backgroundColor: '#000',
    border: '2px solid #66d9ef',
    boxShadow: '0 0 20px rgba(102, 217, 239, 0.2)',
  },
  footerText: {
    fontSize: '11px',
    color: '#66d9ef',
    marginBottom: '8px',
    fontFamily: "'Press Start 2P', monospace",
    textShadow: '0 0 8px #66d9ef',
    letterSpacing: '1px',
  },
  footerTech: {
    fontSize: '9px',
    color: '#facc15',
    marginBottom: '8px',
    fontFamily: "'Press Start 2P', monospace",
    letterSpacing: '0.5px',
  },
  footerVersion: {
    fontSize: '8px',
    color: '#c084fc',
    fontFamily: "'Press Start 2P', monospace",
  },
};

export default DocumentationPage;
