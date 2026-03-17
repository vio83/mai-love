import { describe, expect, it } from 'vitest';
import { classifyRequest, resolveGenerationBudget, routeToProvider } from '../../src/services/ai/orchestrator';

describe('orchestrator helpers', () => {
  it('classifies code requests correctly', () => {
    expect(classifyRequest('Puoi debuggare questa funzione TypeScript?')).toBe('code');
  });

  it('classifies medical requests correctly', () => {
    expect(classifyRequest('Riassumi le linee guida cliniche per un paziente oncologico')).toBe('medical');
  });

  it('routes every local request to Ollama', () => {
    expect(routeToProvider('research', 'local')).toBe('ollama');
    expect(routeToProvider('code', 'local')).toBe('ollama');
  });

  it('uses tighter budgets outside deep mode', () => {
    expect(resolveGenerationBudget(80, false)).toBe(160);
    expect(resolveGenerationBudget(220, false)).toBe(288);
    expect(resolveGenerationBudget(900, false)).toBe(448);
  });

  it('expands budget in deep mode without exceeding configured tiers', () => {
    expect(resolveGenerationBudget(80, true)).toBe(320);
    expect(resolveGenerationBudget(220, true)).toBe(512);
    expect(resolveGenerationBudget(900, true)).toBe(768);
  });
});
