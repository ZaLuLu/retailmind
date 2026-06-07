// GuidedTour.jsx
import { useState, useEffect, useCallback } from 'react'
import './GuidedTour.css'

const STEPS = [
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
    selector: '.pricing-simulator',
    title: '📊 Pricing Margin Simulator',
    content: 'Simulate retail price changes (from -30% to +30%) to estimate the demand volume impact, gross profit margins, and overall category revenue elasticity.'
  },
  {
    selector: '.user-manual-section',
    title: '📖 Store Operating Manual',
    content: 'Review this live manual to see the strict column format specifications for CSV/Excel uploads, and learn how our Holt-Winters and K-Means predictive models cluster your catalog.'
  }
]

export default function GuidedTour() {
  const [activeStep, setActiveStep] = useState(0)
  const [isVisible, setIsVisible] = useState(false)
  const [cardStyle, setCardStyle] = useState({ position: 'fixed', bottom: '2rem', right: '2rem' })

  const handleDismiss = useCallback(() => {
    localStorage.setItem('retailmind_tour_completed', 'true')
    setIsVisible(false)
  }, [])

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
  }, [isVisible, handleDismiss])

  useEffect(() => {
    if (!isVisible) return

    // Clean up any existing glows first
    STEPS.forEach(step => {
      const el = document.querySelector(step.selector)
      if (el) el.classList.remove('tour-active-glow')
    })

    // Find and highlight active target
    const currentStepConfig = STEPS[activeStep]
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
      STEPS.forEach(step => {
        const el = document.querySelector(step.selector)
        if (el) el.classList.remove('tour-active-glow')
      })
    }
  }, [activeStep, isVisible])

  // Contextual floating positioning logic
  useEffect(() => {
    if (!isVisible) return

    const updatePosition = () => {
      const currentStepConfig = STEPS[activeStep]
      if (!currentStepConfig) return

      const target = document.querySelector(currentStepConfig.selector)
      if (target) {
        const rect = target.getBoundingClientRect()
        const isMobile = window.innerWidth < 768

        if (isMobile) {
          setCardStyle({
            position: 'fixed',
            bottom: '1rem',
            left: '50%',
            transform: 'translateX(-50%)',
            width: '90%',
            maxWidth: '340px',
            zIndex: 10001
          })
        } else {
          const cardHeight = 180 // approximate height
          const cardWidth = 340
          const spaceBelow = window.innerHeight - rect.bottom
          const spaceAbove = rect.top

          let top = rect.bottom + window.scrollY + 12
          let left = Math.max(12, rect.left + window.scrollX + (rect.width - cardWidth) / 2)

          // Keep left inside viewport boundary
          if (left + cardWidth > window.innerWidth - 24) {
            left = window.innerWidth - cardWidth - 24
          }

          if (spaceBelow < cardHeight && spaceAbove > cardHeight) {
            // Position above target
            top = rect.top + window.scrollY - cardHeight - 12
          }

          setCardStyle({
            position: 'absolute',
            top: `${top}px`,
            left: `${left}px`,
            width: `${cardWidth}px`,
            zIndex: 10001
          })
        }
      } else {
        // Fallback
        setCardStyle({
          position: 'fixed',
          bottom: '2rem',
          right: '2rem',
          width: '340px',
          zIndex: 10001
        })
      }
    }

    // Recalculate slightly after render/scroll
    const timer = setTimeout(updatePosition, 300)

    window.addEventListener('resize', updatePosition)
    window.addEventListener('scroll', updatePosition)

    return () => {
      clearTimeout(timer)
      window.removeEventListener('resize', updatePosition)
      window.removeEventListener('scroll', updatePosition)
    }
  }, [activeStep, isVisible])

  const handleNext = () => {
    if (activeStep < STEPS.length - 1) {
      setActiveStep(prev => prev + 1)
    } else {
      handleDismiss()
    }
  }

  if (!isVisible) return null

  const currentStepData = STEPS[activeStep]

  return (
    <>
      {/* Dimmed spotlight backdrop to focus attention */}
      <div className="tour-spotlight-backdrop" />

      {/* Floating Guided Tour Dispatch */}
      <div className="tour-card-floating" style={cardStyle}>
        
        <div className="tour-card-header">
          <span className="tour-card-kicker">Retail Intelligence Guide</span>
          <span className="mono" style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
            STEP {activeStep + 1} OF {STEPS.length}
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
            {STEPS.map((_, idx) => (
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
            {activeStep === STEPS.length - 1 ? 'Finish ✓' : 'Next Step →'}
          </button>
        </div>

      </div>
    </>
  )
}
