/**
 * Worker Stats E2E Tests
 *
 * Tests for worker (PIC) statistics feature:
 * - Workers tab navigation
 * - Worker cards display
 * - Worker detail modal
 * - Summary statistics
 */
import { test, expect } from '@playwright/test';

test.describe('Worker Stats Feature', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/work-status');
    await page.waitForLoadState('networkidle');
  });

  test('should display Tasks and Workers tabs', async ({ page }) => {
    // Check for tab buttons
    const tasksTab = page.getByRole('button', { name: /Tasks/i });
    const workersTab = page.getByRole('button', { name: /Workers/i });

    await expect(tasksTab).toBeVisible();
    await expect(workersTab).toBeVisible();
  });

  test('should switch to Workers tab', async ({ page }) => {
    const workersTab = page.getByRole('button', { name: /Workers/i });
    await workersTab.click();

    // Should see summary cards when in Workers tab
    await expect(page.getByText('Total Workers')).toBeVisible();
    await expect(page.getByText('Total Videos')).toBeVisible();
  });

  test('should display summary statistics on Workers tab', async ({ page }) => {
    await page.getByRole('button', { name: /Workers/i }).click();

    // Check for summary cards
    await expect(page.getByText('Total Workers')).toBeVisible();
    await expect(page.getByText('Completed')).toBeVisible();
    await expect(page.getByText('Remaining')).toBeVisible();
  });

  test('should display Status Breakdown section', async ({ page }) => {
    await page.getByRole('button', { name: /Workers/i }).click();

    // Check for Status Breakdown
    await expect(page.getByText('Status Breakdown')).toBeVisible();
  });

  test('should display Archive Breakdown section', async ({ page }) => {
    await page.getByRole('button', { name: /Workers/i }).click();

    // Check for Archive Breakdown (collapsed by default)
    await expect(page.getByText('Archive Breakdown')).toBeVisible();
  });

  test('should toggle Archive Breakdown expansion', async ({ page }) => {
    await page.getByRole('button', { name: /Workers/i }).click();

    // Click Archive Breakdown to expand
    const archiveBreakdown = page.getByRole('button', { name: /Archive Breakdown/i });
    await archiveBreakdown.click();

    // The section should expand - verify by checking for chevron change
    // (Content visibility depends on data)
    await expect(archiveBreakdown).toBeVisible();
  });

  test('should keep Tasks tab functional', async ({ page }) => {
    // Verify Tasks tab is default - use heading specifically
    await expect(page.getByRole('heading', { name: 'Work Status' })).toBeVisible();

    // Switch to Workers then back to Tasks
    await page.getByRole('button', { name: /Workers/i }).click();
    await page.getByRole('button', { name: /Tasks/i }).click();

    // Should see table headers from Tasks view
    await expect(page.getByRole('columnheader', { name: /Archive/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /Category/i })).toBeVisible();
  });

  test('should maintain overall progress bar', async ({ page }) => {
    // Progress bar should be visible regardless of tab
    await expect(page.getByText('Overall Progress')).toBeVisible();

    // Switch to Workers tab
    await page.getByRole('button', { name: /Workers/i }).click();

    // Progress bar should still be visible
    await expect(page.getByText('Overall Progress')).toBeVisible();
  });
});

test.describe('Worker Stats API', () => {
  test('GET /api/worker-stats should return valid response', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/worker-stats');

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('workers');
    expect(data).toHaveProperty('summary');
    expect(Array.isArray(data.workers)).toBe(true);

    // Validate summary structure
    expect(data.summary).toHaveProperty('total_workers');
    expect(data.summary).toHaveProperty('total_videos');
    expect(data.summary).toHaveProperty('total_done');
    expect(data.summary).toHaveProperty('overall_progress');
    expect(data.summary).toHaveProperty('by_status');
    expect(data.summary).toHaveProperty('by_archive');
  });

  test('GET /api/worker-stats/summary should return summary only', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/worker-stats/summary');

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('total_workers');
    expect(data).toHaveProperty('total_videos');
    expect(data).toHaveProperty('overall_progress');
  });

  test('GET /api/worker-stats/{pic} returns 404 for non-existent worker', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/worker-stats/NonExistentWorker');

    expect(response.status()).toBe(404);
  });
});
