import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Prometheus')).toBeVisible({ timeout: 10_000 });
  });

  test('switch to Archimedes agent', async ({ page }) => {
    await page.getByText('Archimedes').click();
    // Welcome screen should update to Archimedes content
    await expect(page.getByText(/tutor|teaches|ML|Python/i)).toBeVisible();
  });

  test('switch to Atlas agent', async ({ page }) => {
    await page.getByText('Atlas').click();
    await expect(page.getByText(/consultant|GitHub|repos/i)).toBeVisible();
  });

  test('switch back to Prometheus', async ({ page }) => {
    await page.getByText('Atlas').click();
    await page.getByText('Prometheus').click();
    await expect(page.getByText(/governance|compliance|privacy/i)).toBeVisible();
  });

  test('model dropdown opens and shows options', async ({ page }) => {
    // Click the model picker button
    const modelButton = page.locator('button:has-text("Qwen"), button:has-text("DeepSeek"), button:has-text("Gemini"), button:has-text("GPT"), button:has-text("Claude"), button:has-text("Select model")').first();
    await modelButton.click();

    // Should show multiple model options
    await expect(page.getByText('DeepSeek V3')).toBeVisible();
  });

  test('can select a different model', async ({ page }) => {
    const modelButton = page.locator('button:has-text("Qwen"), button:has-text("DeepSeek"), button:has-text("Gemini"), button:has-text("GPT"), button:has-text("Claude"), button:has-text("Select model")').first();
    await modelButton.click();

    await page.getByText('Gemini 2.0 Flash').click();
    // Dropdown should close, selected model should be visible
    await expect(page.getByText('Gemini 2.0 Flash (Google)')).toBeVisible();
  });
});
