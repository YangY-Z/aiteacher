import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const backendPort = process.env.BACKEND_PORT ?? '8008'
const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? `http://localhost:${backendPort}`

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: apiProxyTarget,
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
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
})
