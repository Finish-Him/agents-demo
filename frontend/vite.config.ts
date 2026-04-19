import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
  },
  server: {
    port: 5173,
    proxy: {
      '/health': { target: 'http://localhost:8000', changeOrigin: true },
      '/agents': { target: 'http://localhost:8000', changeOrigin: true },
      '/models': { target: 'http://localhost:8000', changeOrigin: true },
      '/chat': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
});
