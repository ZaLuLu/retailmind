import React from 'react';

const CategoryBreakdown = ({ categories, totalSpent }) => {
  return (
    <section>
      <div className="section-kicker">
        <span className="kicker-label">Expenditure Classification</span>
        <div className="kicker-line"></div>
      </div>

      <div className="category-list">
        {categories.length === 0 && (
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            NO CATEGORIES TO DISPLAY YET.
          </p>
        )}
        {categories.map((cat, idx) => {
          let percentage = 0;
          let isOverLimit = false;
          let metaText = `₹${cat.amount.toLocaleString('en-IN')}`;

          if (cat.limit > 0) {
            percentage = Math.min((cat.amount / cat.limit) * 100, 100);
            isOverLimit = cat.amount > cat.limit;
            metaText += ` / ₹${cat.limit.toLocaleString('en-IN')}`;
          } else {
            percentage = totalSpent > 0 ? (cat.amount / totalSpent) * 100 : 0;
          }

          return (
            <div key={idx} className="category-item">
              <div className="category-meta">
                <span className={isOverLimit ? 'over-limit' : ''}>{cat.category.toUpperCase()}</span>
                <span className={isOverLimit ? 'over-limit' : ''}>{metaText}</span>
              </div>
              <div className="progress-bar-container">
                <div
                  className="progress-bar-fill"
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: isOverLimit ? 'var(--ink-red)' : 'var(--ink-black)'
                  }}
                ></div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default CategoryBreakdown;
