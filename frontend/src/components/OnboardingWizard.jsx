import { useState } from 'react'

const CURRENCIES = [
  { code: 'INR', label: '₹ INR (Indian Rupee)' },
  { code: 'USD', label: '$ USD (US Dollar)' },
  { code: 'EUR', label: '€ EUR (Euro)' },
  { code: 'GBP', label: '£ GBP (British Pound)' },
  { code: 'AED', label: 'د.إ AED (UAE Dirham)' },
]

function OnboardingWizard({ onComplete }) {
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState({
    fullName: '',
    storeName: '',
    currency: 'INR',
    initialBalance: '0',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async () => {
    setIsSubmitting(true)
    await onComplete(formData)
    setIsSubmitting(false)
  }

  const handleLoadDemo = async () => {
    setIsSubmitting(true)
    await onComplete({
      fullName: 'Rahul Sharma',
      storeName: 'Sharma Retail & Co.',
      currency: 'INR',
      initialBalance: '0',
    })
    setIsSubmitting(false)
  }

  return (
    <div className="onboarding-overlay">
      <div className="wizard-card">
        <header className="step-indicator">
          <span className="mono">Step {step} of 2</span>
          <h2>
            {step === 1 ? 'Store Profile Configuration' : 'Launch Retail Intelligence'}
          </h2>
        </header>

        {step === 1 && (
          <div className="wizard-step">
            <p>Define your storefront details and reporting currency.</p>
            <div className="form-group">
              <label>Proprietor Name</label>
              <input
                type="text"
                placeholder="e.g. Rahul Sharma"
                value={formData.fullName}
                onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Store Name / Legal Entity</label>
              <input
                type="text"
                placeholder="e.g. Sharma Retail & Co."
                value={formData.storeName}
                onChange={(e) => setFormData({ ...formData, storeName: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Operating Currency</label>
              <select
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                className="onboarding-select"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  fontFamily: 'var(--font-mono)',
                  border: 'var(--border-light)',
                  backgroundColor: 'var(--bg-paper)',
                  color: 'var(--ink)'
                }}
              >
                {CURRENCIES.map(c => (
                  <option key={c.code} value={c.code}>{c.label}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="wizard-step">
            <p>Review your storefront configuration. Are these parameters correct?</p>
            <div className="summary card" style={{ border: 'var(--border-heavy)', padding: '1rem', backgroundColor: 'rgba(0,0,0,0.02)' }}>
              <p className="mono"><strong>PROPRIETOR:</strong> {formData.fullName}</p>
              <p className="mono"><strong>STORE:</strong> {formData.storeName}</p>
              <p className="mono"><strong>REPORTING CURRENCY:</strong> {formData.currency}</p>
            </div>
          </div>
        )}

        <div className="wizard-actions" style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.5rem' }}>
          <div>
            {step === 1 && (
              <button
                onClick={handleLoadDemo}
                disabled={isSubmitting}
                className={isSubmitting ? 'btn-ghost-loading' : ''}
                style={{
                  backgroundColor: 'var(--ink-black)',
                  color: 'var(--bg-paper)',
                  borderColor: 'var(--ink-black)',
                  fontSize: '0.75rem',
                }}
              >
                ⚡ Load Demo Profile
              </button>
            )}
            {step > 1 && (
              <button
                onClick={() => setStep(step - 1)}
                style={{ background: 'transparent', color: 'var(--ink-black)', border: 'var(--border-light)' }}
              >
                ← Back
              </button>
            )}
          </div>
          <div>
            {step < 2 ? (
              <button
                onClick={() => setStep(step + 1)}
                disabled={isSubmitting || !formData.fullName.trim() || !formData.storeName.trim()}
              >
                Continue →
              </button>
            ) : (
              <button onClick={handleSubmit} disabled={isSubmitting} className={isSubmitting ? 'btn-ghost-loading' : ''}>
                Launch Intelligence →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default OnboardingWizard
