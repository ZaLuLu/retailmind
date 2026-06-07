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
          const percentage = cat.limit > 0
            ? Math.min((cat.amount / cat.limit) * 100, 100)
            : (totalSpent > 0 ? (cat.amount / totalSpent) * 100 : 0);
          const isOverLimit = cat.limit > 0 && cat.amount > cat.limit;
          const metaText = cat.limit > 0
            ? `₹${cat.amount.toLocaleString('en-IN')} / ₹${cat.limit.toLocaleString('en-IN')}`
            : `₹${cat.amount.toLocaleString('en-IN')}`;

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
