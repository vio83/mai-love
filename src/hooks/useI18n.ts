import { useCallback } from 'react';
import en from '../i18n/locales/en.json';
import it from '../i18n/locales/it.json';
import { useAppStore } from '../stores/appStore';

type Locale = 'it' | 'en';
type TParams = Record<string, string | number | boolean | null | undefined>;
type TFunction = (key: string, options?: TParams) => string;

const LOCALES = { it, en } as const;
const STORAGE_KEY = 'vio83-locale';
const MAX_CACHE_ENTRIES_PER_LOCALE = 1024;
const TRANSLATION_CACHE: Record<Locale, Map<string, string>> = {
  it: new Map<string, string>(),
  en: new Map<string, string>(),
};
const PATH_SEGMENTS_CACHE = new Map<string, string[]>();

function getPathSegments(path: string): string[] {
  const cached = PATH_SEGMENTS_CACHE.get(path);
  if (cached) return cached;
  const segments = path.split('.');
  PATH_SEGMENTS_CACHE.set(path, segments);
  return segments;
}

function getByPath(source: unknown, path: string): unknown {
  return getPathSegments(path).reduce<unknown>((acc, part) => {
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

function resolveRawTranslation(locale: Locale, key: string): string | undefined {
  const cache = TRANSLATION_CACHE[locale];
  const cached = cache.get(key);
  if (cached !== undefined) return cached;

  const primary = getByPath(LOCALES[locale], key);
  if (typeof primary === 'string') {
    if (cache.size >= MAX_CACHE_ENTRIES_PER_LOCALE) {
      const oldestKey = cache.keys().next().value;
      if (oldestKey) cache.delete(oldestKey);
    }
    cache.set(key, primary);
    return primary;
  }

  const fallback = getByPath(LOCALES.it, key);
  if (typeof fallback === 'string') {
    if (cache.size >= MAX_CACHE_ENTRIES_PER_LOCALE) {
      const oldestKey = cache.keys().next().value;
      if (oldestKey) cache.delete(oldestKey);
    }
    cache.set(key, fallback);
    return fallback;
  }

  return undefined;
}

export function resolveLocaleFromStorage(): Locale {
  if (typeof window === 'undefined') return 'it';
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === 'en' ? 'en' : 'it';
  } catch {
    return 'it';
  }
}

export function translateForLocale(locale: Locale, key: string, options?: TParams): string {
  const resolved = resolveRawTranslation(locale, key);
  if (!resolved) return key;
  return interpolate(resolved, options);
}

export function useI18n() {
  const language = useAppStore((state) => state.settings.language);
  const updateSettings = useAppStore((state) => state.updateSettings);
  const lang: Locale = language === 'en' ? 'en' : 'it';

  const t = useCallback<TFunction>((key, options) => translateForLocale(lang, key, options), [lang]);

  const setLang = useCallback((newLang: Locale) => {
    if (newLang === lang) return;
    updateSettings({ language: newLang });
    if (typeof window === 'undefined') return;
    try {
      window.localStorage.setItem(STORAGE_KEY, newLang);
    } catch {
      // Ignore storage errors (e.g., privacy mode)
    }
  }, [lang, updateSettings]);

  return { t, lang, setLang };
}

export type { Locale, TFunction, TParams };
