import { describe, expect, it } from 'vitest';

/**
 * Smoke test: verifica che tutti i moduli pagina presenti
 * siano importabili senza errori di compilazione.
 */

describe('Page modules — static import check', () => {
  it('imports RagPage', async () => {
    const mod = await import('../../src/pages/RagPage');
    expect(mod.default).toBeDefined();
    expect(typeof mod.default).toBe('function');
  });

  it('imports CrossCheckPage', async () => {
    const mod = await import('../../src/pages/CrossCheckPage');
    expect(mod.default).toBeDefined();
  });

  it('imports WorkflowPage', async () => {
    const mod = await import('../../src/pages/WorkflowPage');
    expect(mod.default).toBeDefined();
  });

  it('imports AnalyticsPage', async () => {
    const mod = await import('../../src/pages/AnalyticsPage');
    expect(mod.default).toBeDefined();
  });

  it('imports ModelsPage', async () => {
    const mod = await import('../../src/pages/ModelsPage');
    expect(mod.default).toBeDefined();
  });

  it('imports DashboardPage', async () => {
    const mod = await import('../../src/pages/DashboardPage');
    expect(mod.default).toBeDefined();
  });

  it('imports AuthPage', async () => {
    const mod = await import('../../src/pages/AuthPage');
    expect(mod.default).toBeDefined();
  });

  it('imports PrivacyPage', async () => {
    const mod = await import('../../src/pages/PrivacyPage');
    expect(mod.default).toBeDefined();
  });

  it('imports OrchestraRuntimePage', async () => {
    const mod = await import('../../src/pages/OrchestraRuntimePage');
    expect(mod.default).toBeDefined();
  });

  it('imports PluginsPage', async () => {
    const mod = await import('../../src/pages/PluginsPage');
    expect(mod.default).toBeDefined();
  });

  it('imports OpenClawPage', async () => {
    const mod = await import('../../src/pages/OpenClawPage');
    expect(mod.default).toBeDefined();
  });
});
