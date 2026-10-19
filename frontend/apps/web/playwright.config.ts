import { defineConfig, devices } from '@playwright/test'

const arStorage = 'tests/e2e/ar-storage.json'
// 5173 is the card's port. This machine already serves another app there, so the
// smoke server uses 5174. CI can set PLAYWRIGHT_PORT=5173.
const port = process.env.PLAYWRIGHT_PORT ?? '5174'
const baseURL = `http://127.0.0.1:${port}`

export default defineConfig({
  testDir: 'tests/e2e',
  fullyParallel: true,
  use: {
    baseURL,
    trace: 'on-first-retry',
  },
  webServer: {
    command: `pnpm exec vite --host 127.0.0.1 --port ${port} --strictPort`,
    url: baseURL,
    reuseExistingServer: false,
  },
  projects: [
    {
      name: 'en-desktop',
      use: { viewport: { width: 1440, height: 900 }, locale: 'en-US' },
    },
    {
      name: 'ar-desktop',
      use: {
        viewport: { width: 1440, height: 900 },
        locale: 'ar-SA',
        storageState: arStorage,
      },
    },
    {
      name: 'en-mobile',
      use: { ...devices['iPhone 14'], locale: 'en-US' },
    },
    {
      name: 'ar-mobile',
      use: { ...devices['iPhone 14'], locale: 'ar-SA', storageState: arStorage },
    },
  ],
})
