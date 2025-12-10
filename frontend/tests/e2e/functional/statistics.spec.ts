/**
 * Level 1: Functional Testing - Statistics
 *
 * Tests for Statistics page functionality:
 * - Page load and navigation
 * - File type distribution chart
 * - Storage growth trend chart
 * - Top folders display
 *
 * Issue: #5
 * Block: progress.dashboard
 */
import { test, expect } from '@playwright/test';

test.describe('Statistics Page Functional Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/statistics');
    await page.waitForLoadState('networkidle');
  });

  test('should load statistics page (not placeholder)', async ({ page }) => {
    // Should NOT show "under construction" message
    await expect(page.locator('text=under construction')).not.toBeVisible();

    // Should have Statistics heading or content
    await expect(page.locator('text=Statistics').first()).toBeVisible();
  });

  test('should display statistics cards', async ({ page }) => {
    // Statistics page has 4 stat cards
    const statCardsGrid = page.locator('.grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-4 > div');
    await expect(statCardsGrid).toHaveCount(4, { timeout: 10000 });
  });

  test('should show total files count', async ({ page }) => {
    const filesCard = page.locator('text=Total Files').locator('..');
    await expect(filesCard).toBeVisible();
  });

  test('should show total size', async ({ page }) => {
    const sizeCard = page.locator('text=Total Size').locator('..');
    await expect(sizeCard).toBeVisible();
  });

  test('should display file type distribution chart', async ({ page }) => {
    // Look for pie chart container or "File Type Distribution" heading
    await expect(
      page.locator('text=File Type Distribution')
    ).toBeVisible({ timeout: 10000 });

    // Recharts renders SVG
    const pieChart = page.locator('.recharts-pie');
    await expect(pieChart).toBeVisible({ timeout: 10000 });
  });

  test('should display top folders section', async ({ page }) => {
    await expect(
      page.locator('text=Top Folders')
    ).toBeVisible({ timeout: 10000 });
  });

  test('should display storage growth trend chart', async ({ page }) => {
    await expect(
      page.locator('text=Storage Growth')
    ).toBeVisible({ timeout: 10000 });

    // Recharts line chart
    const lineChart = page.locator('.recharts-line');
    await expect(lineChart).toBeVisible({ timeout: 10000 });
  });

  test('should navigate from dashboard to statistics', async ({ page }) => {
    // Start from dashboard
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Click Statistics nav link
    await page.click('a[href="/statistics"]');
    await expect(page).toHaveURL('/statistics');

    // Should not be placeholder
    await expect(page.locator('text=under construction')).not.toBeVisible();
  });

  test('should highlight Statistics nav item when active', async ({ page }) => {
    const statisticsNavLink = page.locator('a[href="/statistics"]');
    await expect(statisticsNavLink).toHaveClass(/bg-primary-100/);
  });
});
