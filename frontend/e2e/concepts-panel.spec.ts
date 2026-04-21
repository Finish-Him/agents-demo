import { test } from '@playwright/test';
test.setTimeout(60_000);
test('concepts panel opens + shows 9 concepts', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.getByText('Archimedes').first().waitFor({ timeout: 15_000 });
  await page.getByRole('button', { name: /how it works/i }).click();
  await page.getByText('9 AI Engineering Concepts').waitFor();
  await page.screenshot({ path: '/tmp/concepts.png', fullPage: true });
});
