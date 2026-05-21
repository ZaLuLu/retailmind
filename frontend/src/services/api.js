/**
 * RetailMind API Client
 *
 * Central request() interceptor handles:
 *  - Auth header injection
 *  - Automatic token refresh on 401 (retries original request once)
 *  - Request queuing during refresh (prevents race conditions)
 *  - Structured error normalization (network vs server vs client)
 */

const BASE_URL = 'http://localhost:8000/api/v1'

// ── Token refresh state ────────────────────────────────────────────────────
let isRefreshing = false
let refreshQueue = [] // pending requests waiting for refresh to complete

function onRefreshComplete(newToken) {
  refreshQueue.forEach(resolve => resolve(newToken))
  refreshQueue = []
}

function onRefreshFailed() {
  refreshQueue.forEach(resolve => resolve(null))
  refreshQueue = []
}

async function waitForRefresh() {
  return new Promise(resolve => refreshQueue.push(resolve))
}

// ── Token helpers ──────────────────────────────────────────────────────────
function getToken() {
  return localStorage.getItem('token')
}

function getRefreshToken() {
  return localStorage.getItem('refresh_token')
}

function storeTokens(accessToken, refreshToken) {
  localStorage.setItem('token', accessToken)
  if (refreshToken) localStorage.setItem('refresh_token', refreshToken)
}

function clearTokens() {
  localStorage.removeItem('token')
  localStorage.removeItem('refresh_token')
}

// ── Auth header builder ────────────────────────────────────────────────────
function authHeaders(contentType = 'application/json') {
  const token = getToken()
  return {
    ...(contentType ? { 'Content-Type': contentType } : {}),
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  }
}

// ── Error normalization ────────────────────────────────────────────────────
async function parseError(res) {
  const err = new Error()
  err.status = res.status

  if (res.status >= 500) {
    err.message = 'Server error — please try again'
    err.type = 'server'
    return err
  }

  try {
    const body = await res.json()
    err.message = body.detail || body.message || `Request failed (${res.status})`
  } catch {
    err.message = `Request failed (${res.status})`
  }
  err.type = 'client'
  return err
}

// ── Token refresh ──────────────────────────────────────────────────────────
async function refreshAccessToken() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return null

  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    if (!res.ok) return null
    const data = await res.json()
    storeTokens(data.access_token, data.refresh_token)
    return data.access_token
  } catch {
    return null
  }
}

// ── Central request function ───────────────────────────────────────────────
/**
 * Makes an authenticated API request with automatic token refresh on 401.
 *
 * @param {string} method - HTTP method
 * @param {string} endpoint - API path (e.g. '/retail/summary')
 * @param {object|null} data - Request body (for POST/PATCH)
 * @param {object} options - Additional fetch options
 * @returns {Promise<any>} Parsed JSON response
 */
async function request(method, endpoint, data = null, options = {}) {
  const url = `${BASE_URL}${endpoint}`

  const makeRequest = async (token) => {
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    }
    return fetch(url, {
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    })
  }

  // First attempt
  let res = await makeRequest(getToken())

  // Handle 401 — attempt token refresh
  if (res.status === 401) {
    // Don't refresh if this IS the refresh endpoint (prevents infinite loop)
    if (endpoint === '/auth/refresh') {
      clearTokens()
      window.dispatchEvent(new CustomEvent('auth:logout'))
      const err = new Error('Session expired')
      err.status = 401
      err.type = 'auth'
      throw err
    }

    if (isRefreshing) {
      // Another request is already refreshing — queue this one
      const newToken = await waitForRefresh()
      if (!newToken) {
        const err = new Error('Session expired')
        err.status = 401
        err.type = 'auth'
        throw err
      }
      res = await makeRequest(newToken)
    } else {
      isRefreshing = true
      const newToken = await refreshAccessToken()
      isRefreshing = false

      if (newToken) {
        onRefreshComplete(newToken)
        res = await makeRequest(newToken)
      } else {
        onRefreshFailed()
        clearTokens()
        window.dispatchEvent(new CustomEvent('auth:logout'))
        const err = new Error('Session expired. Please log in again.')
        err.status = 401
        err.type = 'auth'
        throw err
      }
    }
  }

  if (!res.ok) {
    throw await parseError(res)
  }

  // Handle empty responses (204 No Content)
  const contentType = res.headers.get('content-type')
  if (!contentType || !contentType.includes('application/json')) {
    return null
  }

  return res.json()
}

// ── File upload (multipart) ────────────────────────────────────────────────
async function uploadFile(endpoint, file) {
  const url = `${BASE_URL}${endpoint}`
  const formData = new FormData()
  formData.append('file', file)

  const makeUpload = async (token) =>
    fetch(url, {
      method: 'POST',
      headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
      body: formData,
    })

  let res = await makeUpload(getToken())

  if (res.status === 401) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      res = await makeUpload(newToken)
    } else {
      clearTokens()
      window.dispatchEvent(new CustomEvent('auth:logout'))
      const err = new Error('Session expired')
      err.status = 401
      throw err
    }
  }

  if (!res.ok) throw await parseError(res)
  return res.json()
}

// ── Public API ─────────────────────────────────────────────────────────────
export const api = {

  // ── Auth ──────────────────────────────────────────────────────────────────
  login: async (email, password) => {
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      const err = new Error(body.detail || 'Invalid credentials')
      err.status = res.status
      throw err
    }
    const data = await res.json()
    storeTokens(data.access_token, data.refresh_token)
    return data
  },

  demoLogin: async () => {
    const res = await fetch(`${BASE_URL}/auth/demo-login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    if (!res.ok) throw new Error('Demo login failed')
    const data = await res.json()
    storeTokens(data.access_token, data.refresh_token)
    return data
  },

  register: async (email, password) => {
    const res = await fetch(`${BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      const err = new Error(body.detail || 'Registration failed')
      err.status = res.status
      throw err
    }
    return res.json()
  },

  logout: () => {
    clearTokens()
  },

  // ── Generic methods ────────────────────────────────────────────────────────
  get: (endpoint) => request('GET', endpoint),
  post: (endpoint, data) => request('POST', endpoint, data),
  patch: (endpoint, data) => request('PATCH', endpoint, data),
  delete: (endpoint) => request('DELETE', endpoint),

  // ── Retail Stores (Phase 2: Multi-Store Support) ───────────────────────────
  getStores: () => request('GET', '/retail/stores'),
  createStore: (data) => request('POST', '/retail/stores', data),

  // ── Retail Intelligence ────────────────────────────────────────────────────
  /** Full BI summary: KPIs, top products, demand signals, alerts, AI insight */
  getRetailSummary: (period, dateFrom, dateTo, storeId) => {
    let params = []
    if (period) params.push(`period=${period}`)
    if (dateFrom) params.push(`date_from=${dateFrom}`)
    if (dateTo) params.push(`date_to=${dateTo}`)
    if (storeId) params.push(`store_id=${storeId}`)
    const query = params.length ? `?${params.join('&')}` : ''
    return request('GET', `/retail/summary${query}`)
  },

  /** Paginated sales ledger */
  getRetailSales: (limit = 100, offset = 0, search = '', category = '', dateFrom = '', dateTo = '', storeId = '') => {
    let params = [`limit=${limit}`, `offset=${offset}`]
    if (search) params.push(`search=${encodeURIComponent(search)}`)
    if (category && category !== 'All') params.push(`category=${encodeURIComponent(category)}`)
    if (dateFrom) params.push(`date_from=${dateFrom}`)
    if (dateTo) params.push(`date_to=${dateTo}`)
    if (storeId) params.push(`store_id=${storeId}`)
    return request('GET', `/retail/sales?${params.join('&')}`)
  },

  /** Upload CSV/XLSX of sales records */
  uploadSalesCsv: (file, storeId) => {
    const url = storeId ? `/retail/upload-csv?store_id=${storeId}` : '/retail/upload-csv'
    return uploadFile(url, file)
  },

  /** URL for template CSV download (no auth needed) */
  getTemplateCsvUrl: () => `${BASE_URL}/retail/template-csv`,

  /** Demand forecast — next 7 days per product (Phase 2) */
  getRetailForecast: (storeId) => {
    const query = storeId ? `?store_id=${storeId}` : ''
    return request('GET', `/retail/forecast${query}`)
  },

  /** Export filtered ledger as CSV (Phase 2) */
  getExportCsvUrl: (params = '', storeId = '') => {
    let finalParams = params || ''
    if (storeId) {
      finalParams = finalParams ? `${finalParams}&store_id=${storeId}` : `?store_id=${storeId}`
    }
    return `${BASE_URL}/retail/export-csv${finalParams}`
  },

  // ── User settings ──────────────────────────────────────────────────────────
  updateUserSettings: (data) => request('PATCH', '/users/me', data),

  // ── AI Advisor ─────────────────────────────────────────────────────────────
  askAdvisor: (question) => request('POST', '/advisor/ask', { question }),
}
