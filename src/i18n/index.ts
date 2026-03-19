// ============================================================
// VIO 83 AI ORCHESTRA — i18n Configuration
// Copyright (c) 2026 Viorica Porcu (vio83) — AGPL-3.0
//
// Supported languages: Italian (it), English (en)
// Auto-detects browser/OS language on first launch.
// Persists selected language in localStorage.
//
// INSTALL DEPENDENCY (run once on Mac):
//   npm install react-i18next i18next i18next-browser-languagedetector
// ============================================================

/**
 * NOTE: This module uses react-i18next.
 * If the package is not yet installed, run:
 *   npm install react-i18next i18next i18next-browser-languagedetector
 *
 * The app will fall back gracefully to Italian if i18next is not available.
 */

import enTranslations from './locales/en.json';
import itTranslations from './locales/it.json';

// Graceful import — avoids hard crash if package not yet installed
let i18nReady = false;

// Translation resources bundled at build-time (no network requests)
export const resources = {
  it: { translation: null as unknown },
  en: { translation: null as unknown },
};

// Supported languages
export const SUPPORTED_LANGUAGES = [
  { code: 'it', label: 'Italiano', flag: '🇮🇹' },
  { code: 'en', label: 'English', flag: '🇬🇧' },
] as const;

export type SupportedLocale = 'it' | 'en';

export const DEFAULT_LOCALE: SupportedLocale = 'it';
export const FALLBACK_LOCALE: SupportedLocale = 'it';

/**
 * Detect locale from browser/OS.
 * Falls back to DEFAULT_LOCALE if not supported.
 */
export function detectLocale(): SupportedLocale {
  const stored = localStorage.getItem('vio83-locale');
  if (stored === 'it' || stored === 'en') return stored;

  const browserLang = (navigator.language || 'it').split('-')[0].toLowerCase();
  if (browserLang === 'en') return 'en';
  return 'it'; // Default to Italian (primary user language)
}

/**
 * Persist locale preference.
 */
export function setStoredLocale(locale: SupportedLocale): void {
  localStorage.setItem('vio83-locale', locale);
}

/**
 * Async initializer — call this before rendering the app.
 * Dynamically imports react-i18next to avoid hard crash if not installed.
 */
export async function initI18n(): Promise<boolean> {
  try {
    // Dynamic import so TypeScript doesn't error if package missing
    const i18nModule = await import('i18next');

    const i18n = i18nModule.default;
    const { initReactI18next } = await import('react-i18next');
    const LanguageDetector = (await import('i18next-browser-languagedetector')).default;

    await i18n
      .use(LanguageDetector)
      .use(initReactI18next)
      .init({
        resources: {
          it: { translation: itTranslations },
          en: { translation: enTranslations },
        },
        lng: detectLocale(),
        fallbackLng: FALLBACK_LOCALE,
        supportedLngs: ['it', 'en'],
        interpolation: {
          escapeValue: false, // React handles XSS
        },
        detection: {
          order: ['localStorage', 'navigator'],
          caches: ['localStorage'],
          lookupLocalStorage: 'vio83-locale',
        },
        debug: import.meta.env.DEV,
      });

    i18nReady = true;
    console.log('[VIO i18n] Initialized. Locale:', i18n.language);
    return true;
  } catch (err) {
    // Graceful degradation — app works without i18n (Italian hardcoded)
    console.warn('[VIO i18n] react-i18next not available. Run: npm install react-i18next i18next i18next-browser-languagedetector');
    console.warn('[VIO i18n] Continuing with hardcoded Italian strings.', err);
    return false;
  }
}

export { i18nReady };
