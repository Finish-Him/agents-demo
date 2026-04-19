import { test, expect } from '@playwright/test';

test.describe('App Loading', () => {
  test('page loads with correct title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Agents Demo/);
  });

  test('sidebar shows all 3 agents', async ({ page }) => {
    await page.goto('/');
    // Wait for agents to load from API
    await expect(page.getByText('Prometheus')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('Archimedes')).toBeVisible();
    await expect(page.getByText('Atlas')).toBeVisible();
  });

  test('welcome screen shows active agent info', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Prometheus')).toBeVisible({ timeout: 10_000 });
    // Welcome screen should show agent description
    await expect(page.getByText(/governance|compliance|privacy/i)).toBeVisible();
  });

  test('example prompts are clickable buttons', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Prometheus')).toBeVisible({ timeout: 10_000 });
    // Should have "Try asking" section with example buttons
    await expect(page.getByText('Try asking')).toBeVisible();
    const examples = page.locator('button:has-text("GDPR"), button:has-text("EU AI Act"), button:has-text("compliance")');
    await expect(examples.first()).toBeVisible();
  });

  test('model picker is visible and has default model', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Model')).toBeVisible({ timeout: 10_000 });
    // Should show a model name in the picker
    await expect(page.getByText(/Qwen|DeepSeek|Gemini|GPT|Claude/)).toBeVisible();
  });

  test('footer shows attribution', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Prometheus')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(/Moises Alves/)).toBeVisible();
  });

  test('new chat button is visible', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('New Chat')).toBeVisible({ timeout: 10_000 });
  });

  test('source code link points to GitHub', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Prometheus')).toBeVisible({ timeout: 10_000 });
    const link = page.getByRole('link', { name: /Source Code/ });
    await expect(link).toHaveAttribute('href', /github\.com/);
  });
});
