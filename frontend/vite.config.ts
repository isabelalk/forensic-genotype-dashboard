import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Read from the dev server's environment only; a VITE_ prefix would leak it into the browser bundle.
const backendSharedSecret = process.env.BACKEND_SHARED_SECRET

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:3002',
        changeOrigin: true,
        configure: (proxy) => {
          if (!backendSharedSecret) return
          proxy.on('proxyReq', (proxyReq) => {
            proxyReq.setHeader('X-Internal-Token', backendSharedSecret)
          })
        },
      }
    }
  }
})
