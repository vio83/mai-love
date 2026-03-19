import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
  build: {
    target: 'esnext',
    outDir: 'dist',
    chunkSizeWarningLimit: 750,
    // Production optimizations
    sourcemap: false,
    cssMinify: 'lightningcss',
    minify: 'esbuild',
    modulePreload: {
      polyfill: false, // Modern browsers only
    },
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined;

          if (id.includes('framer-motion')) {
            return 'motion';
          }

          if (id.includes('react-markdown') || id.includes('remark-gfm')) {
            return 'markdown';
          }

          if (id.includes('react-syntax-highlighter') || id.includes('prismjs')) {
            return 'syntax';
          }

          if (id.includes('lucide-react')) {
            return 'icons';
          }

          // Group small React ecosystem libs together
          if (id.includes('react') || id.includes('zustand') || id.includes('scheduler')) {
            return 'react-core';
          }

          return undefined;
        },
      },
    },
  },
});
