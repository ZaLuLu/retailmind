import { useState } from 'react'
import { formatMoneyCompact } from '../services/currency'
import DashboardTooltip from './DashboardTooltip'
import './PricingSimulator.css'

const CATEGORY_ELASTICITY = {
  'Electronics': -1.8,
  'Apparel': -1.5,
  'Food': -0.8,
  'Other': -1.2
}

const PricingSimulator = ({ products = [], currency = 'INR' }) => {
  // Fallback default products if empty
  const defaultProducts = [
    { product_name: 'Premium Leather Boots', category: 'Apparel', revenue: 75000, quantity: 150, margin_pct: 42 },
    { product_name: 'Organic Fruit Basket', category: 'Food', revenue: 28000, quantity: 200, margin_pct: 18 },
    { product_name: 'Wireless Headphones', category: 'Electronics', revenue: 110000, quantity: 110, margin_pct: 35 },
    { product_name: 'Vintage Notepad', category: 'Other', revenue: 15000, quantity: 300, margin_pct: 60 }
  ]

  const activeProducts = products.length > 0 ? products : defaultProducts

  const [selectedProductIndex, setSelectedProductIndex] = useState(0)
  const [priceVariance, setPriceVariance] = useState(0) // percentage (-30 to +30)

  const product = activeProducts[selectedProductIndex] || defaultProducts[0]

  const elasticity = CATEGORY_ELASTICITY[product.category] || CATEGORY_ELASTICITY['Other']

  // Calculation parameters
  const currentRevenue = product.revenue || 0
  const currentQty = product.quantity || 1
  const marginPct = product.margin_pct || 0

  const currentPrice = currentQty > 0 ? currentRevenue / currentQty : 0
  const currentProfit = currentRevenue * (marginPct / 100)
  const currentCogs = currentRevenue - currentProfit
  const currentCostPerUnit = currentQty > 0 ? currentCogs / currentQty : 0

  // Simulation calculations
  const priceMultiplier = 1 + (priceVariance / 100)
  const simPrice = currentPrice * priceMultiplier

  // Volume Change % = Elasticity * Price Change %
  const volumeChangePct = elasticity * priceVariance
  const simQty = Math.max(0, currentQty * (1 + (volumeChangePct / 100)))

  const simRevenue = simPrice * simQty
  const simCogs = currentCostPerUnit * simQty
  const simProfit = simRevenue - simCogs
  const simMarginPct = simRevenue > 0 ? (simProfit / simRevenue) * 100 : 0

  // Revenue & Profit difference
  const revDiff = simRevenue - currentRevenue
  const profitDiff = simProfit - currentProfit

  return (
    <section className="pricing-simulator">
      <div className="section-kicker">
        <span className="kicker-label">
          Margin Simulator
          <DashboardTooltip
            title="Pricing & Elasticity"
            content="Simulate how price changes affect sales volume, total revenue, and overall profitability based on historical category elasticity coefficients."
          />
        </span>
        <div className="kicker-line" />
      </div>

      <div className="simulator-card">
        <div className="form-group">
          <label htmlFor="sim-product-select">Select Catalog Item</label>
          <select
            id="sim-product-select"
            className="sim-select"
            value={selectedProductIndex}
            onChange={(e) => {
              setSelectedProductIndex(parseInt(e.target.value))
              setPriceVariance(0)
            }}
          >
            {activeProducts.map((p, idx) => (
              <option key={`${p.product_name}-${idx}`} value={idx}>
                {p.product_name} ({p.category})
              </option>
            ))}
          </select>
        </div>

        <div className="simulator-params">
          <div className="param-row">
            <span className="param-name">Original Price</span>
            <span className="param-dots" />
            <span className="param-value mono">{formatMoneyCompact(currentPrice, currency)} / unit</span>
          </div>
          <div className="param-row">
            <span className="param-name">Category Elasticity</span>
            <span className="param-dots" />
            <span className={`param-value mono ${elasticity < -1.2 ? 'text-red' : 'text-green'}`}>
              {elasticity.toFixed(1)}
            </span>
          </div>
        </div>

        <div className="slider-container">
          <div className="slider-header">
            <span>Price Variance</span>
            <span className={`slider-badge mono ${priceVariance > 0 ? 'pos' : priceVariance < 0 ? 'neg' : ''}`}>
              {priceVariance > 0 ? `+${priceVariance}` : priceVariance}%
            </span>
          </div>
          <input
            type="range"
            min="-30"
            max="30"
            step="1"
            value={priceVariance}
            onChange={(e) => setPriceVariance(parseInt(e.target.value))}
            className="sim-slider"
          />
          <div className="slider-labels mono">
            <span>-30%</span>
            <span>0% (Current)</span>
            <span>+30%</span>
          </div>
        </div>

        <div className="sim-divider" />

        <h4 className="sim-sub-header">Simulation Projections</h4>

        <div className="projection-grid">
          <div className="projection-item">
            <span className="proj-label">Projected Price</span>
            <span className="proj-value mono">{formatMoneyCompact(simPrice, currency)}</span>
            <span className="proj-sub">per unit</span>
          </div>
          <div className="projection-item">
            <span className="proj-label">Volume Impact</span>
            <span className={`proj-value mono ${volumeChangePct < 0 ? 'neg' : volumeChangePct > 0 ? 'pos' : ''}`}>
              {volumeChangePct > 0 ? '+' : ''}{volumeChangePct.toFixed(1)}%
            </span>
            <span className="proj-sub">{simQty.toFixed(0)} units projected</span>
          </div>
          <div className="projection-item">
            <span className="proj-label">Projected Revenue</span>
            <span className="proj-value mono">{formatMoneyCompact(simRevenue, currency)}</span>
            <span className={`proj-sub mono ${revDiff > 0 ? 'pos' : revDiff < 0 ? 'neg' : ''}`}>
              {revDiff >= 0 ? '+' : ''}{formatMoneyCompact(revDiff, currency)}
            </span>
          </div>
          <div className="projection-item">
            <span className="proj-label">Projected Profit</span>
            <span className="proj-value mono">{formatMoneyCompact(simProfit, currency)}</span>
            <span className={`proj-sub mono ${profitDiff > 0 ? 'pos' : profitDiff < 0 ? 'neg' : ''}`}>
              {profitDiff >= 0 ? '+' : ''}{formatMoneyCompact(profitDiff, currency)}
            </span>
          </div>
        </div>

        <div className="margin-meter">
          <div className="margin-meter-header">
            <span>Projected Gross Margin %</span>
            <span className="mono">{simMarginPct.toFixed(1)}%</span>
          </div>
          <div className="margin-meter-track">
            <div
              className="margin-meter-fill"
              style={{
                width: `${Math.min(100, Math.max(0, simMarginPct))}%`,
                backgroundColor: simMarginPct >= 40 ? '#4CAF50' : simMarginPct >= 25 ? '#C9A84C' : '#E57373'
              }}
            />
          </div>
        </div>

        <div className="sim-bulletin mono">
          <span className="bulletin-icon">📰</span>
          <p>
            {priceVariance > 0 ? (
              `Increasing price by ${priceVariance}% triggers a volume drop. However, if profit difference is positive (+${formatMoneyCompact(Math.max(0, profitDiff), currency)}), margin expansion overrides the volume erosion. Recommended.`
            ) : priceVariance < 0 ? (
              `Discounting price by ${Math.abs(priceVariance)}% boosts sales volume (+${Math.abs(volumeChangePct).toFixed(1)}%). Review if profit difference covers the reduced markup.`
            ) : (
              'Adjust the slider to simulate elastic response of inventory items. Food products are inelastic, whereas Apparel is highly elastic.'
            )}
          </p>
        </div>
      </div>
    </section>
  )
}

export default PricingSimulator
