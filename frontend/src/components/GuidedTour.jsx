// GuidedTour.jsx
import React, { useState, useEffect } from 'react'
import './GuidedTour.css'

export default function GuidedTour() {
  const [activeStep, setActiveStep] = useState(0)
  const [isVisible, setIsVisible] = useState(false)

  const steps = [
    {
      selector: '.byline-store-selector-trigger',
      title: '🏬 Location Roster',
      content: 'Click here to switch active storefront locations or register new retail entities. The ledger and predictive forecasts re-cluster immediately.'
    },
    {
      selector: '#tour-sales-graph',
      title: '📈 Forecast Confidence Bands',
      content: 'Hover over the sales graph to see the 14-day Holt-Winters predictive demand. Standard 95% confidence bands and 3σ warnings flag sales spikes.'
    },
    {
      selector: '#tour-alerts',
      title: '⚠️ Severity Alert Board',
      content: 'Audits dead stock, margin erosion, and spikes. Click "Ask Advisor" to open the advisor chat panel pre-filled with dynamic diagnostic instructions.'
    },
    {
      selector: '#tour-upload',
      title: '📷 AI Invoice Scanner',
      content: 'Click "AI Scan Receipt" to feed supplier invoices to the Gemini Vision Engine, review parsed records, and commit them in bulk to the general ledger.'
    }
  ]

  useEffect(() => {
    // Check if user has already completed the tour
    const tourDone = localStorage.getItem('retailmind_tour_completed')
    if (!tourDone) {
      // Delay showing the tour slightly to let the page finish initial rendering/loading
      const timer = setTimeout(() => {
        setIsVisible(true)
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [])

  // Escape key handler to close the tour
  useEffect(() => {
    if (!isVisible) return
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        handleDismiss()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isVisible])

  useEffect(() => {
    if (!isVisible) return

    // Clean up any existing glows first
    steps.forEach(step => {
      const el = document.querySelector(step.selector)
      if (el) el.classList.remove('tour-active-glow')
    })

    // Find and highlight active target
    const currentStepConfig = steps[activeStep]
    if (currentStepConfig) {
      const target = document.querySelector(currentStepConfig.selector)
      if (target) {
        // Scroll target smoothly into view
        target.scrollIntoView({ behavior: 'smooth', block: 'center' })
        // Add spotlight animation class
        target.classList.add('tour-active-glow')
      }
    }

    // Cleanup on unmount or step change
    return () => {
      steps.forEach(step => {
        const el = document.querySelector(step.selector)
        if (el) el.classList.remove('tour-active-glow')
      })
    }
  }, [activeStep, isVisible])

  const handleNext = () => {
    if (activeStep < steps.length - 1) {
      setActiveStep(prev => prev + 1)
    } else {
      handleDismiss()
    }
  }

  const handleDismiss = () => {
    localStorage.setItem('retailmind_tour_completed', 'true')
    setIsVisible(false)
  }

  if (!isVisible) return null

  const currentStepData = steps[activeStep]

  return (
    <>
      {/* Dimmed spotlight backdrop to focus attention */}
      <div className="tour-spotlight-backdrop" />

      {/* Floating Guided Tour Dispatch */}
      <div className="tour-card-floating">
        
        <div className="tour-card-header">
          <span className="tour-card-kicker">Retail Intelligence Guide</span>
          <span className="mono" style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
            STEP {activeStep + 1} OF {steps.length}
          </span>
        </div>

        <h3 className="tour-card-title">{currentStepData.title}</h3>
        <p className="tour-card-body">{currentStepData.content}</p>

        <div className="tour-card-footer">
          <button 
            type="button" 
            className="tour-btn-skip"
            onClick={handleDismiss}
          >
            Skip Guide
          </button>

          <div className="tour-steps-indicator">
            {steps.map((_, idx) => (
              <span 
                key={idx} 
                className={`tour-step-dot ${activeStep === idx ? 'active' : ''}`}
                onClick={() => setActiveStep(idx)}
              >
                {idx + 1}
              </span>
            ))}
          </div>

          <button 
            type="button" 
            className="tour-btn-next"
            onClick={handleNext}
          >
            {activeStep === steps.length - 1 ? 'Finish ✓' : 'Next Step →'}
          </button>
        </div>

      </div>
    </>
  )
}
