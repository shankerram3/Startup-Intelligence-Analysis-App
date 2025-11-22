import React, { useState } from 'react';

interface Section {
  id: string;
  title: string;
  icon: string;
}

const DocumentationPage: React.FC = () => {
  const [activeSection, setActiveSection] = useState<string>('overview');

  const sections: Section[] = [
    { id: 'overview', title: 'Overview', icon: '🏠' },
    { id: 'architecture', title: 'Architecture', icon: '🏗️' },
    { id: 'pipeline', title: 'Data Pipeline', icon: '⚙️' },
    { id: 'graphrag', title: 'GraphRAG System', icon: '🧠' },
    { id: 'entities', title: 'Entity Model', icon: '📊' },
    { id: 'api', title: 'API Reference', icon: '🔌' },
    { id: 'deployment', title: 'Deployment', icon: '🚀' },
    { id: 'quickstart', title: 'Quick Start', icon: '⚡' },
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
        /* Quick link hover effects */
        a[style*="quickLinkCard"]:hover {
          border-color: #3b82f6 !important;
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15) !important;
          transform: translateY(-2px);
        }
        
        /* Feature card hover effects */
        div[style*="featureCard"]:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
        }
        
        /* Nav item hover effects */
        button[style*="navItem"]:hover {
          background-color: #f8fafc;
        }
      `}</style>
      {/* Sidebar Navigation */}
      <aside style={styles.sidebar}>
        <div style={styles.sidebarHeader}>
          <h2 style={styles.sidebarTitle}>📚 Documentation</h2>
        </div>
        <nav style={styles.nav}>
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => scrollToSection(section.id)}
              style={{
                ...styles.navItem,
                ...(activeSection === section.id ? styles.navItemActive : {}),
              }}
            >
              <span style={styles.navIcon}>{section.icon}</span>
              <span>{section.title}</span>
            </button>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main style={styles.content}>
        {/* Overview Section */}
        <section id="overview" style={styles.section}>
          <h1 style={styles.h1}>🚀 Startup Intelligence Analysis Platform</h1>
          <p style={styles.lead}>
            A production-ready knowledge graph and GraphRAG system powered by GPT-4o that extracts entities 
            and relationships from TechCrunch articles, enriches them with deep company intelligence via Playwright, 
            stores them in Neo4j Aura, and provides intelligent querying through 40+ REST API endpoints with 
            hybrid semantic search capabilities. Features a modern React frontend with futuristic UI design, 
            professional dark theme, interactive chat interface, and comprehensive monitoring.
          </p>

          <div style={styles.statsGrid}>
            <div style={styles.statCard}>
              <div style={styles.statNumber}>40+</div>
              <div style={styles.statLabel}>API Endpoints</div>
      </div>
            <div style={styles.statCard}>
              <div style={styles.statNumber}>8</div>
              <div style={styles.statLabel}>Entity Types</div>
          </div>
            <div style={styles.statCard}>
              <div style={styles.statNumber}>15+</div>
              <div style={styles.statLabel}>Relationship Types</div>
        </div>
            <div style={styles.statCard}>
              <div style={styles.statNumber}>6</div>
              <div style={styles.statLabel}>Pipeline Phases</div>
      </div>
    </div>

          <div style={styles.featureGrid}>
            <div style={styles.featureCard}>
              <div style={styles.featureIcon}>🤖</div>
              <h3 style={styles.featureTitle}>GPT-4o Entity Extraction</h3>
              <p style={styles.featureDesc}>Advanced NER with LangChain extracting 8 entity types and relationships with retry logic</p>
            </div>
            <div style={styles.featureCard}>
              <div style={styles.featureIcon}>🕸️</div>
              <h3 style={styles.featureTitle}>Neo4j Aura Cloud</h3>
              <p style={styles.featureDesc}>Managed graph database with GDS (Graph Data Science) for community detection</p>
            </div>
            <div style={styles.featureCard}>
              <div style={styles.featureIcon}>🔍</div>
              <h3 style={styles.featureTitle}>Hybrid RAG Search</h3>
              <p style={styles.featureDesc}>BAAI/bge-small-en-v1.5 embeddings + keyword search with intelligent query routing</p>
            </div>
            <div style={styles.featureCard}>
              <div style={styles.featureIcon}>💬</div>
              <h3 style={styles.featureTitle}>Multi-Hop Reasoning</h3>
              <p style={styles.featureDesc}>Complex graph traversal for entity comparison, aggregation, and relationship queries</p>
            </div>
            <div style={styles.featureCard}>
              <div style={styles.featureIcon}>🏢</div>
              <h3 style={styles.featureTitle}>Company Intelligence</h3>
              <p style={styles.featureDesc}>Playwright scraper enriching companies with founders, funding, products, and team data</p>
            </div>
            <div style={styles.featureCard}>
              <div style={styles.featureIcon}>⚡</div>
              <h3 style={styles.featureTitle}>40+ REST Endpoints</h3>
              <p style={styles.featureDesc}>FastAPI with Pydantic validation, CORS, health checks, Swagger UI, rate limiting, and security</p>
            </div>
            <div style={styles.featureCard}>
              <div style={styles.featureIcon}>✨</div>
              <h3 style={styles.featureTitle}>Auto Post-Processing</h3>
              <p style={styles.featureDesc}>Sentence-transformers embeddings, entity deduplication, and Leiden community detection</p>
            </div>
            <div style={styles.featureCard}>
              <div style={styles.featureIcon}>🎯</div>
              <h3 style={styles.featureTitle}>Production Ready</h3>
              <p style={styles.featureDesc}>Checkpoint system, progress tracking, validation, Docker support, Redis caching, Prometheus metrics, and structured logging</p>
            </div>
            <div style={styles.featureCard}>
              <div style={styles.featureIcon}>🎨</div>
              <h3 style={styles.featureTitle}>Modern UI</h3>
              <p style={styles.featureDesc}>Futuristic header design, professional dark theme, interactive chat with history, collapsible templates, and minimal scrollbars</p>
            </div>
            <div style={styles.featureCard}>
              <div style={styles.featureIcon}>⚡</div>
              <h3 style={styles.featureTitle}>Performance</h3>
              <p style={styles.featureDesc}>Redis caching for queries and relationships, optimized pipeline logging, and enhanced community detection with Aura Graph Analytics</p>
            </div>
          </div>
        </section>

        {/* Architecture Section */}
        <section id="architecture" style={styles.section}>
          <h1 style={styles.h1}>🏗️ System Architecture</h1>
          
          <div style={styles.diagramCard}>
            <h3 style={styles.diagramTitle}>High-Level Architecture</h3>
            <div style={styles.architectureDiagram}>
              <div style={styles.architectureLayer}>
                <div style={styles.layerTitle}>Frontend Layer</div>
                <div style={styles.componentRow}>
                  <div style={{...styles.component, ...styles.componentReact}}>
                    <div style={styles.componentIcon}>⚛️</div>
                    <div style={styles.componentName}>React UI</div>
                    <div style={styles.componentDesc}>TypeScript + Vite</div>
                  </div>
                  <div style={{...styles.component, ...styles.componentReact}}>
                    <div style={styles.componentIcon}>💬</div>
                    <div style={styles.componentName}>Chat Interface</div>
                    <div style={styles.componentDesc}>Real-time queries with history</div>
                  </div>
                  <div style={{...styles.component, ...styles.componentReact}}>
                    <div style={styles.componentIcon}>📊</div>
                    <div style={styles.componentName}>Dashboard</div>
                    <div style={styles.componentDesc}>Analytics & Viz</div>
                  </div>
                  <div style={{...styles.component, ...styles.componentReact}}>
                    <div style={styles.componentIcon}>🎨</div>
                    <div style={styles.componentName}>Modern UI</div>
                    <div style={styles.componentDesc}>Dark theme, futuristic design</div>
                  </div>
                </div>
              </div>

              <div style={styles.arrow}>↓</div>

              <div style={styles.architectureLayer}>
                <div style={styles.layerTitle}>API Layer</div>
                <div style={styles.componentRow}>
                  <div style={{...styles.component, ...styles.componentApi}}>
                    <div style={styles.componentIcon}>⚡</div>
                    <div style={styles.componentName}>FastAPI</div>
                    <div style={styles.componentDesc}>40+ REST endpoints</div>
                  </div>
                  <div style={{...styles.component, ...styles.componentApi}}>
                    <div style={styles.componentIcon}>🔀</div>
                    <div style={styles.componentName}>Query Router</div>
                    <div style={styles.componentDesc}>Intelligent routing</div>
                  </div>
                  <div style={{...styles.component, ...styles.componentApi}}>
                    <div style={styles.componentIcon}>🧠</div>
                    <div style={styles.componentName}>RAG Engine</div>
                    <div style={styles.componentDesc}>Hybrid search</div>
                  </div>
                  <div style={{...styles.component, ...styles.componentApi}}>
                    <div style={styles.componentIcon}>🔒</div>
                    <div style={styles.componentName}>Security</div>
                    <div style={styles.componentDesc}>JWT auth, rate limiting</div>
                  </div>
                  <div style={{...styles.component, ...styles.componentApi}}>
                    <div style={styles.componentIcon}>📊</div>
                    <div style={styles.componentName}>Monitoring</div>
                    <div style={styles.componentDesc}>Prometheus metrics</div>
                  </div>
                  <div style={{...styles.component, ...styles.componentApi}}>
                    <div style={styles.componentIcon}>💾</div>
                    <div style={styles.componentName}>Cache</div>
                    <div style={styles.componentDesc}>Redis caching</div>
                  </div>
                </div>
              </div>

              <div style={styles.arrow}>↓</div>

              <div style={styles.architectureLayer}>
                <div style={styles.layerTitle}>Processing Layer</div>
                <div style={styles.componentRow}>
                  <div style={{...styles.component, ...styles.componentProcess}}>
                    <div style={styles.componentIcon}>🕷️</div>
                    <div style={styles.componentName}>Web Scraper</div>
                    <div style={styles.componentDesc}>TechCrunch + Playwright</div>
                  </div>
                  <div style={{...styles.component, ...styles.componentProcess}}>
                    <div style={styles.componentIcon}>🤖</div>
                    <div style={styles.componentName}>Entity Extractor</div>
                    <div style={styles.componentDesc}>GPT-4o NER</div>
                  </div>
                  <div style={{...styles.component, ...styles.componentProcess}}>
                    <div style={styles.componentIcon}>🔗</div>
                    <div style={styles.componentName}>Graph Builder</div>
                    <div style={styles.componentDesc}>Neo4j integration</div>
                  </div>
                </div>
              </div>

              <div style={styles.arrow}>↓</div>

              <div style={styles.architectureLayer}>
                <div style={styles.layerTitle}>Data Layer</div>
                <div style={styles.componentRow}>
                  <div style={{...styles.component, ...styles.componentData}}>
                    <div style={styles.componentIcon}>🗄️</div>
                    <div style={styles.componentName}>Neo4j</div>
                    <div style={styles.componentDesc}>Graph database</div>
                  </div>
                  <div style={{...styles.component, ...styles.componentData}}>
                    <div style={styles.componentIcon}>🔢</div>
                    <div style={styles.componentName}>Vector Index</div>
                    <div style={styles.componentDesc}>Embeddings store</div>
                  </div>
                  <div style={{...styles.component, ...styles.componentData}}>
                    <div style={styles.componentIcon}>📁</div>
                    <div style={styles.componentName}>File Storage</div>
                    <div style={styles.componentDesc}>Raw data cache</div>
                  </div>
                  <div style={{...styles.component, ...styles.componentData}}>
                    <div style={styles.componentIcon}>⚡</div>
                    <div style={styles.componentName}>Redis Cache</div>
                    <div style={styles.componentDesc}>Query & entity caching</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Pipeline Section */}
        <section id="pipeline" style={styles.section}>
          <h1 style={styles.h1}>⚙️ Data Pipeline Flow</h1>
          
          <div style={styles.diagramCard}>
            <h3 style={styles.diagramTitle}>End-to-End Pipeline</h3>
            <div style={styles.pipelineFlow}>
              {[
                { phase: 'Phase 0', title: 'Web Scraping', icon: '🕷️', desc: 'Crawl4AI + BeautifulSoup extraction', color: '#3b82f6', tech: 'crawl4ai, aiofiles' },
                { phase: 'Phase 1', title: 'Entity Extraction', icon: '🤖', desc: 'GPT-4o via LangChain with retry', color: '#8b5cf6', tech: 'langchain-openai, pydantic' },
                { phase: 'Phase 1.5', title: 'Company Intelligence', icon: '🏢', desc: 'Playwright deep scraping', color: '#ec4899', tech: 'playwright, company_intelligence_scraper' },
                { phase: 'Phase 2', title: 'Graph Construction', icon: '🔗', desc: 'Neo4j Aura with constraints', color: '#10b981', tech: 'neo4j-driver, graph_builder' },
                { phase: 'Phase 3', title: 'Graph Cleanup', icon: '🧹', desc: 'Deduplication & validation', color: '#f59e0b', tech: 'entity_resolver, graph_cleanup' },
                { phase: 'Phase 4', title: 'Post-Processing', icon: '✨', desc: 'Embeddings + GDS communities', color: '#06b6d4', tech: 'sentence-transformers, graphdatascience' },
              ].map((step, idx) => (
                <React.Fragment key={step.phase}>
                  <div style={{...styles.pipelineStep, borderColor: step.color}}>
                    <div style={{...styles.pipelinePhase, backgroundColor: step.color}}>{step.phase}</div>
                    <div style={styles.pipelineIcon}>{step.icon}</div>
                    <div style={styles.pipelineTitle}>{step.title}</div>
                    <div style={styles.pipelineDesc}>{step.desc}</div>
                    <div style={styles.pipelineTech}>{step.tech}</div>
                  </div>
                  {idx < 5 && <div style={styles.pipelineArrow}>→</div>}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div style={styles.codeBlock}>
            <div style={styles.codeHeader}>
              <span style={styles.codeTitle}>💻 Run Complete Pipeline</span>
            </div>
            <pre style={styles.code}>
{`# Full pipeline with all phases (automatic embeddings!)
python pipeline.py \\
  --scrape-category startups \\
  --scrape-max-pages 2 \\
  --max-articles 10

# Use existing articles (skip scraping)
python pipeline.py --skip-scraping --max-articles 50

# Use existing extractions (skip to graph building)
python pipeline.py --skip-scraping --skip-extraction

# Skip company enrichment (Phase 1.5)
python pipeline.py --skip-enrichment

# Control company enrichment limit
python pipeline.py --max-companies-to-scrape 20`}
            </pre>
          </div>

          {/* Utility Modules */}
          <div style={styles.utilitySection}>
            <h2 style={styles.subsectionTitle}>🔧 Core Utility Modules</h2>
            <div style={styles.utilityGrid}>
              <div style={styles.utilityCard}>
                <div style={styles.utilityIcon}>📍</div>
                <h4 style={styles.utilityTitle}>checkpoint.py</h4>
                <p style={styles.utilityDesc}>Resume capability for long-running extractions</p>
              </div>
              <div style={styles.utilityCard}>
                <div style={styles.utilityIcon}>🔄</div>
                <h4 style={styles.utilityTitle}>entity_resolver.py</h4>
                <p style={styles.utilityDesc}>Automatic entity deduplication and merging</p>
              </div>
              <div style={styles.utilityCard}>
                <div style={styles.utilityIcon}>✅</div>
                <h4 style={styles.utilityTitle}>data_validation.py</h4>
                <p style={styles.utilityDesc}>Multi-layer article and extraction validation</p>
              </div>
              <div style={styles.utilityCard}>
                <div style={styles.utilityIcon}>🔢</div>
                <h4 style={styles.utilityTitle}>embedding_generator.py</h4>
                <p style={styles.utilityDesc}>Sentence-transformers vector embeddings</p>
              </div>
              <div style={styles.utilityCard}>
                <div style={styles.utilityIcon}>👥</div>
                <h4 style={styles.utilityTitle}>community_detector.py</h4>
                <p style={styles.utilityDesc}>Leiden, Louvain, Label Propagation algorithms</p>
              </div>
              <div style={styles.utilityCard}>
                <div style={styles.utilityIcon}>📊</div>
                <h4 style={styles.utilityTitle}>relationship_scorer.py</h4>
                <p style={styles.utilityDesc}>Relationship strength scoring and ranking</p>
              </div>
              <div style={styles.utilityCard}>
                <div style={styles.utilityIcon}>🏢</div>
                <h4 style={styles.utilityTitle}>company_intelligence_aggregator.py</h4>
                <p style={styles.utilityDesc}>Aggregate and enrich company data</p>
              </div>
              <div style={styles.utilityCard}>
                <div style={styles.utilityIcon}>🧹</div>
                <h4 style={styles.utilityTitle}>graph_cleanup.py</h4>
                <p style={styles.utilityDesc}>Fix MENTIONED_IN and duplicate relationships</p>
              </div>
              <div style={styles.utilityCard}>
                <div style={styles.utilityIcon}>📈</div>
                <h4 style={styles.utilityTitle}>progress_tracker.py</h4>
                <p style={styles.utilityDesc}>Real-time progress monitoring with ETA</p>
              </div>
              <div style={styles.utilityCard}>
                <div style={styles.utilityIcon}>🔁</div>
                <h4 style={styles.utilityTitle}>retry.py</h4>
                <p style={styles.utilityDesc}>Exponential backoff for API calls</p>
              </div>
              <div style={styles.utilityCard}>
                <div style={styles.utilityIcon}>📅</div>
                <h4 style={styles.utilityTitle}>temporal_analyzer.py</h4>
                <p style={styles.utilityDesc}>Time-based trend analysis</p>
              </div>
              <div style={styles.utilityCard}>
                <div style={styles.utilityIcon}>☁️</div>
                <h4 style={styles.utilityTitle}>aura_graph_analytics.py</h4>
                <p style={styles.utilityDesc}>Neo4j Aura GDS integration</p>
              </div>
            </div>
          </div>
        </section>

        {/* GraphRAG Section */}
        <section id="graphrag" style={styles.section}>
          <h1 style={styles.h1}>🧠 GraphRAG Query System</h1>
          
          <div style={styles.diagramCard}>
            <h3 style={styles.diagramTitle}>Query Processing Flow</h3>
            <div style={styles.queryFlow}>
              <div style={styles.queryStep}>
                <div style={styles.queryStepNumber}>1</div>
                <div style={styles.queryStepContent}>
                  <div style={styles.queryStepTitle}>📝 User Query</div>
                  <div style={styles.queryStepDesc}>Natural language question</div>
                  <div style={styles.queryExample}>"Which AI startups raised funding?"</div>
                </div>
              </div>

              <div style={styles.queryArrow}>↓</div>

              <div style={styles.queryStep}>
                <div style={styles.queryStepNumber}>2</div>
                <div style={styles.queryStepContent}>
                  <div style={styles.queryStepTitle}>🔀 Query Routing</div>
                  <div style={styles.queryStepDesc}>Classify query type & select strategy</div>
                  <div style={styles.queryTypes}>
                    <span style={styles.queryType}>Entity</span>
                    <span style={styles.queryType}>Relationship</span>
                    <span style={styles.queryType}>Comparison</span>
                    <span style={styles.queryType}>Aggregation</span>
                  </div>
                </div>
              </div>

              <div style={styles.queryArrow}>↓</div>

              <div style={styles.queryStep}>
                <div style={styles.queryStepNumber}>3</div>
                <div style={styles.queryStepContent}>
                  <div style={styles.queryStepTitle}>🔍 Hybrid Search</div>
                  <div style={styles.queryStepDesc}>Parallel semantic + keyword search</div>
                  <div style={styles.searchMethods}>
                    <div style={styles.searchMethod}>
                      <div style={styles.searchIcon}>🔢</div>
                      <div>Vector Similarity</div>
                    </div>
                    <div style={styles.searchMethod}>
                      <div style={styles.searchIcon}>🔤</div>
                      <div>Keyword Match</div>
                    </div>
                    <div style={styles.searchMethod}>
                      <div style={styles.searchIcon}>🕸️</div>
                      <div>Graph Traversal</div>
                    </div>
                  </div>
                </div>
              </div>

              <div style={styles.queryArrow}>↓</div>

              <div style={styles.queryStep}>
                <div style={styles.queryStepNumber}>4</div>
                <div style={styles.queryStepContent}>
                  <div style={styles.queryStepTitle}>🎯 Context Retrieval</div>
                  <div style={styles.queryStepDesc}>Extract relevant entities & relationships</div>
                  <div style={styles.contextBox}>
                    <div style={styles.contextItem}>• Companies with AI technology</div>
                    <div style={styles.contextItem}>• Funding relationships</div>
                    <div style={styles.contextItem}>• Investment amounts & dates</div>
                  </div>
                </div>
              </div>

              <div style={styles.queryArrow}>↓</div>

              <div style={styles.queryStep}>
                <div style={styles.queryStepNumber}>5</div>
                <div style={styles.queryStepContent}>
                  <div style={styles.queryStepTitle}>🤖 LLM Generation</div>
                  <div style={styles.queryStepDesc}>Generate natural language answer</div>
                  <div style={styles.answerBox}>
                    "Based on the knowledge graph, 3 AI startups raised funding: 
                    OpenAI ($10B from Microsoft), Anthropic ($450M from Google), 
                    and Stability AI ($101M from Coatue)."
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div style={styles.infoBox}>
            <div style={styles.infoIcon}>💡</div>
            <div>
              <strong>Hybrid RAG combines:</strong> Vector embeddings for semantic similarity, 
              keyword search for exact matches, and graph traversal for relationship discovery.
            </div>
          </div>
        </section>

        {/* Entity Model Section */}
        <section id="entities" style={styles.section}>
          <h1 style={styles.h1}>📊 Entity & Relationship Model</h1>
          
          <div style={styles.diagramCard}>
            <h3 style={styles.diagramTitle}>Knowledge Graph Schema</h3>
            <div style={styles.entityDiagram}>
              <div style={styles.entityGroup}>
                <div style={styles.entityGroupTitle}>Core Entities</div>
                <div style={styles.entityRow}>
                  <div style={{...styles.entity, ...styles.entityCompany}}>
                    <div style={styles.entityIcon}>🏢</div>
                    <div style={styles.entityName}>Company</div>
                    <div style={styles.entityProps}>name, founded, employees, headquarters</div>
                  </div>
                  <div style={{...styles.entity, ...styles.entityPerson}}>
                    <div style={styles.entityIcon}>👤</div>
                    <div style={styles.entityName}>Person</div>
                    <div style={styles.entityProps}>name, role, title</div>
                  </div>
                  <div style={{...styles.entity, ...styles.entityInvestor}}>
                    <div style={styles.entityIcon}>💰</div>
                    <div style={styles.entityName}>Investor</div>
                    <div style={styles.entityProps}>name, type, portfolio</div>
                  </div>
                </div>
              </div>

              <div style={styles.relationshipLines}>
                <svg width="100%" height="80" style={{overflow: 'visible'}}>
                  <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                      <polygon points="0 0, 10 3, 0 6" fill="#64748b" />
                    </marker>
                  </defs>
                  <line x1="20%" y1="10" x2="50%" y2="70" stroke="#64748b" strokeWidth="2" markerEnd="url(#arrowhead)" />
                  <line x1="50%" y1="10" x2="50%" y2="70" stroke="#64748b" strokeWidth="2" markerEnd="url(#arrowhead)" />
                  <line x1="80%" y1="10" x2="50%" y2="70" stroke="#64748b" strokeWidth="2" markerEnd="url(#arrowhead)" />
                  
                  <text x="15%" y="45" fill="#64748b" fontSize="11" fontWeight="600">FOUNDED_BY</text>
                  <text x="45%" y="45" fill="#64748b" fontSize="11" fontWeight="600">WORKS_AT</text>
                  <text x="70%" y="45" fill="#64748b" fontSize="11" fontWeight="600">FUNDED_BY</text>
                </svg>
              </div>

              <div style={styles.entityGroup}>
                <div style={styles.entityGroupTitle}>Supporting Entities</div>
                <div style={styles.entityRow}>
                  <div style={{...styles.entity, ...styles.entityTech}}>
                    <div style={styles.entityIcon}>⚙️</div>
                    <div style={styles.entityName}>Technology</div>
                  </div>
                  <div style={{...styles.entity, ...styles.entityProduct}}>
                    <div style={styles.entityIcon}>📦</div>
                    <div style={styles.entityName}>Product</div>
                  </div>
                  <div style={{...styles.entity, ...styles.entityFunding}}>
                    <div style={styles.entityIcon}>💵</div>
                    <div style={styles.entityName}>FundingRound</div>
                  </div>
                  <div style={{...styles.entity, ...styles.entityLocation}}>
                    <div style={styles.entityIcon}>📍</div>
                    <div style={styles.entityName}>Location</div>
                  </div>
                  <div style={{...styles.entity, ...styles.entityEvent}}>
                    <div style={styles.entityIcon}>🎯</div>
                    <div style={styles.entityName}>Event</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div style={styles.relationshipGrid}>
            <h3 style={styles.subsectionTitle}>Relationship Types (15+)</h3>
            <div style={styles.relationshipList}>
              {[
                'FUNDED_BY', 'FOUNDED_BY', 'WORKS_AT', 'ACQUIRED', 'PARTNERS_WITH',
                'COMPETES_WITH', 'USES_TECHNOLOGY', 'LOCATED_IN', 'ANNOUNCED_AT',
                'INVESTS_IN', 'ADVISES', 'LEADS', 'COLLABORATES_WITH', 'REGULATES',
                'OPPOSES', 'SUPPORTS', 'MENTIONED_IN'
              ].map(rel => (
                <div key={rel} style={styles.relationshipBadge}>{rel}</div>
              ))}
            </div>
          </div>

          {/* Entity Properties */}
          <div style={styles.entityPropertiesSection}>
            <h3 style={styles.subsectionTitle}>Enriched Entity Properties</h3>
            <div style={styles.propertiesGrid}>
              <div style={styles.propertyCard}>
                <h4 style={styles.propertyTitle}>Company Properties</h4>
                <ul style={styles.propertyList}>
                  <li>name, id, description</li>
                  <li>headquarters, founded_year</li>
                  <li>founders, employees_count</li>
                  <li>products, technologies</li>
                  <li>funding_total, funding_stage</li>
                  <li>website_url, social_links</li>
                  <li>enrichment_status, embedding</li>
                </ul>
              </div>
              <div style={styles.propertyCard}>
                <h4 style={styles.propertyTitle}>Person Properties</h4>
                <ul style={styles.propertyList}>
                  <li>name, id, description</li>
                  <li>role, title</li>
                  <li>company affiliations</li>
                  <li>embedding vector</li>
                </ul>
              </div>
              <div style={styles.propertyCard}>
                <h4 style={styles.propertyTitle}>Article Properties</h4>
                <ul style={styles.propertyList}>
                  <li>id, title, url</li>
                  <li>published_date, author</li>
                  <li>content, summary</li>
                  <li>category, tags</li>
                  <li>embedding vector</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* API Reference Section */}
        <section id="api" style={styles.section}>
          <h1 style={styles.h1}>🔌 API Reference</h1>
          
          <p style={styles.lead}>
            The platform provides 40+ REST API endpoints for querying the knowledge graph, 
            semantic search, entity management, and analytics.
          </p>

          <div style={styles.apiGrid}>
            <div style={styles.apiCard}>
              <div style={styles.apiMethod}>POST</div>
              <div style={styles.apiEndpoint}>/query</div>
              <div style={styles.apiDesc}>Execute natural language query with GraphRAG</div>
              <div style={styles.codeBlock}>
                <pre style={styles.code}>
{`curl -X POST http://localhost:8000/query \\
  -H "Content-Type: application/json" \\
  -d '{
    "question": "Which AI startups raised funding?",
    "use_llm": true
  }'`}
                </pre>
              </div>
            </div>

            <div style={styles.apiCard}>
              <div style={styles.apiMethod}>POST</div>
              <div style={styles.apiEndpoint}>/search/semantic</div>
              <div style={styles.apiDesc}>Vector similarity search with embeddings</div>
              <div style={styles.codeBlock}>
                <pre style={styles.code}>
{`curl -X POST http://localhost:8000/search/semantic \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "artificial intelligence",
    "limit": 10
  }'`}
                </pre>
              </div>
            </div>

            <div style={styles.apiCard}>
              <div style={styles.apiMethod}>POST</div>
              <div style={styles.apiEndpoint}>/search/hybrid</div>
              <div style={styles.apiDesc}>Combined semantic + keyword search</div>
              <div style={styles.codeBlock}>
                <pre style={styles.code}>
{`curl -X POST http://localhost:8000/search/hybrid \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "fintech startups",
    "limit": 10
  }'`}
                </pre>
              </div>
            </div>

            <div style={styles.apiCard}>
              <div style={styles.apiMethod}>GET</div>
              <div style={styles.apiEndpoint}>/company/{'{name}'}</div>
              <div style={styles.apiDesc}>Get company details and relationships</div>
              <div style={styles.codeBlock}>
                <pre style={styles.code}>
{`curl http://localhost:8000/company/OpenAI`}
                </pre>
              </div>
            </div>

            <div style={styles.apiCard}>
              <div style={styles.apiMethod}>GET</div>
              <div style={styles.apiEndpoint}>/investors/top</div>
              <div style={styles.apiDesc}>Get most active investors</div>
              <div style={styles.codeBlock}>
                <pre style={styles.code}>
{`curl http://localhost:8000/investors/top?limit=20`}
                </pre>
              </div>
            </div>

            <div style={styles.apiCard}>
              <div style={styles.apiMethod}>GET</div>
              <div style={styles.apiEndpoint}>/health</div>
              <div style={styles.apiDesc}>Check API and database connectivity</div>
              <div style={styles.codeBlock}>
                <pre style={styles.code}>
{`curl http://localhost:8000/health`}
                </pre>
              </div>
            </div>
          </div>

          <div style={styles.infoBox}>
            <div style={styles.infoIcon}>📖</div>
            <div>
              <strong>Full API Documentation:</strong> Visit{' '}
              <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" style={styles.link}>
                http://localhost:8000/docs
              </a>{' '}
              for interactive Swagger UI with all 40+ endpoints, request/response schemas, and try-it-out functionality.
            </div>
          </div>

          {/* Quick Links */}
          <div style={styles.quickLinksSection}>
            <h2 style={styles.subsectionTitle}>🔗 Quick Links</h2>
            <div style={styles.quickLinksGrid}>
              <a href="http://localhost:5173" target="_blank" rel="noopener noreferrer" style={styles.quickLinkCard}>
                <div style={styles.quickLinkIcon}>⚛️</div>
                <div style={styles.quickLinkTitle}>React Frontend</div>
                <div style={styles.quickLinkUrl}>http://localhost:5173</div>
              </a>
              <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" style={styles.quickLinkCard}>
                <div style={styles.quickLinkIcon}>📚</div>
                <div style={styles.quickLinkTitle}>API Docs</div>
                <div style={styles.quickLinkUrl}>http://localhost:8000/docs</div>
              </a>
              <a href="https://console.neo4j.io/" target="_blank" rel="noopener noreferrer" style={styles.quickLinkCard}>
                <div style={styles.quickLinkIcon}>☁️</div>
                <div style={styles.quickLinkTitle}>Neo4j Aura Console</div>
                <div style={styles.quickLinkUrl}>console.neo4j.io</div>
              </a>
              <a href="http://localhost:8000/health" target="_blank" rel="noopener noreferrer" style={styles.quickLinkCard}>
                <div style={styles.quickLinkIcon}>💚</div>
                <div style={styles.quickLinkTitle}>Health Check</div>
                <div style={styles.quickLinkUrl}>http://localhost:8000/health</div>
              </a>
            </div>
          </div>
        </section>

        {/* Deployment Section */}
        <section id="deployment" style={styles.section}>
          <h1 style={styles.h1}>🚀 Deployment & Configuration</h1>
          
          {/* Configuration */}
          <div style={styles.configSection}>
            <h2 style={styles.subsectionTitle}>🔧 Configuration</h2>
            
            <div style={styles.configGrid}>
              <div style={styles.configCard}>
                <h4 style={styles.configTitle}>Backend (.env)</h4>
                <div style={styles.codeBlock}>
                  <pre style={styles.code}>
{`# Required
OPENAI_API_KEY=sk-your-key
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io  # Aura
# NEO4J_URI=bolt://localhost:7687  # Local Docker
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Optional
API_HOST=0.0.0.0
API_PORT=8000
RAG_EMBEDDING_BACKEND=sentence-transformers
SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5`}
                  </pre>
                </div>
              </div>

              <div style={styles.configCard}>
                <h4 style={styles.configTitle}>Frontend (frontend/.env.local)</h4>
                <div style={styles.codeBlock}>
                  <pre style={styles.code}>
{`# Local development
VITE_API_BASE_URL=http://localhost:8000

# Remote server
VITE_API_BASE_URL=http://YOUR_SERVER_PUBLIC_IP:8000`}
                  </pre>
                </div>
              </div>
            </div>
          </div>

          {/* Deployment Options */}
          <h2 style={{...styles.subsectionTitle, marginTop: '48px'}}>Deployment Options</h2>
          
          <div style={styles.deploymentGrid}>
            <div style={styles.deploymentCard}>
              <div style={styles.deploymentIcon}>🐳</div>
              <h3 style={styles.deploymentTitle}>Local Development</h3>
              <p style={styles.deploymentDesc}>Docker Compose with all services</p>
              <div style={styles.codeBlock}>
                <pre style={styles.code}>
{`# Start all services
docker-compose up -d
python api.py
cd frontend && npm run dev

# Access
http://localhost:5173  # Frontend
http://localhost:8000  # API
http://localhost:7474  # Neo4j Browser`}
                </pre>
              </div>
            </div>

            <div style={styles.deploymentCard}>
              <div style={styles.deploymentIcon}>☁️</div>
              <h3 style={styles.deploymentTitle}>Neo4j Aura</h3>
              <p style={styles.deploymentDesc}>Managed cloud database</p>
              <div style={styles.codeBlock}>
                <pre style={styles.code}>
{`# .env configuration
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Enable GDS (Graph Data Science)
# Contact Aura support for GDS access
# Required for community detection features`}
                </pre>
              </div>
            </div>

            <div style={styles.deploymentCard}>
              <div style={styles.deploymentIcon}>🖥️</div>
              <h3 style={styles.deploymentTitle}>Remote Server</h3>
              <p style={styles.deploymentDesc}>Deploy on VM or cloud instance</p>
              <div style={styles.codeBlock}>
                <pre style={styles.code}>
{`# On your server
./start_all.sh

# Configure firewall
sudo ufw allow 8000/tcp  # API
sudo ufw allow 5173/tcp  # Frontend
sudo ufw allow 7474/tcp  # Neo4j Browser
sudo ufw allow 7687/tcp  # Neo4j Bolt

# Access from local browser
http://YOUR_SERVER_PUBLIC_IP:5173`}
                </pre>
              </div>
            </div>
          </div>
        </section>

        {/* Quick Start Section */}
        <section id="quickstart" style={styles.section}>
          <h1 style={styles.h1}>⚡ Quick Start Guide (5 Minutes)</h1>
          
          <div style={styles.quickstartSteps}>
            <div style={styles.quickstartStep}>
              <div style={styles.quickstartNumber}>1</div>
              <div style={styles.quickstartContent}>
                <h3 style={styles.quickstartTitle}>Prerequisites</h3>
                <ul style={styles.quickstartList}>
                  <li>Python 3.11+</li>
                  <li>Node.js 18+ (for frontend)</li>
                  <li>Neo4j (Docker or Aura cloud)</li>
                  <li>OpenAI API key</li>
                </ul>
              </div>
            </div>

            <div style={styles.quickstartStep}>
              <div style={styles.quickstartNumber}>2</div>
              <div style={styles.quickstartContent}>
                <h3 style={styles.quickstartTitle}>Install & Setup</h3>
                <div style={styles.codeBlock}>
                  <pre style={styles.code}>
{`# Install dependencies
pip install -r requirements.txt

# Configure environment
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-openai-api-key
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io  # or bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
API_HOST=0.0.0.0
API_PORT=8000
RAG_EMBEDDING_BACKEND=sentence-transformers
SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5
EOF

# Start Neo4j (if using Docker)
docker-compose up -d`}
                  </pre>
                </div>
              </div>
            </div>

            <div style={styles.quickstartStep}>
              <div style={styles.quickstartNumber}>3</div>
              <div style={styles.quickstartContent}>
                <h3 style={styles.quickstartTitle}>Run Pipeline</h3>
                <div style={styles.codeBlock}>
                  <pre style={styles.code}>
{`# Build knowledge graph (embeddings generated automatically!)
python pipeline.py \\
  --scrape-category startups \\
  --scrape-max-pages 2 \\
  --max-articles 10`}
                  </pre>
                </div>
                <p style={styles.quickstartNote}>
                  This automatically runs all phases:<br/>
                  <strong>1.</strong> Web Scraping - TechCrunch article extraction<br/>
                  <strong>2.</strong> Entity Extraction - GPT-4o NER and relationships<br/>
                  <strong>3.</strong> Company Intelligence Enrichment - Deep company data via Playwright<br/>
                  <strong>4.</strong> Graph Construction - Build Neo4j knowledge graph<br/>
                  <strong>5.</strong> Post-Processing - Embeddings, deduplication, communities
                </p>
              </div>
            </div>

            <div style={styles.quickstartStep}>
              <div style={styles.quickstartNumber}>4</div>
              <div style={styles.quickstartContent}>
                <h3 style={styles.quickstartTitle}>Start Services</h3>
                <div style={styles.codeBlock}>
                  <pre style={styles.code}>
{`# Start everything
./start_all.sh

# Access from local machine: http://YOUR_VM_IP:5173
# Access locally: http://localhost:5173`}
                  </pre>
                </div>
              </div>
            </div>
          </div>

          <div style={{...styles.infoBox, backgroundColor: '#dcfce7', borderColor: '#86efac'}}>
            <div style={styles.infoIcon}>🎉</div>
            <div>
              <strong>You're all set!</strong> The application is now running. 
              Try asking questions like "Which AI startups raised funding?" or 
              "Show me companies founded by former Google employees."
            </div>
          </div>

          {/* Additional Commands */}
          <div style={styles.commandsSection}>
            <h2 style={styles.subsectionTitle}>📋 Common Commands</h2>
            
            <div style={styles.commandGrid}>
              <div style={styles.commandCard}>
                <h4 style={styles.commandTitle}>Pipeline Options</h4>
                <div style={styles.codeBlock}>
                  <pre style={styles.code}>
{`# Full pipeline (automatic embeddings!)
python pipeline.py --scrape-category startups --scrape-max-pages 2 --max-articles 10

# Use existing articles
python pipeline.py --skip-scraping --max-articles 50

# Use existing extractions
python pipeline.py --skip-scraping --skip-extraction`}
                  </pre>
                </div>
              </div>

              <div style={styles.commandCard}>
                <h4 style={styles.commandTitle}>Service Management</h4>
                <div style={styles.codeBlock}>
                  <pre style={styles.code}>
{`# Start all (API + Frontend in tmux)
./start_all.sh

# Start API only
python api.py

# Start frontend only
cd frontend && npm run dev

# Stop all
tmux kill-session -t graphrag`}
                  </pre>
                </div>
              </div>

              <div style={styles.commandCard}>
                <h4 style={styles.commandTitle}>Query Methods</h4>
                <div style={styles.codeBlock}>
                  <pre style={styles.code}>
{`# Via React UI
open http://localhost:5173

# Via API docs
open http://localhost:8000/docs

# Via Python
python -c "from rag_query import create_rag_query; rag = create_rag_query(); print(rag.query('Which AI startups raised funding?')['answer']); rag.close()"

# Via cURL
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question": "Which AI startups raised funding?", "use_llm": true}'`}
                  </pre>
                </div>
              </div>
            </div>
          </div>

          {/* Troubleshooting */}
          <div style={styles.troubleshootingSection}>
            <h2 style={styles.subsectionTitle}>🐛 Troubleshooting</h2>
            
            <div style={styles.troubleshootingGrid}>
              <div style={styles.troubleshootingCard}>
                <h4 style={styles.troubleshootingTitle}>❌ Queries Return "No Relevant Context"</h4>
                <div style={styles.codeBlock}>
                  <pre style={styles.code}>
{`# Check embeddings
python -c "from neo4j import GraphDatabase; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); result = driver.session().run('MATCH (n) WHERE n.embedding IS NOT NULL RETURN count(n) as count'); print(f'Embeddings: {result.single()[\"count\"]}'); driver.close()"

# Generate embeddings if needed
python -c "from neo4j import GraphDatabase; from utils.embedding_generator import EmbeddingGenerator; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); gen = EmbeddingGenerator(driver, 'sentence-transformers'); gen.generate_embeddings_for_all_entities(); driver.close()"`}
                  </pre>
                </div>
              </div>

              <div style={styles.troubleshootingCard}>
                <h4 style={styles.troubleshootingTitle}>❌ Neo4j Connection Failed</h4>
                <div style={styles.codeBlock}>
                  <pre style={styles.code}>
{`# Check Neo4j
docker ps | grep neo4j

# Start Neo4j
docker-compose up -d

# Test connection
python -c "from neo4j import GraphDatabase; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); driver.verify_connectivity(); print('✓ Connected'); driver.close()"`}
                  </pre>
                </div>
              </div>

              <div style={styles.troubleshootingCard}>
                <h4 style={styles.troubleshootingTitle}>❌ Frontend Not Accessible</h4>
                <div style={styles.codeBlock}>
                  <pre style={styles.code}>
{`# Check services
sudo netstat -tulpn | grep -E '8000|5173'

# Check firewall
sudo ufw status | grep -E '8000|5173'

# Add firewall rules
sudo ufw allow 8000/tcp
sudo ufw allow 5173/tcp`}
                  </pre>
                </div>
              </div>

              <div style={styles.troubleshootingCard}>
                <h4 style={styles.troubleshootingTitle}>❌ Chat Not Working</h4>
                <div style={styles.codeBlock}>
                  <pre style={styles.code}>
{`# Hard refresh browser: Ctrl + Shift + R
# Check browser console (F12) for errors
# Verify API: curl http://YOUR_VM_IP:8000/health`}
                  </pre>
                </div>
              </div>

              <div style={styles.troubleshootingCard}>
                <h4 style={styles.troubleshootingTitle}>❌ Port Already in Use</h4>
                <div style={styles.codeBlock}>
                  <pre style={styles.code}>
{`# Kill existing services
tmux kill-session -t graphrag

# Restart
./start_all.sh`}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Technology Stack Section */}
        <section id="tech-stack" style={styles.section}>
          <h1 style={styles.h1}>🛠️ Technology Stack</h1>
          
          <div style={styles.techStackSection}>
            <div style={styles.techCategory}>
              <h3 style={styles.techCategoryTitle}>Backend & API</h3>
              <div style={styles.techGrid}>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>🐍</div>
                  <div style={styles.techItemName}>Python 3.11+</div>
                  <div style={styles.techItemDesc}>Core language</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>⚡</div>
                  <div style={styles.techItemName}>FastAPI</div>
                  <div style={styles.techItemDesc}>REST API framework</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>🦄</div>
                  <div style={styles.techItemName}>Uvicorn</div>
                  <div style={styles.techItemDesc}>ASGI server</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>✅</div>
                  <div style={styles.techItemName}>Pydantic</div>
                  <div style={styles.techItemDesc}>Data validation</div>
                </div>
              </div>
            </div>

            <div style={styles.techCategory}>
              <h3 style={styles.techCategoryTitle}>AI & NLP</h3>
              <div style={styles.techGrid}>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>🤖</div>
                  <div style={styles.techItemName}>GPT-4o</div>
                  <div style={styles.techItemDesc}>Entity extraction</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>🔗</div>
                  <div style={styles.techItemName}>LangChain</div>
                  <div style={styles.techItemDesc}>LLM orchestration</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>🔢</div>
                  <div style={styles.techItemName}>Sentence Transformers</div>
                  <div style={styles.techItemDesc}>BAAI/bge-small-en-v1.5</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>📊</div>
                  <div style={styles.techItemName}>NumPy</div>
                  <div style={styles.techItemDesc}>Vector operations</div>
                </div>
              </div>
            </div>

            <div style={styles.techCategory}>
              <h3 style={styles.techCategoryTitle}>Database & Graph</h3>
              <div style={styles.techGrid}>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>🗄️</div>
                  <div style={styles.techItemName}>Neo4j Aura</div>
                  <div style={styles.techItemDesc}>Cloud graph database</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>📈</div>
                  <div style={styles.techItemName}>Graph Data Science</div>
                  <div style={styles.techItemDesc}>Community detection</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>🕸️</div>
                  <div style={styles.techItemName}>NetworkX</div>
                  <div style={styles.techItemDesc}>Graph algorithms</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>🔌</div>
                  <div style={styles.techItemName}>Neo4j Driver 5.0+</div>
                  <div style={styles.techItemDesc}>Python client</div>
                </div>
              </div>
            </div>

            <div style={styles.techCategory}>
              <h3 style={styles.techCategoryTitle}>Web Scraping</h3>
              <div style={styles.techGrid}>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>🕷️</div>
                  <div style={styles.techItemName}>Crawl4AI</div>
                  <div style={styles.techItemDesc}>Article extraction</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>🎭</div>
                  <div style={styles.techItemName}>Playwright</div>
                  <div style={styles.techItemDesc}>Company intelligence</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>🥣</div>
                  <div style={styles.techItemName}>BeautifulSoup4</div>
                  <div style={styles.techItemDesc}>HTML parsing</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>📄</div>
                  <div style={styles.techItemName}>lxml</div>
                  <div style={styles.techItemDesc}>XML processing</div>
                </div>
              </div>
            </div>

            <div style={styles.techCategory}>
              <h3 style={styles.techCategoryTitle}>Frontend</h3>
              <div style={styles.techGrid}>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>⚛️</div>
                  <div style={styles.techItemName}>React 18</div>
                  <div style={styles.techItemDesc}>UI framework</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>📘</div>
                  <div style={styles.techItemName}>TypeScript</div>
                  <div style={styles.techItemDesc}>Type safety</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>⚡</div>
                  <div style={styles.techItemName}>Vite</div>
                  <div style={styles.techItemDesc}>Build tool</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>📝</div>
                  <div style={styles.techItemName}>React Markdown</div>
                  <div style={styles.techItemDesc}>Content rendering</div>
                </div>
              </div>
            </div>

            <div style={styles.techCategory}>
              <h3 style={styles.techCategoryTitle}>DevOps & Utilities</h3>
              <div style={styles.techGrid}>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>🐳</div>
                  <div style={styles.techItemName}>Docker</div>
                  <div style={styles.techItemDesc}>Containerization</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>🔧</div>
                  <div style={styles.techItemName}>Docker Compose</div>
                  <div style={styles.techItemDesc}>Multi-container</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>💻</div>
                  <div style={styles.techItemName}>tmux</div>
                  <div style={styles.techItemDesc}>Session management</div>
                </div>
                <div style={styles.techItem}>
                  <div style={styles.techItemIcon}>🔐</div>
                  <div style={styles.techItemName}>python-dotenv</div>
                  <div style={styles.techItemDesc}>Environment config</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer style={styles.footer}>
          <div style={styles.footerContent}>
            <div style={styles.footerSection}>
              <h4 style={styles.footerTitle}>Project Info</h4>
              <div style={styles.projectInfo}>
                <div style={styles.projectInfoItem}>📦 40+ API Endpoints</div>
                <div style={styles.projectInfoItem}>🗄️ Neo4j Aura Cloud</div>
                <div style={styles.projectInfoItem}>🤖 GPT-4o Powered</div>
                <div style={styles.projectInfoItem}>⚡ Production Ready</div>
              </div>
            </div>
            <div style={styles.footerSection}>
              <h4 style={styles.footerTitle}>Key Technologies</h4>
              <div style={styles.techStack}>
                <span style={styles.techBadge}>Python 3.11</span>
                <span style={styles.techBadge}>Neo4j Aura</span>
                <span style={styles.techBadge}>FastAPI</span>
                <span style={styles.techBadge}>React 18</span>
                <span style={styles.techBadge}>GPT-4o</span>
                <span style={styles.techBadge}>LangChain</span>
                <span style={styles.techBadge}>Sentence Transformers</span>
                <span style={styles.techBadge}>Playwright</span>
              </div>
            </div>
          </div>
          <div style={styles.footerBottom}>
            🚀 Startup Intelligence Analysis Platform • Built with ❤️ for intelligent startup analysis
          </div>
        </footer>
      </main>
    </div>
  );
};

// Styles
const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: 'flex',
    minHeight: '100vh',
    backgroundColor: '#0f172a',
  },
  sidebar: {
    width: '280px',
    backgroundColor: '#1e293b',
    borderRight: '1px solid rgba(51, 65, 85, 0.5)',
    position: 'sticky' as const,
    top: 0,
    height: '100vh',
    overflowY: 'auto' as const,
    flexShrink: 0,
  },
  sidebarHeader: {
    padding: '24px 20px',
    borderBottom: '1px solid rgba(51, 65, 85, 0.5)',
  },
  sidebarTitle: {
    margin: 0,
    fontSize: '20px',
    fontWeight: 700,
    color: '#f1f5f9',
  },
  nav: {
    padding: '16px 8px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '4px',
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    border: 'none',
    backgroundColor: 'transparent',
    color: '#cbd5e1',
    fontSize: '15px',
    fontWeight: 500,
    cursor: 'pointer',
    borderRadius: '8px',
    transition: 'all 0.2s',
    textAlign: 'left' as const,
  },
  navItemActive: {
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    color: '#60a5fa',
    fontWeight: 600,
  },
  navIcon: {
    fontSize: '18px',
  },
  content: {
    flex: 1,
    padding: '40px 60px',
    maxWidth: '1400px',
    margin: '0 auto',
    width: '100%',
  },
  section: {
    marginBottom: '80px',
  },
  h1: {
    fontSize: '36px',
    fontWeight: 700,
    color: '#f1f5f9',
    marginBottom: '16px',
    marginTop: 0,
  },
  lead: {
    fontSize: '18px',
    color: '#cbd5e1',
    lineHeight: 1.7,
    marginBottom: '40px',
  },
  featureGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '24px',
    marginTop: '32px',
  },
  featureCard: {
    backgroundColor: '#1e293b',
    padding: '28px',
    borderRadius: '12px',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    transition: 'all 0.3s',
    cursor: 'default',
  },
  featureIcon: {
    fontSize: '40px',
    marginBottom: '16px',
  },
  featureTitle: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginBottom: '8px',
    marginTop: 0,
  },
  featureDesc: {
    fontSize: '14px',
    color: '#cbd5e1',
    lineHeight: 1.6,
    margin: 0,
  },
  diagramCard: {
    backgroundColor: '#1e293b',
    padding: '32px',
    borderRadius: '12px',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    marginBottom: '24px',
  },
  diagramTitle: {
    fontSize: '20px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginTop: 0,
    marginBottom: '28px',
  },
  architectureDiagram: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '16px',
  },
  architectureLayer: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
  },
  layerTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#cbd5e1',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  componentRow: {
    display: 'flex',
    gap: '16px',
    justifyContent: 'space-between',
  },
  component: {
    flex: 1,
    padding: '20px',
    borderRadius: '8px',
    border: '2px solid',
    textAlign: 'center' as const,
  },
  componentReact: {
    borderColor: '#61dafb',
    backgroundColor: '#f0fdff',
  },
  componentApi: {
    borderColor: '#10b981',
    backgroundColor: '#f0fdf4',
  },
  componentProcess: {
    borderColor: '#8b5cf6',
    backgroundColor: '#faf5ff',
  },
  componentData: {
    borderColor: '#f59e0b',
    backgroundColor: '#fffbeb',
  },
  componentIcon: {
    fontSize: '28px',
    marginBottom: '8px',
  },
  componentName: {
    fontSize: '15px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginBottom: '4px',
  },
  componentDesc: {
    fontSize: '12px',
    color: '#cbd5e1',
  },
  arrow: {
    textAlign: 'center' as const,
    fontSize: '24px',
    color: '#cbd5e1',
    fontWeight: 'bold',
  },
  pipelineFlow: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    overflowX: 'auto' as const,
    padding: '8px 0',
  },
  pipelineStep: {
    minWidth: '180px',
    padding: '20px',
    backgroundColor: '#1e293b',
    borderRadius: '8px',
    border: '2px solid',
    textAlign: 'center' as const,
  },
  pipelinePhase: {
    display: 'inline-block',
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '11px',
    fontWeight: 700,
    color: '#ffffff',
    marginBottom: '12px',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  pipelineIcon: {
    fontSize: '32px',
    marginBottom: '8px',
  },
  pipelineTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginBottom: '6px',
  },
  pipelineDesc: {
    fontSize: '12px',
    color: '#cbd5e1',
    lineHeight: 1.4,
    marginBottom: '8px',
  },
  pipelineTech: {
    fontSize: '10px',
    color: '#cbd5e1',
    fontFamily: 'monospace',
    fontStyle: 'italic' as const,
  },
  pipelineArrow: {
    fontSize: '24px',
    color: '#cbd5e1',
    fontWeight: 'bold',
    flexShrink: 0,
  },
  queryFlow: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '16px',
  },
  queryStep: {
    display: 'flex',
    gap: '20px',
    alignItems: 'flex-start',
  },
  queryStepNumber: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    backgroundColor: '#3b82f6',
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '18px',
    fontWeight: 700,
    flexShrink: 0,
  },
  queryStepContent: {
    flex: 1,
  },
  queryStepTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginBottom: '6px',
  },
  queryStepDesc: {
    fontSize: '14px',
    color: '#cbd5e1',
    marginBottom: '12px',
  },
  queryExample: {
    padding: '12px 16px',
    backgroundColor: '#334155',
    borderLeft: '3px solid #3b82f6',
    borderRadius: '4px',
    fontSize: '14px',
    color: '#cbd5e1',
    fontStyle: 'italic' as const,
  },
  queryTypes: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap' as const,
  },
  queryType: {
    padding: '6px 12px',
    backgroundColor: '#e0f2fe',
    color: '#0369a1',
    borderRadius: '6px',
    fontSize: '12px',
    fontWeight: 600,
  },
  searchMethods: {
    display: 'flex',
    gap: '16px',
    marginTop: '8px',
  },
  searchMethod: {
    flex: 1,
    padding: '12px',
    backgroundColor: '#334155',
    borderRadius: '6px',
    textAlign: 'center' as const,
    fontSize: '13px',
    color: '#cbd5e1',
    fontWeight: 500,
  },
  searchIcon: {
    fontSize: '20px',
    marginBottom: '4px',
  },
  contextBox: {
    padding: '16px',
    backgroundColor: '#fef3c7',
    borderRadius: '6px',
    marginTop: '8px',
  },
  contextItem: {
    fontSize: '13px',
    color: '#78350f',
    marginBottom: '4px',
  },
  answerBox: {
    padding: '16px',
    backgroundColor: '#dcfce7',
    borderRadius: '6px',
    fontSize: '14px',
    color: '#14532d',
    lineHeight: 1.6,
    marginTop: '8px',
  },
  queryArrow: {
    textAlign: 'center' as const,
    fontSize: '24px',
    color: '#cbd5e1',
    fontWeight: 'bold',
    marginLeft: '20px',
  },
  entityDiagram: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '24px',
  },
  entityGroup: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
  },
  entityGroupTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#cbd5e1',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  entityRow: {
    display: 'flex',
    gap: '12px',
    flexWrap: 'wrap' as const,
  },
  entity: {
    flex: '1 1 150px',
    padding: '16px',
    borderRadius: '8px',
    border: '2px solid',
    textAlign: 'center' as const,
  },
  entityCompany: {
    borderColor: '#3b82f6',
    backgroundColor: '#eff6ff',
  },
  entityPerson: {
    borderColor: '#8b5cf6',
    backgroundColor: '#faf5ff',
  },
  entityInvestor: {
    borderColor: '#10b981',
    backgroundColor: '#f0fdf4',
  },
  entityTech: {
    borderColor: '#f59e0b',
    backgroundColor: '#fffbeb',
  },
  entityProduct: {
    borderColor: '#ec4899',
    backgroundColor: '#fdf2f8',
  },
  entityFunding: {
    borderColor: '#06b6d4',
    backgroundColor: '#f0fdfa',
  },
  entityLocation: {
    borderColor: '#ef4444',
    backgroundColor: '#fef2f2',
  },
  entityEvent: {
    borderColor: '#6366f1',
    backgroundColor: '#eef2ff',
  },
  entityIcon: {
    fontSize: '24px',
    marginBottom: '8px',
  },
  entityName: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginBottom: '4px',
  },
  entityProps: {
    fontSize: '11px',
    color: '#cbd5e1',
  },
  relationshipLines: {
    margin: '0 auto',
    width: '100%',
    maxWidth: '600px',
  },
  subsectionTitle: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginBottom: '16px',
    marginTop: '32px',
  },
  relationshipGrid: {
    marginTop: '32px',
  },
  relationshipList: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '8px',
  },
  relationshipBadge: {
    padding: '8px 14px',
    backgroundColor: '#334155',
    color: '#cbd5e1',
    borderRadius: '6px',
    fontSize: '12px',
    fontWeight: 600,
    fontFamily: 'monospace',
  },
  codeBlock: {
    backgroundColor: '#1e293b',
    borderRadius: '8px',
    overflow: 'hidden',
    marginTop: '16px',
  },
  codeHeader: {
    padding: '12px 16px',
    backgroundColor: '#0f172a',
    borderBottom: '1px solid #334155',
  },
  codeTitle: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#cbd5e1',
  },
  code: {
    margin: 0,
    padding: '20px',
    color: '#e2e8f0',
    fontSize: '13px',
    lineHeight: 1.6,
    fontFamily: 'Monaco, Consolas, monospace',
    overflow: 'auto' as const,
  },
  infoBox: {
    display: 'flex',
    gap: '16px',
    padding: '16px 20px',
    backgroundColor: '#dbeafe',
    border: '1px solid #93c5fd',
    borderRadius: '8px',
    marginTop: '24px',
    fontSize: '14px',
    color: '#1e3a8a',
    lineHeight: 1.6,
  },
  infoIcon: {
    fontSize: '20px',
    flexShrink: 0,
  },
  link: {
    color: '#2563eb',
    textDecoration: 'none',
    fontWeight: 600,
  },
  quickLinksSection: {
    marginTop: '48px',
  },
  quickLinksGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginTop: '20px',
  },
  quickLinkCard: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    padding: '24px',
    backgroundColor: '#1e293b',
    borderRadius: '12px',
    border: '2px solid #e2e8f0',
    textDecoration: 'none',
    transition: 'all 0.3s',
    cursor: 'pointer',
  },
  quickLinkIcon: {
    fontSize: '32px',
    marginBottom: '12px',
  },
  quickLinkTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginBottom: '6px',
  },
  quickLinkUrl: {
    fontSize: '12px',
    color: '#cbd5e1',
    fontFamily: 'monospace',
  },
  apiGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
    gap: '24px',
  },
  apiCard: {
    backgroundColor: '#1e293b',
    padding: '24px',
    borderRadius: '12px',
    border: '1px solid rgba(51, 65, 85, 0.5)',
  },
  apiMethod: {
    display: 'inline-block',
    padding: '4px 10px',
    backgroundColor: '#10b981',
    color: '#ffffff',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 700,
    marginBottom: '12px',
  },
  apiEndpoint: {
    fontSize: '16px',
    fontWeight: 600,
    color: '#f1f5f9',
    fontFamily: 'monospace',
    marginBottom: '8px',
  },
  apiDesc: {
    fontSize: '14px',
    color: '#cbd5e1',
    marginBottom: '16px',
  },
  configSection: {
    marginBottom: '32px',
  },
  configGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
    gap: '24px',
    marginTop: '20px',
  },
  configCard: {
    backgroundColor: '#1e293b',
    padding: '24px',
    borderRadius: '12px',
    border: '1px solid rgba(51, 65, 85, 0.5)',
  },
  configTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginTop: 0,
    marginBottom: '16px',
  },
  deploymentGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
    gap: '24px',
  },
  deploymentCard: {
    backgroundColor: '#1e293b',
    padding: '28px',
    borderRadius: '12px',
    border: '1px solid rgba(51, 65, 85, 0.5)',
  },
  deploymentIcon: {
    fontSize: '48px',
    marginBottom: '16px',
  },
  deploymentTitle: {
    fontSize: '20px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginBottom: '8px',
    marginTop: 0,
  },
  deploymentDesc: {
    fontSize: '14px',
    color: '#cbd5e1',
    marginBottom: '20px',
  },
  quickstartSteps: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '32px',
  },
  quickstartStep: {
    display: 'flex',
    gap: '24px',
    alignItems: 'flex-start',
  },
  quickstartNumber: {
    width: '48px',
    height: '48px',
    borderRadius: '50%',
    backgroundColor: '#3b82f6',
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '20px',
    fontWeight: 700,
    flexShrink: 0,
  },
  quickstartContent: {
    flex: 1,
  },
  quickstartTitle: {
    fontSize: '20px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginTop: 0,
    marginBottom: '12px',
  },
  quickstartList: {
    margin: 0,
    paddingLeft: '20px',
    color: '#cbd5e1',
    fontSize: '15px',
    lineHeight: 1.8,
  },
  quickstartNote: {
    marginTop: '12px',
    fontSize: '14px',
    color: '#cbd5e1',
    lineHeight: 1.7,
    padding: '12px 16px',
    backgroundColor: '#334155',
    borderRadius: '6px',
    borderLeft: '3px solid #3b82f6',
  },
  commandsSection: {
    marginTop: '48px',
  },
  commandGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
    gap: '24px',
    marginTop: '20px',
  },
  commandCard: {
    backgroundColor: '#1e293b',
    padding: '24px',
    borderRadius: '12px',
    border: '1px solid rgba(51, 65, 85, 0.5)',
  },
  commandTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginTop: 0,
    marginBottom: '16px',
  },
  troubleshootingSection: {
    marginTop: '48px',
  },
  troubleshootingGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))',
    gap: '24px',
    marginTop: '20px',
  },
  troubleshootingCard: {
    backgroundColor: '#1e293b',
    padding: '24px',
    borderRadius: '12px',
    border: '1px solid rgba(51, 65, 85, 0.5)',
  },
  troubleshootingTitle: {
    fontSize: '15px',
    fontWeight: 600,
    color: '#dc2626',
    marginTop: 0,
    marginBottom: '16px',
  },
  footer: {
    marginTop: '80px',
    padding: '40px 0',
    borderTop: '1px solid #e2e8f0',
  },
  footerContent: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '32px',
    marginBottom: '24px',
  },
  footerSection: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
  },
  footerTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#f1f5f9',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
    marginTop: 0,
    marginBottom: 0,
  },
  footerLinks: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
  },
  footerLink: {
    color: '#3b82f6',
    textDecoration: 'none',
    fontSize: '14px',
    fontWeight: 500,
  },
  techStack: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '8px',
  },
  techBadge: {
    padding: '6px 12px',
    backgroundColor: '#334155',
    color: '#cbd5e1',
    borderRadius: '6px',
    fontSize: '12px',
    fontWeight: 600,
  },
  footerBottom: {
    textAlign: 'center' as const,
    color: '#cbd5e1',
    fontSize: '14px',
    paddingTop: '24px',
    borderTop: '1px solid #f1f5f9',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '20px',
    marginTop: '32px',
    marginBottom: '32px',
  },
  statCard: {
    backgroundColor: '#1e293b',
    padding: '24px',
    borderRadius: '12px',
    border: '2px solid #e2e8f0',
    textAlign: 'center' as const,
  },
  statNumber: {
    fontSize: '36px',
    fontWeight: 700,
    color: '#3b82f6',
    marginBottom: '8px',
  },
  statLabel: {
    fontSize: '14px',
    color: '#cbd5e1',
    fontWeight: 500,
  },
  techStackSection: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '32px',
  },
  techCategory: {
    backgroundColor: '#1e293b',
    padding: '28px',
    borderRadius: '12px',
    border: '1px solid rgba(51, 65, 85, 0.5)',
  },
  techCategoryTitle: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginTop: 0,
    marginBottom: '20px',
  },
  techGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
  },
  techItem: {
    padding: '16px',
    backgroundColor: '#334155',
    borderRadius: '8px',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    textAlign: 'center' as const,
  },
  techItemIcon: {
    fontSize: '24px',
    marginBottom: '8px',
  },
  techItemName: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginBottom: '4px',
  },
  techItemDesc: {
    fontSize: '12px',
    color: '#cbd5e1',
  },
  projectInfo: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
  },
  projectInfoItem: {
    fontSize: '14px',
    color: '#cbd5e1',
    fontWeight: 500,
  },
  utilitySection: {
    marginTop: '48px',
  },
  utilityGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '16px',
    marginTop: '20px',
  },
  utilityCard: {
    backgroundColor: '#1e293b',
    padding: '20px',
    borderRadius: '8px',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    textAlign: 'center' as const,
  },
  utilityIcon: {
    fontSize: '28px',
    marginBottom: '12px',
  },
  utilityTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginTop: 0,
    marginBottom: '8px',
    fontFamily: 'monospace',
  },
  utilityDesc: {
    fontSize: '12px',
    color: '#cbd5e1',
    lineHeight: 1.5,
    margin: 0,
  },
  entityPropertiesSection: {
    marginTop: '32px',
  },
  propertiesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '20px',
    marginTop: '20px',
  },
  propertyCard: {
    backgroundColor: '#1e293b',
    padding: '24px',
    borderRadius: '12px',
    border: '1px solid rgba(51, 65, 85, 0.5)',
  },
  propertyTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: '#f1f5f9',
    marginTop: 0,
    marginBottom: '12px',
  },
  propertyList: {
    margin: 0,
    paddingLeft: '20px',
    fontSize: '13px',
    color: '#cbd5e1',
    lineHeight: 1.8,
  },
};

export default DocumentationPage;
