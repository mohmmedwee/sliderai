import { expect, test } from './fixtures'

test('document direction follows the project language', async ({ page, locale }) => {
  await page.goto('/')
  await expect(page.locator('html')).toHaveAttribute('dir', locale === 'ar' ? 'rtl' : 'ltr')
})
