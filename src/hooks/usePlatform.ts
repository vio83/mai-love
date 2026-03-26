// VIO 83 AI ORCHESTRA — Platform Detection Hook
// Rileva se l'app è in esecuzione su mobile (Tauri iOS/Android) o desktop
import { useCallback, useEffect, useState } from 'react';

export type Platform = 'desktop' | 'ios' | 'android' | 'web';

interface PlatformInfo {
  platform: Platform;
  isMobile: boolean;
  isDesktop: boolean;
  isTauri: boolean;
  isSmallScreen: boolean;
  screenWidth: number;
  screenHeight: number;
  safeAreaTop: number;
  safeAreaBottom: number;
}

/** Breakpoints (px) */
const MOBILE_BREAKPOINT = 768;

function detectPlatform(): Platform {
  // Tauri injects __TAURI_INTERNALS__ on the window object
  const hasTauri = typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;

  if (hasTauri) {
    const ua = navigator.userAgent.toLowerCase();
    if (ua.includes('iphone') || ua.includes('ipad') || ua.includes('ipod')) return 'ios';
    if (ua.includes('android')) return 'android';
    return 'desktop';
  }

  // Fallback: browser detection for web builds
  if (typeof window !== 'undefined') {
    const ua = navigator.userAgent.toLowerCase();
    if (/iphone|ipad|ipod/.test(ua)) return 'ios';
    if (/android/.test(ua)) return 'android';
  }

  return 'web';
}

function getSafeArea(): { top: number; bottom: number } {
  if (typeof document === 'undefined') return { top: 0, bottom: 0 };
  const style = getComputedStyle(document.documentElement);
  const top = parseInt(style.getPropertyValue('env(safe-area-inset-top)') || '0', 10) || 0;
  const bottom = parseInt(style.getPropertyValue('env(safe-area-inset-bottom)') || '0', 10) || 0;
  return { top, bottom };
}

export function usePlatform(): PlatformInfo {
  const [info, setInfo] = useState<PlatformInfo>(() => {
    const platform = detectPlatform();
    const w = typeof window !== 'undefined' ? window.innerWidth : 1280;
    const h = typeof window !== 'undefined' ? window.innerHeight : 800;
    const sa = getSafeArea();
    return {
      platform,
      isMobile: platform === 'ios' || platform === 'android',
      isDesktop: platform === 'desktop',
      isTauri: platform !== 'web',
      isSmallScreen: w < MOBILE_BREAKPOINT,
      screenWidth: w,
      screenHeight: h,
      safeAreaTop: sa.top,
      safeAreaBottom: sa.bottom,
    };
  });

  const handleResize = useCallback(() => {
    const w = window.innerWidth;
    const h = window.innerHeight;
    const sa = getSafeArea();
    setInfo((prev) => ({
      ...prev,
      isSmallScreen: w < MOBILE_BREAKPOINT,
      screenWidth: w,
      screenHeight: h,
      safeAreaTop: sa.top,
      safeAreaBottom: sa.bottom,
    }));
  }, []);

  useEffect(() => {
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [handleResize]);

  return info;
}
