import { test } from '@playwright/test';
test.setTimeout(120_000);
test('mouts × ambev visual identity hero', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle' });
  await page.waitForSelector('text=Arquimedes', { timeout: 15_000 });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: '/tmp/hero.png', fullPage: false });
});
test('concepts modal pt-br', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await page.getByRole('button', { name: /como funciona/i }).click();
  await page.waitForSelector('text=9 conceitos', { timeout: 10_000 });
  await page.waitForTimeout(800);
  await page.screenshot({ path: '/tmp/concepts.png', fullPage: false });
});
