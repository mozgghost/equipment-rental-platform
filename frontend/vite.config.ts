import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  envDir: '..',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:8001', '/healthz': 'http://localhost:8001' },
  },
});
