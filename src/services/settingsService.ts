// VIO 83 AI ORCHESTRA - Settings Service
// Sincronizza impostazioni tra frontend e backend

import { buildBackendUrl } from './backendApi';

/**
 * Carica tutte le impostazioni dal backend.
 * Ritorna un dizionario { key: value }.
 */
export async function fetchAllSettings(): Promise<Record<string, string>> {
  const response = await fetch(buildBackendUrl('/settings'), {
    signal: AbortSignal.timeout(3000),
  });
  if (!response.ok) throw new Error(`Backend: ${response.status}`);
  return response.json();
}

/**
 * Salva un singolo setting nel backend.
 */
export async function saveSetting(key: string, value: string): Promise<void> {
  const response = await fetch(
    `${buildBackendUrl('/settings')}/${encodeURIComponent(key)}?value=${encodeURIComponent(value)}`,
    { method: 'PUT', signal: AbortSignal.timeout(3000) },
  );
  if (!response.ok) throw new Error(`Backend: ${response.status}`);
}

/**
 * Salva più settings nel backend (batch best-effort).
 */
export async function saveSettingsBatch(
  settings: Record<string, string>,
): Promise<void> {
  const promises = Object.entries(settings).map(([key, value]) =>
    saveSetting(key, value).catch(() => { }),
  );
  await Promise.allSettled(promises);
}

// Mapping tra chiavi frontend APIKeyConfig.provider → chiave settings backend
const PROVIDER_TO_SETTINGS_KEY: Record<string, string> = {
  claude: 'api_key_claude',
  gpt4: 'api_key_gpt4',
  grok: 'api_key_grok',
  mistral: 'api_key_mistral',
  deepseek: 'api_key_deepseek',
  gemini: 'api_key_gemini',
  groq: 'api_key_groq',
  openrouter: 'api_key_openrouter',
  together: 'api_key_together',
  perplexity: 'api_key_perplexity',
};

/**
 * Salva una API key nel backend.
 */
export async function saveApiKey(provider: string, key: string): Promise<void> {
  const settingsKey = PROVIDER_TO_SETTINGS_KEY[provider] || `api_key_${provider}`;
  await saveSetting(settingsKey, key);
}

/**
 * Carica le API keys dal backend e le ritorna come Record<provider, key>.
 */
export function extractApiKeysFromSettings(
  backendSettings: Record<string, string>,
): Record<string, string> {
  const result: Record<string, string> = {};
  for (const [provider, settingsKey] of Object.entries(PROVIDER_TO_SETTINGS_KEY)) {
    if (backendSettings[settingsKey]) {
      result[provider] = backendSettings[settingsKey];
    }
  }
  return result;
}
