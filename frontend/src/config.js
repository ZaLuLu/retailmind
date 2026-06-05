// RetailMind Frontend Configuration
// ────────────────────────────────────
// This file is the single source of truth for environment-driven behaviour.
// Import IS_DEMO anywhere to gate auth flows, show banners, and adjust routing.

/** True when the app is running in public demo mode (no auth required). */
export const IS_DEMO = import.meta.env.VITE_DEMO_MODE !== 'false'

/** API base URL — falls back to relative path for Vercel serverless proxy. */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

/** Current environment label. */
export const ENV = import.meta.env.MODE ?? 'production'

/** Demo user display info (shown in banner and avatar). */
export const DEMO_USER = {
  id: '00000000-0000-0000-0000-000000000001',
  email: 'demo@retailmind.com',
  fullName: 'Demo Store',
  storeName: 'RetailMind Demo Store',
  currency: 'USD',
  isOnboarded: true,
}
