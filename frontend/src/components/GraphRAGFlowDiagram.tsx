import React, { useEffect } from 'react';

const GraphRAGFlowDiagram: React.FC = () => {
  useEffect(() => {
    // Create animated particles
    for (let i = 0; i < 20; i++) {
      const particle = document.createElement('div');
      particle.className = 'particle';
      particle.style.left = Math.random() * 100 + '%';
      particle.style.top = Math.random() * 100 + '%';
      particle.style.animationDelay = Math.random() * 20 + 's';
      document.body.appendChild(particle);
    }

    return () => {
      // Cleanup particles on unmount
      const particles = document.querySelectorAll('.particle');
      particles.forEach(p => p.remove());
    };
  }, []);

  return (
    <>
      <style>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        .flow-container {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
          background: transparent;
          padding: 20px 0;
          overflow-x: hidden;
        }

        .flow-wrapper {
          max-width: 1600px;
          margin: 0 auto;
          display: flex;
          gap: 25px;
          flex-wrap: wrap;
          justify-content: center;
          position: relative;
        }

        /* Animated background particles */
        .particle {
          position: fixed;
          width: 4px;
          height: 4px;
          background: rgba(96, 165, 250, 0.5);
          border-radius: 50%;
          pointer-events: none;
          animation: float 20s infinite ease-in-out;
          z-index: 0;
        }

        @keyframes float {
          0%, 100% {
            transform: translate(0, 0) scale(1);
            opacity: 0;
          }
          10% {
            opacity: 1;
          }
          90% {
            opacity: 1;
          }
          50% {
            transform: translate(100px, -100px) scale(1.5);
          }
        }

        .flow-section {
          border: 3px solid;
          border-radius: 20px;
          padding: 25px;
          background: rgba(30, 41, 59, 0.6);
          backdrop-filter: blur(10px);
          position: relative;
          min-width: 320px;
          max-width: 400px;
          animation: fadeInUp 0.8s ease-out backwards;
          transition: all 0.3s ease;
          z-index: 1;
        }

        .flow-section:hover {
          transform: translateY(-5px);
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        }

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .flow-section:nth-child(1) { animation-delay: 0.1s; }
        .flow-section:nth-child(2) { animation-delay: 0.2s; }
        .flow-section:nth-child(3) { animation-delay: 0.3s; }
        .flow-section:nth-child(4) { animation-delay: 0.4s; }

        .flow-section.cyan {
          border-color: #06b6d4;
          background: rgba(8, 145, 178, 0.1);
          box-shadow: 0 0 30px rgba(6, 182, 212, 0.2);
        }

        .flow-section.green {
          border-color: #10b981;
          background: rgba(16, 185, 129, 0.1);
          box-shadow: 0 0 30px rgba(16, 185, 129, 0.2);
        }

        .flow-section.purple {
          border-color: #a855f7;
          background: rgba(168, 85, 247, 0.1);
          box-shadow: 0 0 30px rgba(168, 85, 247, 0.2);
        }

        .flow-section.blue {
          border-color: #3b82f6;
          background: rgba(59, 130, 246, 0.1);
          box-shadow: 0 0 30px rgba(59, 130, 246, 0.2);
        }

        .flow-section-header {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 700;
          font-size: 0.8em;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 20px;
          color: #e2e8f0;
          animation: glow 2s ease-in-out infinite;
        }

        @keyframes glow {
          0%, 100% { text-shadow: 0 0 5px rgba(96, 165, 250, 0.5); }
          50% { text-shadow: 0 0 20px rgba(96, 165, 250, 0.8); }
        }

        .flow-node {
          border-radius: 12px;
          padding: 18px 20px;
          margin: 15px 0;
          font-size: 0.95em;
          font-weight: 600;
          text-align: center;
          position: relative;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          transition: all 0.3s ease;
          animation: slideIn 0.6s ease-out backwards;
          cursor: pointer;
        }

        .flow-function-annotation {
          font-size: 0.65em;
          color: #94a3b8;
          font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
          margin-top: 6px;
          font-weight: 400;
          opacity: 0.8;
          line-height: 1.3;
        }

        .flow-node:hover {
          transform: scale(1.05);
          box-shadow: 0 8px 20px rgba(0,0,0,0.5);
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(-50px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        .flow-node.start {
          background: rgba(59, 130, 246, 0.3);
          border: 2px solid #60a5fa;
          border-radius: 50px;
          color: #bfdbfe;
          animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
          0%, 100% {
            box-shadow: 0 0 10px rgba(96, 165, 250, 0.5);
          }
          50% {
            box-shadow: 0 0 25px rgba(96, 165, 250, 0.8);
          }
        }

        .flow-node.process {
          background: rgba(16, 185, 129, 0.3);
          border: 2px solid #34d399;
          color: #a7f3d0;
        }

        .flow-node.decision {
          background: rgba(249, 115, 22, 0.3);
          border: 2px solid #fb923c;
          clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
          padding: 25px 10px;
          color: #fed7aa;
          animation: rotate 3s ease-in-out infinite;
        }

        @keyframes rotate {
          0%, 100% { transform: rotate(0deg); }
          50% { transform: rotate(5deg); }
        }

        .flow-node.subprocess {
          background: rgba(168, 85, 247, 0.3);
          border: 2px solid #c084fc;
          color: #e9d5ff;
        }

        .flow-node.data {
          background: rgba(6, 182, 212, 0.3);
          border: 2px solid #22d3ee;
          color: #cffafe;
        }

        .flow-node.end {
          background: rgba(236, 72, 153, 0.3);
          border: 2px solid #f472b6;
          border-radius: 50px;
          color: #fbcfe8;
        }

        .flow-node.storage {
          background: rgba(71, 85, 105, 0.3);
          border: 2px solid #94a3b8;
          color: #cbd5e1;
        }

        .flow-arrow {
          display: flex;
          justify-content: center;
          align-items: center;
          margin: 5px 0;
          font-size: 1.5em;
          color: #94a3b8;
          animation: bounce 2s ease-in-out infinite;
        }

        @keyframes bounce {
          0%, 100% {
            transform: translateY(0);
            opacity: 0.5;
          }
          50% {
            transform: translateY(-10px);
            opacity: 1;
          }
        }

        .flow-arrow-text {
          font-size: 0.7em;
          color: #cbd5e1;
          font-weight: 600;
          margin: 0 8px;
          animation: fadeInOut 2s ease-in-out infinite;
        }

        @keyframes fadeInOut {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }

        .flow-icon {
          font-size: 1.1em;
          margin-right: 5px;
          animation: spin 3s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .flow-parallel-container {
          display: flex;
          gap: 15px;
          justify-content: center;
          margin: 15px 0;
          flex-wrap: wrap;
        }

        .flow-parallel-box {
          background: rgba(51, 65, 85, 0.5);
          border: 2px solid #475569;
          border-radius: 10px;
          padding: 15px;
          flex: 1;
          min-width: 140px;
          text-align: center;
          box-shadow: 0 2px 6px rgba(0,0,0,0.3);
          animation: zoomIn 0.8s ease-out backwards;
          transition: all 0.3s ease;
        }

        .flow-parallel-box:hover {
          transform: scale(1.1);
          border-color: #60a5fa;
          box-shadow: 0 5px 15px rgba(96, 165, 250, 0.3);
        }

        @keyframes zoomIn {
          from {
            opacity: 0;
            transform: scale(0.5);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .flow-parallel-box:nth-child(1) { animation-delay: 0.2s; }
        .flow-parallel-box:nth-child(2) { animation-delay: 0.3s; }
        .flow-parallel-box:nth-child(3) { animation-delay: 0.4s; }

        .flow-parallel-box h4 {
          font-size: 0.85em;
          margin-bottom: 10px;
          color: #e2e8f0;
        }

        .flow-parallel-box ul {
          list-style: none;
          font-size: 0.75em;
          color: #cbd5e1;
        }

        .flow-note {
          background: rgba(251, 191, 36, 0.15);
          border-left: 4px solid #fbbf24;
          padding: 12px;
          border-radius: 6px;
          font-size: 0.8em;
          margin: 15px 0;
          color: #fde68a;
          animation: slideInLeft 0.8s ease-out backwards;
        }

        @keyframes slideInLeft {
          from {
            opacity: 0;
            transform: translateX(50px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        .flow-cycle-arrow {
          display: inline-block;
          font-size: 2em;
          color: #f97316;
          animation: rotate360 4s linear infinite;
        }

        @keyframes rotate360 {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .flow-success-check {
          display: inline-block;
          font-size: 1.5em;
          color: #10b981;
          animation: checkmark 1s ease-in-out infinite;
        }

        @keyframes checkmark {
          0%, 100% {
            transform: scale(1);
            opacity: 0.7;
          }
          50% {
            transform: scale(1.2);
            opacity: 1;
          }
        }

        .flow-data-flow {
          position: relative;
          overflow: hidden;
        }

        .flow-data-flow::after {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(96, 165, 250, 0.3), transparent);
          animation: dataFlow 2s linear infinite;
        }

        @keyframes dataFlow {
          0% {
            left: -100%;
          }
          100% {
            left: 100%;
          }
        }

        .flow-footer {
          max-width: 1600px;
          margin: 40px auto 20px;
          text-align: center;
          color: #cbd5e1;
          font-size: 0.9em;
          animation: fadeInOut 3s ease-in-out infinite;
        }

        @media (max-width: 768px) {
          .flow-wrapper {
            flex-direction: column;
          }
          .flow-section {
            max-width: 100%;
          }
        }
      `}</style>
      <div className="flow-container">
        <div className="flow-wrapper">
          {/* Query Initiation Section */}
          <div className="flow-section cyan">
            <div className="flow-section-header">
              <span className="flow-icon">🔍</span>
              QUERY INITIATION
            </div>

            <div className="flow-node start">
              <span className="flow-icon">👤</span>
              User Submits Question
              <div className="flow-function-annotation">api.py: query() endpoint</div>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-node process flow-data-flow">
              <span className="flow-icon">📝</span>
              Parse User Input
              <div className="flow-function-annotation">QueryRequest model validation</div>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-node process flow-data-flow">
              <span className="flow-icon">🧩</span>
              Formulate Structured Query
              <div className="flow-function-annotation">QueryRequest.question</div>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-node decision">
              Query Type?
              <div className="flow-function-annotation">rag_query.py: classify_query_intent()</div>
            </div>

            <div className="flow-arrow">
              <span className="flow-arrow-text">Entity / Relationship / Aggregation</span>
              ↓
            </div>
          </div>

          {/* Knowledge Graph Interaction Section */}
          <div className="flow-section green">
            <div className="flow-section-header">
              <span className="flow-icon">⚙️</span>
              KNOWLEDGE GRAPH INTERACTION
            </div>

            <div className="flow-node data flow-data-flow">
              <span className="flow-icon">📥</span>
              Receive Query
              <div className="flow-function-annotation">rag_query.py: query()</div>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-node decision">
              Check Cache First
              <div className="flow-function-annotation">utils.cache.py: QueryCache.get()</div>
            </div>

            <div className="flow-arrow">
              <span className="flow-arrow-text">Cache Hit</span>
              ↓
            </div>

            <div className="flow-node process">
              <span className="flow-icon">✅</span>
              Return Cached Result
              <div className="flow-function-annotation">Return from cache</div>
            </div>

            <div className="flow-arrow">
              <span className="flow-arrow-text">Cache Miss</span>
              →
            </div>

            <div className="flow-node process">
              <span className="flow-icon">🔎</span>
              Route Query & Retrieve Context
              <div className="flow-function-annotation">rag_query.py: route_query()</div>
            </div>

            <div className="flow-note">
              <strong>Hybrid Search Methods:</strong>
              <div className="flow-parallel-container">
                <div className="flow-parallel-box">
                  <h4>🔢 Vector</h4>
                  <ul>
                    <li>rag_query.py: semantic_search()</li>
                    <li>utils.embedding_generator: find_similar_entities()</li>
                  </ul>
                </div>
                <div className="flow-parallel-box">
                  <h4>🔤 Keyword</h4>
                  <ul>
                    <li>query_templates.py: search_entities_full_text()</li>
                    <li>Neo4j text matching</li>
                  </ul>
                </div>
                <div className="flow-parallel-box">
                  <h4>🕸️ Graph</h4>
                  <ul>
                    <li>query_templates.py: get_entity_relationships()</li>
                    <li>Various QueryTemplates methods</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-node subprocess flow-data-flow">
              <span className="flow-icon">🔗</span>
              Enrich with Article URLs
              <div className="flow-function-annotation">rag_query.py: _enrich_with_article_urls()</div>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-node subprocess flow-data-flow">
              <span className="flow-icon">⚡</span>
              Combine & Rank Results
              <div className="flow-function-annotation">rag_query.py: hybrid_search()</div>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-node storage">
              <span className="flow-icon">📊</span>
              Log Query and Response
              <div className="flow-function-annotation">utils.monitoring: record_query_execution()</div>
            </div>

            <div className="flow-arrow">↓</div>
          </div>

          {/* Response Handling Section */}
          <div className="flow-section purple">
            <div className="flow-section-header">
              <span className="flow-icon">💬</span>
              RESPONSE HANDLING
            </div>

            <div className="flow-node subprocess flow-data-flow">
              <span className="flow-icon">✨</span>
              Synthesize Response
              <div className="flow-function-annotation">rag_query.py: generate_answer()</div>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-node subprocess flow-data-flow">
              <span className="flow-icon">📋</span>
              Format Response
              <div className="flow-function-annotation">rag_query.py: _format_context_for_llm()</div>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-node storage">
              <span className="flow-icon">💾</span>
              Cache Result
              <div className="flow-function-annotation">utils.cache.py: QueryCache.set()</div>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-node end">
              <span className="flow-icon">🚀</span>
              Deliver Response to User
              <div className="flow-function-annotation">api.py: return QueryResponse</div>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-node decision">
              Follow-up Question?
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '15px' }}>
              <div style={{ textAlign: 'center' }}>
                <div className="flow-arrow-text">Yes</div>
                <div className="flow-cycle-arrow">↻</div>
                <div style={{ fontSize: '0.7em', color: '#cbd5e1', marginTop: '5px' }}>Return to Query Initiation</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div className="flow-arrow-text">No</div>
                <div className="flow-success-check">✓</div>
                <div style={{ fontSize: '0.7em', color: '#cbd5e1', marginTop: '5px' }}>End Session</div>
              </div>
            </div>
          </div>

          {/* Data Sources & Analytics Section */}
          <div className="flow-section blue">
            <div className="flow-section-header">
              <span className="flow-icon">💾</span>
              DATA SOURCES & ANALYTICS
            </div>

            <div className="flow-node data flow-data-flow">
              <span className="flow-icon">🗄️</span>
              Neo4j Knowledge Graph
              <div className="flow-function-annotation">query_templates.py: QueryTemplates</div>
            </div>

            <div style={{ textAlign: 'center', margin: '10px 0', fontSize: '0.8em', color: '#cbd5e1' }}>
              Entities & Relationships
            </div>

            <div className="flow-arrow">↕️</div>

            <div className="flow-node data flow-data-flow">
              <span className="flow-icon">🔢</span>
              Embeddings in Neo4j
              <div className="flow-function-annotation">utils.embedding_generator: EmbeddingGenerator</div>
            </div>

            <div style={{ textAlign: 'center', margin: '10px 0', fontSize: '0.8em', color: '#cbd5e1' }}>
              BAAI/bge-small-en-v1.5<br />
              <span style={{ fontSize: '0.7em', opacity: 0.7 }}>768-dim vectors stored in Neo4j</span>
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-node subprocess flow-data-flow">
              <span className="flow-icon">📈</span>
              Analytics Dashboard
              <div className="flow-function-annotation">utils.monitoring: PrometheusMiddleware</div>
            </div>

            <div className="flow-note">
              <strong>Monitors:</strong><br />
              • Query patterns<br />
              • Response quality<br />
              • User satisfaction<br />
              • System performance
            </div>

            <div className="flow-arrow">↓</div>

            <div className="flow-node decision">
              Model Update Needed?
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '15px' }}>
              <div style={{ textAlign: 'center' }}>
                <div className="flow-arrow-text">Yes</div>
                <div className="flow-cycle-arrow">↻</div>
                <div style={{ fontSize: '0.7em', color: '#cbd5e1', marginTop: '5px' }}>Retrain / Update KG</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div className="flow-arrow-text">No</div>
                <div style={{ fontSize: '1.5em', color: '#10b981' }}>→</div>
                <div style={{ fontSize: '0.7em', color: '#cbd5e1', marginTop: '5px' }}>Continue Monitoring</div>
              </div>
            </div>
          </div>
        </div>

        <div className="flow-footer">
          <strong>Key Feedback Loops:</strong>{' '}
          Follow-up Questions ↻ Query Initiation |{' '}
          Analytics ↻ Model Updates |{' '}
          User Interactions ↻ Response Improvement
        </div>
      </div>
    </>
  );
};

export default GraphRAGFlowDiagram;

