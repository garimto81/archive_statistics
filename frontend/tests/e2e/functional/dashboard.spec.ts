/**
 * Level 1: Functional Testing - Dashboard
 *
 * Tests for Dashboard page functionality:
 * - Page load and navigation
 * - Statistics display
 * - Scan trigger
 */
import { test, expect } from '@playwright/test';

test.describe('Dashboard Functional Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should load dashboard page', async ({ page }) => {
    await expect(page).toHaveTitle(/Archive Statistics/);
    // Header contains "Archive Statistics" title
    await expect(page.getByRole('heading', { name: 'Archive Statistics' })).toBeVisible();
  });

  test('should display statistics cards', async ({ page }) => {
    // Dashboard has 4 stat cards in the top grid
    const statCardsGrid = page.locator('.grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-4 > div');
    await expect(statCardsGrid).toHaveCount(4, { timeout: 10000 });
  });

  test('should show total files count', async ({ page }) => {
    // Find the stat card with "Total Files" title
    const filesCard = page.locator('text=Total Files').locator('..');
    await expect(filesCard).toBeVisible();
    // Should have a numeric value
    const value = filesCard.locator('.text-2xl.font-bold');
    await expect(value).toBeVisible();
  });

  test('should show total size', async ({ page }) => {
    // Find the stat card with "Total Size" title
    const sizeCard = page.locator('text=Total Size').locator('..');
    await expect(sizeCard).toBeVisible();
  });

  test('should show media duration', async ({ page }) => {
    // Find the stat card with "Media Duration" title
    const durationCard = page.locator('text=Media Duration').locator('..');
    await expect(durationCard).toBeVisible();
  });

  test('should navigate to folders page', async ({ page }) => {
    await page.click('a[href="/folders"]');
    await expect(page).toHaveURL('/folders');
    // Folders page doesn't have its own h1, just nav highlights
    await expect(page.locator('a[href="/folders"]')).toHaveClass(/bg-primary-100/);
  });

  test('should navigate to work status page', async ({ page }) => {
    await page.click('a[href="/work-status"]');
    await expect(page).toHaveURL('/work-status');
    // Work Status page has its own h1
    await expect(page.getByRole('heading', { name: 'Work Status' })).toBeVisible();
  });

  test('should have working scan button', async ({ page }) => {
    // Find scan button by text "Scan Now"
    const scanButton = page.getByRole('button', { name: /Scan Now|Scanning/i });
    await expect(scanButton).toBeVisible();

    // Only click if not already scanning
    const buttonText = await scanButton.textContent();
    if (buttonText?.includes('Scan Now')) {
      await scanButton.click();
      // Should show scanning state or progress
      await expect(
        page.getByRole('button', { name: /Scanning/i })
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test('should display navigation menu', async ({ page }) => {
    // Check all nav items are present
    const navItems = ['Dashboard', 'Folders', 'Work Status', 'Statistics', 'History'];
    for (const item of navItems) {
      await expect(page.getByRole('link', { name: item })).toBeVisible();
    }
  });

  test('should show NAS connection status', async ({ page }) => {
    // Footer shows "NAS Connected" status
    await expect(page.locator('text=NAS Connected')).toBeVisible();
  });
});
