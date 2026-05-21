import React from 'react';

const LedgerPreview = ({ transactions, onSelectTransaction, onShowFullLedger }) => {
  const recentTx = transactions.slice(0, 5);

  return (
    <section>
      <div className="section-kicker">
        <span className="kicker-label">Transaction Ledger // Recent</span>
        <div className="kicker-line"></div>
      </div>

      {recentTx.length === 0 ? (
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '1rem' }}>
          NO TRANSACTIONS ON RECORD. UPLOAD A RECEIPT TO BEGIN.
        </p>
      ) : (
        <div className="ledger-table-container">
          <table className="ledger-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Vendor</th>
                <th className="text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {recentTx.map((tx, idx) => (
                <tr
                  key={tx.id || idx}
                  onClick={() => onSelectTransaction(tx)}
                  className="clickable-row"
                >
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', whiteSpace: 'nowrap' }}>
                    {new Date(tx.date || tx.transaction_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
                  </td>
                  <td style={{ fontWeight: 600 }}>{tx.vendor || tx.vendor_name}</td>
                  <td className="text-right" style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                    ₹{parseFloat(tx.amount).toLocaleString('en-IN')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <button className="ledger-footer-btn" onClick={onShowFullLedger}>
        View Full Ledger →
      </button>
    </section>
  );
};

export default LedgerPreview;
