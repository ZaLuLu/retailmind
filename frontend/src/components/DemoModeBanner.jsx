import React from 'react'
import { IS_DEMO } from '../config'
import './DemoModeBanner.css'

/**
 * DemoModeBanner
 * ──────────────
 * Fixed 36px top banner shown on every page in demo mode.
 * - NOT dismissible (demo mode is always explicit)
 * - Shows "Upload Your Data" CTA → opens Data Import page
 * - Shows "Restore Demo Data" if user has uploaded their own file
 *
 * @param {Object} props
 * @param {() => void} props.onUpload — opens the Data Import / reset flow
 * @param {boolean} props.hasCustomData — true if user uploaded their own file
 * @param {() => void} props.onRestore — restores original seeded demo data
 */
export default function DemoModeBanner({ onUpload, hasCustomData, onRestore }) {
  if (!IS_DEMO) return null

  return (
    <div className="demo-banner" role="banner" aria-label="Demo mode notification">
      <div className="demo-banner__content">
        <span className="demo-banner__icon" aria-hidden="true">👁</span>
        <span className="demo-banner__text">
          <strong>DEMO MODE</strong>
          <span className="demo-banner__sep">·</span>
          Showing 90-day sample dataset
        </span>

        <div className="demo-banner__actions">
          <button
            id="demo-upload-btn"
            className="demo-banner__cta"
            onClick={onUpload}
            aria-label="Upload your own sales data"
          >
            Upload Your Data
          </button>

          {hasCustomData && (
            <button
              id="demo-restore-btn"
              className="demo-banner__restore"
              onClick={onRestore}
              aria-label="Restore original demo data"
            >
              ← Restore Demo Data
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
