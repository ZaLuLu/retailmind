const EXCHANGE_RATES = {
  INR: 1.0,
  USD: 0.012,  // 1 INR = 0.012 USD
  EUR: 0.011,  // 1 INR = 0.011 EUR
  GBP: 0.0095, // 1 INR = 0.0095 GBP
  AED: 0.044,  // 1 INR = 0.044 AED
}

const CURRENCY_SYMBOLS = {
  INR: '₹',
  USD: '$',
  EUR: '€',
  GBP: '£',
  AED: 'د.إ'
}

export const convertMoney = (val, toCurrency = 'INR') => {
  if (val == null) return 0
  const rate = EXCHANGE_RATES[toCurrency] || 1.0
  return val * rate
}

export const formatMoneyCompact = (val, currency = 'INR', convert = true) => {
  if (val == null) return '—'
  const convertedVal = convert ? convertMoney(val, currency) : val
  const sym = CURRENCY_SYMBOLS[currency] || currency

  if (currency === 'INR') {
    if (convertedVal >= 1_00_00_000) return `${sym}${(convertedVal / 1_00_00_000).toFixed(1)}Cr`
    if (convertedVal >= 1_00_000)   return `${sym}${(convertedVal / 1_00_000).toFixed(1)}L`
    if (convertedVal >= 1_000)      return `${sym}${(convertedVal / 1_000).toFixed(1)}K`
    return `${sym}${convertedVal.toFixed(0)}`
  } else {
    // Standard Western Million / Thousand
    if (convertedVal >= 1_000_000) return `${sym}${(convertedVal / 1_000_000).toFixed(1)}M`
    if (convertedVal >= 1_000)     return `${sym}${(convertedVal / 1_000).toFixed(1)}K`
    return `${sym}${convertedVal.toFixed(0)}`
  }
}

export const formatMoneyDetailed = (val, currency = 'INR', convert = true) => {
  if (val == null) return '—'
  const convertedVal = convert ? convertMoney(val, currency) : val
  const sym = CURRENCY_SYMBOLS[currency] || currency
  
  return `${sym}${Number(convertedVal).toLocaleString(currency === 'INR' ? 'en-IN' : 'en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`
}
