import { describe, expect, it } from 'vitest';
import { classifyRequest, resolveGenerationBudget, routeToProvider } from '../../src/services/ai/orchestrator';

describe('classifyRequest — intent detection', () => {
  // Code
  it('classifies Python code request', () => expect(classifyRequest('scrivi codice Python')).toBe('code'));
  it('classifies debug request', () => expect(classifyRequest('debug this function')).toBe('code'));
  it('classifies SQL request', () => expect(classifyRequest('ottimizza questa query SQL')).toBe('code'));
  it('classifies React request', () => expect(classifyRequest('crea un componente React')).toBe('code'));

  // Legal
  it('classifies GDPR request', () => expect(classifyRequest('clausola GDPR compliance')).toBe('legal'));
  it('classifies contract request', () => expect(classifyRequest('analizza questo contratto')).toBe('legal'));

  // Medical
  it('classifies clinical request', () => expect(classifyRequest('diagnosi differenziale diabete')).toBe('medical'));
  it('classifies treatment request', () => expect(classifyRequest('terapia per paziente oncologico')).toBe('medical'));

  // Creative
  it('classifies poetry request', () => expect(classifyRequest('scrivi una poesia')).toBe('creative'));
  it('classifies story request', () => expect(classifyRequest('write a short story')).toBe('creative'));

  // Reasoning
  it('classifies explanation request', () => expect(classifyRequest('spiega la teoria della relatività')).toBe('reasoning'));
  it('classifies why request', () => expect(classifyRequest('perché il cielo è blu')).toBe('reasoning'));

  // Research
  it('classifies research request', () => expect(classifyRequest('deep research sullo stato dell\'arte')).toBe('research'));

  // Conversation fallback
  it('classifies greeting as conversation', () => expect(classifyRequest('ciao come stai')).toBe('conversation'));
  it('classifies empty as conversation', () => expect(classifyRequest('')).toBe('conversation'));
});

describe('routeToProvider — cloud routing', () => {
  it('routes code to claude', () => expect(routeToProvider('code', 'cloud')).toBe('claude'));
  it('routes research to perplexity', () => expect(routeToProvider('research', 'cloud')).toBe('perplexity'));
  it('routes creative to gpt4', () => expect(routeToProvider('creative', 'cloud')).toBe('gpt4'));
  it('routes realtime to grok', () => expect(routeToProvider('realtime', 'cloud')).toBe('grok'));
  it('routes reasoning to claude', () => expect(routeToProvider('reasoning', 'cloud')).toBe('claude'));
  it('routes conversation to claude', () => expect(routeToProvider('conversation', 'cloud')).toBe('claude'));
});

describe('routeToProvider — local routing always returns ollama', () => {
  const types = ['code', 'legal', 'medical', 'writing', 'research', 'creative', 'reasoning', 'conversation'] as const;
  types.forEach(t => {
    it(`routes ${t} local → ollama`, () => expect(routeToProvider(t, 'local')).toBe('ollama'));
  });
});

describe('resolveGenerationBudget', () => {
  // Normal mode
  it('short message normal → 160', () => expect(resolveGenerationBudget(50, false)).toBe(160));
  it('medium message normal → 288', () => expect(resolveGenerationBudget(200, false)).toBe(288));
  it('long message normal → 448', () => expect(resolveGenerationBudget(500, false)).toBe(448));
  it('boundary 120 normal → 160', () => expect(resolveGenerationBudget(120, false)).toBe(160));
  it('boundary 400 normal → 288', () => expect(resolveGenerationBudget(400, false)).toBe(288));

  // Deep mode
  it('short message deep → 320', () => expect(resolveGenerationBudget(50, true)).toBe(320));
  it('medium message deep → 512', () => expect(resolveGenerationBudget(200, true)).toBe(512));
  it('long message deep → 768', () => expect(resolveGenerationBudget(500, true)).toBe(768));
  it('boundary 120 deep → 320', () => expect(resolveGenerationBudget(120, true)).toBe(320));
  it('boundary 400 deep → 512', () => expect(resolveGenerationBudget(400, true)).toBe(512));
});
