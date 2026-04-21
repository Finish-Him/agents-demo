import { test } from '@playwright/test';

test.setTimeout(60_000);
test('concepts panel opens + shows 9 PT-BR cards', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.getByText('Arquimedes').first().waitFor({ timeout: 15_000 });
  await page.getByRole('button', { name: /como funciona/i }).click();
  await page.getByText('9 conceitos de AI Engineering').waitFor();
  await page.screenshot({ path: '/tmp/concepts.png', fullPage: true });
});
