import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['tests/frontend/**/*.test.ts'],
    coverage: {
      enabled: true,
      reporter: ['text', 'lcov'],
    },
  },
});
