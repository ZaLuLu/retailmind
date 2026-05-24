import React, { useState, useEffect, useRef } from 'react'
import { api } from '../services/api'

function AdvisorChat({ summary, prefill, clearPrefill, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: 'advisor',
      content: 'Hello. I am your RetailMind Advisor. Ask me about your top products, margin erosion, demand signals, dead stock, or any trends in your sales data.'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (prefill) {
      setInput(prefill)
      clearPrefill()
    }
  }, [prefill, clearPrefill])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const currentInput = input;
    const userMsg = { role: 'user', content: currentInput }
    
    // Create unique ID for the streaming response card
    const streamId = Date.now();
    
    setMessages(prev => [...prev, userMsg, { id: streamId, role: 'advisor', content: '' }])
    setInput('')
    setLoading(true)

    const contextStr = summary ? JSON.stringify(summary) : ''

    await api.askAdvisorStream(
      currentInput,
      contextStr,
      (chunk) => {
        setMessages(prev => prev.map(msg => 
          msg.id === streamId 
            ? { ...msg, content: msg.content + chunk } 
            : msg
        ))
      },
      (error) => {
        setMessages(prev => prev.map(msg => 
          msg.id === streamId 
            ? { ...msg, content: 'The intelligence desk encountered a telex line drop. Please resubmit your request.' } 
            : msg
        ))
        setLoading(false)
      },
      () => {
        setLoading(false)
      }
    )
  }

  return (
    <div className="chat-overlay">
      <div className="chat-card">
        <header>
          <div className="chat-header-row">
            <div>
              <p className="mono" style={{ margin: '0 0 0.1rem', color: 'var(--ink-muted)', fontSize: '0.6rem', fontWeight: 800, letterSpacing: '0.12em' }}>
                DIRECT WIRE TRANSMISSION // CLASSIFIED LEDGER ACCESS
              </p>
              <h2>Teletype Advisor Dispatch</h2>
              <div style={{ display: 'flex', gap: '1rem', marginTop: '0.4rem', fontFamily: 'var(--font-mono)', fontSize: '0.55rem', color: 'var(--text-muted)' }}>
                <span>STATION: RETAILMIND CORE V3.1.0</span>
                <span>DESK ID: ENG-RAG-902</span>
                <span>STATUS: ACTIVE ONLINE</span>
              </div>
            </div>
            <button className="close-btn" onClick={onClose} aria-label="Close advisor">×</button>
          </div>
        </header>

        <div className="chat-history" ref={scrollRef}>
          {messages.map((msg, i) => (
            <div key={i} className={`chat-message ${msg.role}`}>
              <div className="message-header">
                {msg.role === 'advisor' ? '▲ ADVISOR SYSTEM DISPATCH' : '▼ OPERATOR INQUIRY'}
              </div>
              <div className="message-content">
                {msg.role === 'advisor' && (
                  <div className="telex-badge">REPLY STAMP: INTEL-OK</div>
                )}
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-thinking">TELEX TRANSCRIPTION IN PROGRESS...</div>
          )}
        </div>

        {/* Pre-built Prompt Chips */}
        <div className="chat-prompt-chips" style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', padding: '0.5rem 1rem', borderTop: '1px dashed rgba(0,0,0,0.12)' }}>
          {[
            "What's dragging down my margin?",
            "Which products should I reorder?",
            "Why did sales drop last week?"
          ].map((chip) => (
            <button
              key={chip}
              className="prompt-chip mono"
              style={{
                fontSize: '0.62rem',
                background: 'var(--bg-tint)',
                border: '1px solid var(--ink-black)',
                padding: '3px 8px',
                cursor: 'pointer',
                borderRadius: '3px',
                fontWeight: 700
              }}
              disabled={loading}
              onClick={() => setInput(chip)}
            >
              {chip}
            </button>
          ))}
        </div>

        <div className="chat-input-area">
          <input
            type="text"
            placeholder="Ask about top products, margins, dead stock, demand trends..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            aria-label="Advisor question"
            disabled={loading}
          />
          <button 
            className={`chat-send-btn ${loading ? 'btn-ghost-loading' : ''}`} 
            onClick={handleSend}
            disabled={loading}
          >
            Send →
          </button>
        </div>
      </div>
    </div>
  )
}

export default AdvisorChat
