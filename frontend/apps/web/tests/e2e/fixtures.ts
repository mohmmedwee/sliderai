import { test as base } from '@playwright/test'
import type { Page } from '@playwright/test'

type Fixtures = {
  locale: string
  login: (page: Page, creds: { email: string; password: string }) => Promise<void>
}

export const test = base.extend<Fixtures>({
  locale: async ({}, use, testInfo) => {
    await use(testInfo.project.name.startsWith('ar') ? 'ar' : 'en')
  },
  login: async ({}, use) => {
    // T049 fills this in. The stub keeps the fixture shape stable.
    await use(async () => {})
  },
})

export { expect } from '@playwright/test'
