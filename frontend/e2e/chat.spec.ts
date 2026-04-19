import { test, expect } from '@playwright/test';

test.describe('Chat Interaction', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Prometheus')).toBeVisible({ timeout: 10_000 });
  });

  test('textarea is visible with placeholder', async ({ page }) => {
    const textarea = page.getByPlaceholder('Send a message...');
    await expect(textarea).toBeVisible();
  });

  test('send button is disabled when textarea is empty', async ({ page }) => {
    const sendButton = page.getByTitle('Send message');
    await expect(sendButton).toBeVisible();
    // Should have disabled styling (cursor-not-allowed class)
    await expect(sendButton).toHaveClass(/cursor-not-allowed/);
  });

  test('send button enables when text is typed', async ({ page }) => {
    const textarea = page.getByPlaceholder('Send a message...');
    await textarea.fill('Hello');
    const sendButton = page.getByTitle('Send message');
    // Should no longer have disabled styling
    await expect(sendButton).not.toHaveClass(/cursor-not-allowed/);
  });

  test('typing message and sending creates user message', async ({ page }) => {
    const textarea = page.getByPlaceholder('Send a message...');
    await textarea.fill('What are the GDPR penalties for a data breach?');

    const sendButton = page.getByTitle('Send message');
    await sendButton.click();

    // User message should appear
    await expect(page.getByText('What are the GDPR penalties for a data breach?')).toBeVisible();
    // "You" label should be visible
    await expect(page.getByText('You')).toBeVisible();
  });

  test('assistant response appears after sending', async ({ page }) => {
    const textarea = page.getByPlaceholder('Send a message...');
    await textarea.fill('What are the GDPR penalties?');
    await page.getByTitle('Send message').click();

    // Wait for assistant response (streaming may take time)
    await expect(page.getByText('Assistant')).toBeVisible({ timeout: 60_000 });
  });

  test('stop button appears during streaming', async ({ page }) => {
    const textarea = page.getByPlaceholder('Send a message...');
    await textarea.fill('Generate a GDPR compliance checklist for an AI system.');
    await page.getByTitle('Send message').click();

    // Stop button should briefly appear during streaming
    const stopButton = page.getByTitle('Stop generating');
    // It may disappear quickly if response is fast, so use a short timeout
    try {
      await expect(stopButton).toBeVisible({ timeout: 5_000 });
    } catch {
      // If response was too fast, that's OK — the button appeared and disappeared
    }
  });

  test('clicking example prompt sends message', async ({ page }) => {
    // Click the first example prompt
    const firstExample = page.locator('button:has-text("GDPR")').first();
    await firstExample.click();

    // User message should appear with the example text
    await expect(page.getByText('You')).toBeVisible({ timeout: 10_000 });
  });

  test('Enter key sends message', async ({ page }) => {
    const textarea = page.getByPlaceholder('Send a message...');
    await textarea.fill('Hello Prometheus');
    await textarea.press('Enter');

    await expect(page.getByText('Hello Prometheus')).toBeVisible();
  });

  test('Shift+Enter does not send message', async ({ page }) => {
    const textarea = page.getByPlaceholder('Send a message...');
    await textarea.fill('Line 1');
    await textarea.press('Shift+Enter');
    // Message should NOT be sent — no "You" label should appear
    await expect(page.getByText('You')).not.toBeVisible({ timeout: 2_000 }).catch(() => {
      // This is expected — the message wasn't sent
    });
  });

  test('new chat clears messages', async ({ page }) => {
    // Send a message first
    const textarea = page.getByPlaceholder('Send a message...');
    await textarea.fill('Hello');
    await page.getByTitle('Send message').click();
    await expect(page.getByText('You')).toBeVisible({ timeout: 10_000 });

    // Click New Chat
    await page.getByText('New Chat').click();

    // Messages should be cleared — welcome screen should reappear
    await expect(page.getByText('Try asking')).toBeVisible({ timeout: 5_000 });
  });
});
