import { test, expect } from '@playwright/test';

test.describe('App Loading', () => {
  test('page loads with correct title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Arquimedes/);
  });

  test('sidebar shows all 3 agents', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Prometheus')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('Arquimedes').first()).toBeVisible();
    await expect(page.getByText('Atlas')).toBeVisible();
  });

  test('hero shows Mouts × AmBev brand line', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Arquimedes').first()).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(/Mouts/).first()).toBeVisible();
    await expect(page.getByText(/AmBev/).first()).toBeVisible();
  });

  test('hero example prompts are clickable buttons', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Comece por aqui')).toBeVisible({ timeout: 10_000 });
    const examples = page.locator(
      'button:has-text("autovetores"), button:has-text("MSE"), button:has-text("Bayes")'
    );
    await expect(examples.first()).toBeVisible();
  });

  test('model picker is visible with default model', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Modelo')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(/Qwen|DeepSeek|Gemini|GPT|Claude/)).toBeVisible();
  });

  test('footer shows Mouts × AmBev attribution', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText(/construído para/i)).toBeVisible({ timeout: 10_000 });
  });

  test('new chat button is visible (PT-BR)', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Nova conversa')).toBeVisible({ timeout: 10_000 });
  });

  test('source code link points to GitHub', async ({ page }) => {
    await page.goto('/');
    const link = page.getByRole('link', { name: /Código-fonte/ });
    await expect(link).toHaveAttribute('href', /github\.com/);
  });
});
