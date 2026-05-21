import React, { useState } from 'react';
import './MLArchitectureMap.css';

const ML_NODES = [
  {
    id: 'NODE-01',
    title: 'Ingestion Engine',
    model: 'Gemini 3 Flash (Vision/Multimodal)',
    desc: 'Multimodal OCR & Data Structuring',
    details: {
      input: 'Raw JPG/PNG Image or Multi-page PDF Receipt',
      output: 'Structured Extraction JSON',
      latency: '~2.5s',
      context: "Utilizes Gemini's native multimodal capabilities to analyze uploaded JPG, PNG, or PDF receipts. Applies spatial coordinates reasoning to parse raw text and return standard structured JSON containing vendor_name, amount, category, transaction_date, and confidence score."
    }
  },
  {
    id: 'NODE-02',
    title: 'Categorization Engine',
    model: 'Gemini 3 Flash (Zero-shot NLP)',
    desc: 'Zero-shot Semantic Mapping',
    details: {
      input: 'Extracted Vendor Name & Context Metadata',
      output: 'Standardized Retail Category Tag',
      latency: '~800ms',
      context: 'Implements a zero-shot prompting strategy. Matches arbitrary extracted merchant/vendor strings (e.g. "Starbucks India") to a strict pre-defined retail taxonomy list (Food, Transport, Utilities, Entertainment, Health, Shopping, Other) without needing custom training data.'
    }
  },
  {
    id: 'NODE-03',
    title: 'Anomaly Analysis',
    model: 'Gemini 3 Flash (Few-shot Prompting)',
    desc: 'Contextual Spending Spike Detection',
    details: {
      input: 'Current Transaction + Last 10 Transactions Baseline',
      output: 'Anomaly Boolean & Explanation',
      latency: '~1.2s',
      context: 'Implements sliding window history injection. Passes the currently uploaded transaction along with a rolling few-shot baseline of the last 10 store transactions. The model performs in-context reasoning to flag outliers, spike triggers, or margin erosion signals.'
    }
  },
  {
    id: 'NODE-04',
    title: 'Advisory Intelligence',
    model: 'Gemini 3 Flash (RAG Conversational)',
    desc: 'Retrieval-Augmented Generation Agent',
    details: {
      input: 'User Prompt + Dynamic Financial Context JSON',
      output: 'Insightful Plain-English Advisory Advice',
      latency: '~1.5s',
      context: 'Implements a RAG pipeline. Collects real-time sales summaries, category metrics, and budget parameters, injecting them as retrieval-context into the chat prompt. This enables a natural language conversational assistant to deliver highly customized retail tips.'
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
