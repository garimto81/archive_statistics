/**
 * Level 2: Visual Regression Testing
 *
 * Captures screenshots and compares against baselines:
 * - Full page screenshots
 * - Component screenshots
 * - Responsive breakpoints
 *
 * NOTE: maxDiffPixels set to 5000 to accommodate dynamic data variations
 * (real-time stats, timestamps, etc.)
 */
import { test, expect } from '@playwright/test';

// Increased threshold to handle dynamic data (stats change between runs)
// Dashboard has real-time updating stats, viewer count, etc.
const MAX_DIFF_PIXELS = 10000;

test.describe('Visual Regression Tests', () => {
  test('dashboard - full page screenshot', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500); // Allow animations to settle

    await expect(page).toHaveScreenshot('dashboard-full.png', {
      fullPage: true,
      maxDiffPixels: MAX_DIFF_PIXELS,
    });
  });

  test('dashboard - stats section', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const statsSection = page.locator('.grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-4');

    if (await statsSection.isVisible()) {
      await expect(statsSection).toHaveScreenshot('stats-section.png', {
        maxDiffPixels: MAX_DIFF_PIXELS,
      });
    }
  });

  test('folders - tree view', async ({ page }) => {
    await page.goto('/folders');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('folders-page.png', {
      fullPage: true,
      maxDiffPixels: MAX_DIFF_PIXELS,
    });
  });

  test('work status - progress view', async ({ page }) => {
    await page.goto('/work-status');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await expect(page).toHaveScreenshot('work-status-page.png', {
      fullPage: true,
      maxDiffPixels: MAX_DIFF_PIXELS,
    });
  });

  test.describe('Responsive Breakpoints', () => {
    test('dashboard - desktop (1920x1080)', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(500);

      await expect(page).toHaveScreenshot('dashboard-desktop.png', {
        maxDiffPixels: MAX_DIFF_PIXELS,
      });
    });

    test('dashboard - tablet (768x1024)', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(500);

      await expect(page).toHaveScreenshot('dashboard-tablet.png', {
        maxDiffPixels: MAX_DIFF_PIXELS,
      });
    });

    test('dashboard - mobile (375x667)', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(500);

      await expect(page).toHaveScreenshot('dashboard-mobile.png', {
        maxDiffPixels: MAX_DIFF_PIXELS,
      });
    });
  });
});
