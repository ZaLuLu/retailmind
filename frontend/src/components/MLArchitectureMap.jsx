import React, { useState } from 'react';
import './MLArchitectureMap.css';

const ML_NODES = [
  {
    id: 'NODE-01',
    title: 'Ingestion Engine',
    model: 'Gemini 1.5 Flash Vision',
    desc: 'Spatial OCR & Key-Value Extraction',
    details: {
      input: 'Raw Image / PDF Receipt',
      output: 'Structured JSON (Vendor, Date, Amount)',
      latency: '~2.5s',
      context: 'Utilizes multimodal vision capabilities to spatially locate line items and total amounts regardless of receipt format.'
    }
  },
  {
    id: 'NODE-02',
    title: 'Categorization Engine',
    model: 'Gemini 1.5 Flash',
    desc: 'Zero-shot Semantic Classification',
    details: {
      input: 'Extracted Vendor Name & Context',
      output: 'Standardized Taxonomy Category',
      latency: '~800ms',
      context: 'Uses zero-shot prompting to map arbitrary vendor names (e.g., "Starbucks") to a strict internal taxonomy (e.g., "Food").'
    }
  },
  {
    id: 'NODE-03',
    title: 'Anomaly Analysis',
    model: 'Gemini 1.5 Flash',
    desc: 'Contextual Spending Spike Detection',
    details: {
      input: 'Current Tx + Last 10 Txs Baseline',
      output: 'Boolean Flag + Newsprint Reason',
      latency: '~1.2s',
      context: 'Dynamically analyzes recent history to determine if a new transaction represents an unusual spending spike or behavioral anomaly.'
    }
  },
  {
    id: 'NODE-04',
    title: 'Advisory Intelligence',
    model: 'Gemini 1.5 Flash',
    desc: 'RAG Conversational Agent',
    details: {
      input: 'User Query + Complete Ledger Data',
      output: 'Plain-English Financial Guidance',
      latency: '~1.5s',
      context: 'Injects the user\'s full monthly summary and budget constraints into the prompt context to provide highly personalized financial advice.'
    }
  }
];

const MLArchitectureMap = ({ onClose }) => {
  const [activeNode, setActiveNode] = useState(ML_NODES[0]);

  return (
    <div className="ml-map-overlay">
      <div className="ml-map-card">
        <header className="ml-map-header">
          <div className="ml-map-title-group">
            <span className="ml-map-subtitle">
              <span className="pulse-dot"></span>
              SYSTEM TOPOLOGY
            </span>
            <h2 className="ml-map-title">ML Architecture</h2>
          </div>
          <button className="settings-close" onClick={onClose} aria-label="Close architecture map">×</button>
        </header>

        <div className="ml-map-body">
          {/* Details Sidebar */}
          <aside className="ml-details-panel">
            <h3 className="ml-details-title">{activeNode.id} Specs</h3>
            
            <div className="ml-details-row">
              <span className="ml-details-label">Engine</span>
              <span className="ml-details-value">{activeNode.model}</span>
            </div>
            
            <div className="ml-details-row">
              <span className="ml-details-label">Input Vector</span>
              <span className="ml-details-value">{activeNode.details.input}</span>
            </div>
            
            <div className="ml-details-row">
              <span className="ml-details-label">Output Payload</span>
              <span className="ml-details-value">{activeNode.details.output}</span>
            </div>

            <div className="ml-details-row">
              <span className="ml-details-label">Avg Latency</span>
              <span className="ml-details-value">{activeNode.details.latency}</span>
            </div>

            <div className="ml-details-prompt">
              <span className="ml-details-label" style={{color: '#aaa'}}>Technical Context</span><br/>
              {activeNode.details.context}
            </div>
          </aside>

          {/* Schematic Nodes */}
          <div className="ml-schematic-area">
            <div className="ml-wiring"></div>
            
            {ML_NODES.map((node) => (
              <div 
                key={node.id} 
                className={`ml-node ${activeNode.id === node.id ? 'active' : ''}`}
                onMouseEnter={() => setActiveNode(node)}
                onClick={() => setActiveNode(node)}
              >
                <div className="ml-node-header">
                  <span className="ml-node-id">{node.id}</span>
                  <span className="ml-node-model">{node.model}</span>
                </div>
                <h3>{node.title}</h3>
                <p>{node.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MLArchitectureMap;
