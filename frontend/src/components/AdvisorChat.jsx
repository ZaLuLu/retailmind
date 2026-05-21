import React, { useState, useEffect, useRef } from 'react'
import { api } from '../services/api'

function AdvisorChat({ summary, onClose }) {
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
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMsg = { role: 'user', content: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const contextStr = summary ? JSON.stringify(summary) : ''
      const response = await api.post('/advisor/ask', {
        question: input,
        context: contextStr
      })
      setMessages(prev => [...prev, { role: 'advisor', content: response.answer }])
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'advisor', content: 'The intelligence desk is temporarily unavailable. Please try again shortly.' }
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-overlay">
      <div className="chat-card">
        <header>
          <div className="chat-header-row">
            <div>
              <p className="mono" style={{ margin: '0 0 0.2rem', color: 'var(--text-muted)' }}>
                Bureau of Retail Intelligence
              </p>
              <h2>Retail Advisor Desk</h2>
            </div>
            <button className="close-btn" onClick={onClose} aria-label="Close advisor">×</button>
          </div>
        </header>

        <div className="chat-history" ref={scrollRef}>
          {messages.map((msg, i) => (
            <div key={i} className={`chat-message ${msg.role}`}>
              <div className="message-header">
                {msg.role === 'advisor' ? 'RetailMind Advisor' : 'You'}
              </div>
              <div className="message-content">{msg.content}</div>
            </div>
          ))}
          {loading && (
            <div className="chat-thinking animate-pulse">Consulting retail intelligence...</div>
          )}
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
