/**
 * RetailMind Toast Notification System
 *
 * Usage:
 *   const { showToast } = useToast()
 *   showToast('success', 'Settings saved.')
 *   showToast('error', 'Upload failed — check your file format.')
 *   showToast('warning', 'No data for selected period.')
 *   showToast('info', 'Refreshing intelligence data…')
 */

/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useCallback, useRef } from 'react'

// ── Context ────────────────────────────────────────────────────────────────
const ToastContext = createContext(null)

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>')
  return ctx
}

// ── Provider ───────────────────────────────────────────────────────────────
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const timerRefs = useRef({})

  const dismiss = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
    if (timerRefs.current[id]) {
      clearTimeout(timerRefs.current[id])
      delete timerRefs.current[id]
    }
  }, [])

  const showToast = useCallback((type, message, duration = 4000) => {
    const id = Date.now() + Math.random()
    setToasts(prev => {
      // Max 3 visible at once — drop oldest if needed
      const next = prev.length >= 3 ? prev.slice(1) : prev
      return [...next, { id, type, message }]
    })
    if (duration > 0) {
      timerRefs.current[id] = setTimeout(() => dismiss(id), duration)
    }
    return id
  }, [dismiss])

  return (
    <ToastContext.Provider value={{ showToast, dismiss }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  )
}

// ── Container ──────────────────────────────────────────────────────────────
function ToastContainer({ toasts, onDismiss }) {
  if (toasts.length === 0) return null
  return (
    <div className="toast-container" role="region" aria-label="Notifications" aria-live="polite">
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  )
}

// ── Item ───────────────────────────────────────────────────────────────────
const ICONS = {
  success: '✓',
  error:   '✕',
  warning: '⚠',
  info:    'ℹ',
}

function ToastItem({ toast, onDismiss }) {
  return (
    <div className={`toast toast--${toast.type}`} role="alert">
      <span className="toast__icon" aria-hidden="true">{ICONS[toast.type]}</span>
      <span className="toast__message">{toast.message}</span>
      <button
        className="toast__close"
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss notification"
      >
        ✕
      </button>
    </div>
  )
}
