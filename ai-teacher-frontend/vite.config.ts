import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8008',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes) => {
            if (proxyRes.headers['content-type']?.includes('text/event-stream')) {
              proxyRes.headers['content-encoding'] = 'identity';
              delete proxyRes.headers['content-length'];
            }
          });
        },
      },
      '/media': {
        target: 'http://localhost:8008',
        changeOrigin: true,
      },
    },
  },
})