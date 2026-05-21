import React from 'react';

const SummaryHero = ({ summary }) => {
  const isOverBudget = summary.remaining_budget < 0;

  return (
    <section className="summary-hero">
      <div className="section-kicker">
        <span className="kicker-label">
          Terminal Summary // {new Date().toLocaleDateString('en-US', { month: 'short', year: '2-digit' }).toUpperCase()}
        </span>
        <div className="kicker-line"></div>
      </div>

      <div className="hero-stats">
        <div className="hero-stat">
          <span className="hero-stat-label">Total Spent</span>
          <span className="hero-stat-value">
            ₹{summary.total_spent.toLocaleString('en-IN')}
          </span>
        </div>
        <div className="hero-stat">
          <span className="hero-stat-label">Budget Remaining</span>
          <span className={`hero-stat-value ${isOverBudget ? 'alert-text' : ''}`}>
            ₹{Math.abs(summary.remaining_budget).toLocaleString('en-IN')}
            {isOverBudget && <span style={{ fontSize: '0.4em', verticalAlign: 'super' }}> OVR</span>}
          </span>
        </div>
      </div>

      <div className="hero-status-bar">
        <div className={`status-dot ${isOverBudget ? 'critical' : ''}`}></div>
        <span className="status-label">
          Savings Status: {isOverBudget ? 'Over Budget — Review Required' : 'On Track — Stable'}
        </span>
      </div>
    </section>
  );
};

export default SummaryHero;
