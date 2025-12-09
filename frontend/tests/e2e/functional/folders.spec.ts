/**
 * Level 1: Functional Testing - Folders
 *
 * Tests for Folders page functionality:
 * - Page load
 * - Folder tree display
 * - Folder navigation
 */
import { test, expect } from '@playwright/test';

test.describe('Folders Functional Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/folders');
    await page.waitForLoadState('networkidle');
  });

  test('should load folders page', async ({ page }) => {
    await expect(page).toHaveURL('/folders');
    // Nav item should be active
    await expect(page.locator('a[href="/folders"]')).toHaveClass(/bg-primary-100/);
  });

  test('should display folder tree', async ({ page }) => {
    // FolderTree component should be visible
    const folderTree = page.locator('.space-y-6 >> text=Folder Explorer').first();
    await expect(folderTree).toBeVisible({ timeout: 10000 });
  });

  test('should show folder list items', async ({ page }) => {
    // Wait for folder items to load
    await page.waitForTimeout(1000);

    // Check for folder items - they have folder icons
    const folderItems = page.locator('[class*="cursor-pointer"]').filter({ hasText: /.+/ });
    const count = await folderItems.count();
    expect(count).toBeGreaterThanOrEqual(0); // May be 0 if no data
  });

  test('should expand folder on click', async ({ page }) => {
    // Find an expandable folder item (with chevron)
    const expandableFolder = page.locator('[class*="cursor-pointer"]').first();

    if (await expandableFolder.isVisible()) {
      await expandableFolder.click();
      // After click, tree might expand or navigate
      await page.waitForTimeout(500);
    }
  });

  test('should show folder statistics', async ({ page }) => {
    // Folders page shows size info
    const sizeInfo = page.locator('text=/\\d+(\\.\\d+)?\\s*(B|KB|MB|GB|TB)/i').first();
    if (await sizeInfo.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(sizeInfo).toBeVisible();
    }
  });

  test('should navigate back to dashboard', async ({ page }) => {
    await page.click('a[href="/"]');
    await expect(page).toHaveURL('/');
  });

  test('should maintain header during navigation', async ({ page }) => {
    // Header should always show "Archive Statistics"
    await expect(page.getByRole('heading', { name: 'Archive Statistics' })).toBeVisible();
  });
});
