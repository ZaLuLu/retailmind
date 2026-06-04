// SplashScreen.jsx
import React, { useState, useEffect } from 'react'
import './SplashScreen.css'

export default function SplashScreen({ onComplete }) {
  const [logs, setLogs] = useState([])
  const [fade, setFade] = useState(false)

  const steps = [
    '[SYS] INITIALIZING RETAIL ANALYTICS ENGINE...',
    '[SYS] CONFIGURING ENCRYPTED RETAIL DATASTORES...',
    '[SYS] SYSTEM CORE READY.'
  ]

  useEffect(() => {
    let t1 = setTimeout(() => {
      setLogs(prev => [...prev, steps[0]])
    }, 250)

    let t2 = setTimeout(() => {
      setLogs(prev => [...prev, steps[1]])
    }, 650)

    let t3 = setTimeout(() => {
      setLogs(prev => [...prev, steps[2]])
    }, 1100)

    let tFade = setTimeout(() => {
      setFade(true)
    }, 1600)

    let tComplete = setTimeout(() => {
      if (onComplete) onComplete()
    }, 2100)

    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
      clearTimeout(t3)
      clearTimeout(tFade)
      clearTimeout(tComplete)
    }
  }, [])

  return (
    <div className={`splash-overlay ${fade ? 'fade-out' : ''}`}>
      <div className="splash-broadsheet">
        
        <div className="splash-masthead">
          <span className="splash-kicker">SMB Retail Intelligence Dashboard</span>
          <h1 className="splash-title">RetailMind</h1>
          <span className="splash-sub">VOL. I — SALES INTELLIGENCE EDITION</span>
        </div>

        <div className="splash-terminal">
          {logs.map((log, idx) => (
            <div key={idx}>{log}</div>
          ))}
          {logs.length < steps.length && (
            <div>
              [SYS] Connecting...<span className="splash-terminal-cursor"></span>
            </div>
          )}
        </div>

        <div className="splash-stamp">
          <div className="splash-stamp-text">
            SECURE<br />DATA
          </div>
        </div>

      </div>
    </div>
  )
}
