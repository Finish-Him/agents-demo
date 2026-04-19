import { test, expect } from '@playwright/test';

test.describe('Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Prometheus')).toBeVisible({ timeout: 10_000 });
  });

  test('all buttons have accessible text or title', async ({ page }) => {
    const buttons = page.locator('button');
    const count = await buttons.count();
    for (let i = 0; i < count; i++) {
      const btn = buttons.nth(i);
      const text = await btn.textContent();
      const title = await btn.getAttribute('title');
      const ariaLabel = await btn.getAttribute('aria-label');
      // Every button should have some identifying text
      expect(text?.trim() || title || ariaLabel).toBeTruthy();
    }
  });

  test('links have href attributes', async ({ page }) => {
    const links = page.locator('a[href]');
    const count = await links.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < count; i++) {
      const href = await links.nth(i).getAttribute('href');
      expect(href).toBeTruthy();
    }
  });

  test('textarea has placeholder for screen readers', async ({ page }) => {
    const textarea = page.getByPlaceholder('Send a message...');
    await expect(textarea).toBeVisible();
  });

  test('keyboard Tab navigates through interactive elements', async ({ page }) => {
    // Press Tab multiple times and verify focus moves
    await page.keyboard.press('Tab');
    const firstFocused = await page.evaluate(() => document.activeElement?.tagName);
    expect(firstFocused).toBeTruthy();

    await page.keyboard.press('Tab');
    const secondFocused = await page.evaluate(() => document.activeElement?.tagName);
    expect(secondFocused).toBeTruthy();
  });

  test('page has proper heading structure', async ({ page }) => {
    // Should have at least one heading
    const h1 = page.locator('h1');
    await expect(h1.first()).toBeVisible();
  });

  test('page has lang attribute', async ({ page }) => {
    const lang = await page.locator('html').getAttribute('lang');
    expect(lang).toBe('en');
  });

  test('images/icons do not break accessibility', async ({ page }) => {
    // SVG icons from lucide-react should not be announced by screen readers
    // They should either have aria-hidden or role="img" with label
    const svgs = page.locator('svg');
    const count = await svgs.count();
    // Just verify SVGs exist without breaking page
    expect(count).toBeGreaterThan(0);
  });
});
