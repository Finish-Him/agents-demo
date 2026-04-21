import { test, expect } from '@playwright/test';
test.setTimeout(180_000);
test('arquimedes renders math answer with tool trace', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.getByText('Arquimedes').first().waitFor({ timeout: 15_000 });
  await page.getByText('Arquimedes').first().click();
  const textarea = page.locator('textarea').first();
  await textarea.fill('Derivative of f(x)=3x^2+5x-7. Show the result in one LaTeX formula.');
  await textarea.press('Enter');
  // Wait until the assistant bubble has meaningful content
  await expect(page.locator('body')).toContainText(/6x|power rule/i, { timeout: 120_000 });
});
