import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Vite forwards API requests to FastAPI. Keep the backend's 8000 port private.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:8000', '/health': 'http://127.0.0.1:8000' },
  },
});
