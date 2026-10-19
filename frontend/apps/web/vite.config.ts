import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'

// The built SPA is what the API serves in single-host mode.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/v1': { target: 'http://localhost:8000', changeOrigin: true, ws: false },
      // Prefix `/s` would also swallow Vite's `/src`. Only share links are proxied.
      '/s': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: false,
        bypass(req) {
          const url = req.url ?? ''
          if (url === '/s' || url.startsWith('/s/')) return undefined
          return url
        },
      },
    },
  },
})
