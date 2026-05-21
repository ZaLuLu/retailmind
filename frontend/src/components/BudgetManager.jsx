import React, { useState } from 'react'

const CATEGORIES = ['Food', 'Transport', 'Utilities', 'Entertainment', 'Health', 'Shopping', 'Other']

function BudgetManager({ user, onSave, onClose }) {
  const [formData, setFormData] = useState({
    fullName: user.fullName || '',
    initialBalance: user.balance || 0,
    budgets: user.budgets || CATEGORIES.reduce((acc, cat) => ({ ...acc, [cat]: '0' }), {})
  })

  const handleBudgetChange = (cat, val) => {
    setFormData({
      ...formData,
      budgets: { ...formData.budgets, [cat]: val }
    })
  }

  const handleSubmit = () => {
    onSave(formData)
  }

  return (
    <div className="settings-overlay">
      <div className="settings-card">
        <header className="settings-header">
          <div className="settings-top">
            <span>Ledger Configuration</span>
            <button className="settings-close" onClick={onClose} aria-label="Close settings">×</button>
          </div>
          <h2 className="settings-title">Control Panel</h2>
        </header>

        <div className="settings-body">
          <div className="settings-form-group">
            <label>Display Name</label>
            <input
              type="text"
              className="settings-input"
              value={formData.fullName}
              onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
            />
          </div>
          <div className="settings-form-group">
            <label>Current Savings / Balance (₹)</label>
            <input
              type="number"
              className="settings-input"
              value={formData.initialBalance}
              onChange={(e) => setFormData({ ...formData, initialBalance: e.target.value })}
            />
          </div>

          <h4 className="settings-section-title">Monthly Allocations</h4>
          <div className="settings-budget-list">
            {CATEGORIES.map(cat => (
              <div key={cat} className="settings-budget-row">
                <label>{cat}</label>
                <input
                  type="number"
                  className="settings-budget-input"
                  value={formData.budgets[cat] || '0'}
                  onChange={(e) => handleBudgetChange(cat, e.target.value)}
                />
              </div>
            ))}
          </div>
        </div>

        <div className="settings-actions">
          <button className="newsprint-btn secondary" onClick={onClose}>Discard</button>
          <button className="newsprint-btn" onClick={handleSubmit}>Save Changes</button>
        </div>
      </div>
    </div>
  )
}

export default BudgetManager
