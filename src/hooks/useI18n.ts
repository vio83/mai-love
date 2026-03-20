import { useCallback } from 'react';
import en from '../i18n/locales/en.json';
import it from '../i18n/locales/it.json';
import { useAppStore } from '../stores/appStore';

type Locale = 'it' | 'en';
type TParams = Record<string, string | number | boolean | null | undefined>;
type TFunction = (key: string, options?: TParams) => string;

const LOCALES = { it, en } as const;

function getByPath(source: unknown, path: string): unknown {
  return path.split('.').reduce<unknown>((acc, part) => {
    if (typeof acc !== 'object' || acc === null) return undefined;
    return (acc as Record<string, unknown>)[part];
  }, source);
}

function interpolate(value: string, options?: TParams): string {
  if (!options) return value;
  return value.replace(/\{\{(\w+)\}\}/g, (_, key: string) => {
    const candidate = options[key];
    return candidate === undefined || candidate === null ? `{{${key}}}` : String(candidate);
  });
}

export function resolveLocaleFromStorage(): Locale {
  try {
    if (typeof window === 'undefined' || !window.localStorage) {
      return 'it'; // SSR/webview default
    }
    const stored = window.localStorage.getItem('vio83-locale');
    return stored === 'en' ? 'en' : 'it';
  } catch {
    // Privacy mode or other storage errors
    return 'it';
  }
}

export function translateForLocale(locale: Locale, key: string, options?: TParams): string {
  const primary = getByPath(LOCALES[locale], key);
  if (typeof primary === 'string') return interpolate(primary, options);

  const fallback = getByPath(LOCALES.it, key);
  if (typeof fallback === 'string') return interpolate(fallback, options);

  return key;
}

export function useI18n() {
  const language = useAppStore((state) => state.settings.language);
  const updateSettings = useAppStore((state) => state.updateSettings);
  const lang: Locale = language === 'en' ? 'en' : 'it';

  const t = useCallback<TFunction>((key, options) => translateForLocale(lang, key, options), [lang]);

  const setLang = useCallback((newLang: Locale) => {
    // Skip if language didn't change
    if (newLang === lang) return;

    updateSettings({ language: newLang });

    // Safely persist preference to localStorage
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem('vio83-locale', newLang);
      }
    } catch {
      // Silently ignore storage errors (privacy mode, quota exceeded, etc)
    }
  }, [lang, updateSettings]);

  return { t, lang, setLang };
}

export type { Locale, TFunction, TParams };
