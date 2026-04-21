import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Prometheus')).toBeVisible({ timeout: 10_000 });
  });

  test('switch to Arquimedes agent (default)', async ({ page }) => {
    await page.getByText('Arquimedes').first().click();
    // Hero shows the math-for-ML headline
    await expect(page.getByText(/Matemática que/i)).toBeVisible();
  });

  test('switch to Atlas agent', async ({ page }) => {
    await page.getByText('Atlas').click();
    await expect(page.getByText(/consultor|GitHub|repos/i)).toBeVisible();
  });

  test('switch to Prometheus', async ({ page }) => {
    await page.getByText('Prometheus').click();
    await expect(page.getByText(/governança|compliance|privacidade|GDPR/i)).toBeVisible();
  });

  test('model dropdown opens and shows options', async ({ page }) => {
    const modelButton = page
      .locator(
        'button:has-text("Qwen"), button:has-text("DeepSeek"), button:has-text("Gemini"), button:has-text("GPT"), button:has-text("Claude")',
      )
      .first();
    await modelButton.click();
    await expect(page.getByText('DeepSeek V3')).toBeVisible();
  });

  test('can select a different model', async ({ page }) => {
    const modelButton = page
      .locator(
        'button:has-text("Qwen"), button:has-text("DeepSeek"), button:has-text("Gemini"), button:has-text("GPT"), button:has-text("Claude")',
      )
      .first();
    await modelButton.click();
    await page.getByText('Gemini 2.0 Flash').first().click();
    await expect(page.getByText('Gemini 2.0 Flash (Google)')).toBeVisible();
  });
});
