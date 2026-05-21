import React from 'react';

const AlertsSection = ({ anomalies }) => {
  return (
    <section className="alerts-section">
      <div className="section-kicker kicker-red">
        <span className="kicker-label">Breaking News</span>
        <div className="kicker-line"></div>
      </div>

      <div className="alerts-grid">
        {anomalies.length === 0 ? (
          <div className="alert-card stability">
            <div className="alert-header">
              <h3>Stability Report</h3>
              <span className="alert-icon">✓</span>
            </div>
            <p className="alert-reason">
              No unusual spending spikes detected this period. Your patterns remain consistent with historical baseline.
            </p>
          </div>
        ) : (
          anomalies.map((anomaly, idx) => (
            <div key={idx} className="alert-card">
              <div className="alert-header">
                <h3>Spending Spike: {anomaly.vendor}</h3>
                <span className="alert-icon">⚠</span>
              </div>
              <p className="alert-amount">
                SPIKE DETECTED: ₹{anomaly.amount.toLocaleString('en-IN')}
              </p>
              <p className="alert-reason">{anomaly.reason}</p>
            </div>
          ))
        )}
      </div>
    </section>
  );
};

export default AlertsSection;
