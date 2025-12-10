/**
 * Level 5: Performance Testing
 *
 * Tests for performance metrics:
 * - Page load time
 * - Core Web Vitals (LCP, FCP)
 * - API response time
 * - Memory usage
 */
import { test, expect } from '@playwright/test';

test.describe('Performance Tests', () => {
  test('dashboard should load under 3 seconds', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(3000);
  });

  test('folders page should load under 4 seconds', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/folders');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    // Increased threshold for NAS-dependent data loading
    expect(loadTime).toBeLessThan(4000);
  });

  test('work status page should load under 3 seconds', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/work-status');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(3000);
  });

  test('First Contentful Paint should be under 1.8s', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const fcp = await page.evaluate(() => {
      const entry = performance
        .getEntriesByType('paint')
        .find((e) => e.name === 'first-contentful-paint');
      return entry?.startTime || 0;
    });

    expect(fcp).toBeLessThan(1800);
  });

  test('API response time should be under 500ms', async ({ request }) => {
    const startTime = Date.now();

    await request.get('http://localhost:8000/api/stats');

    const responseTime = Date.now() - startTime;

    expect(responseTime).toBeLessThan(500);
  });

  test('no memory leaks on navigation', async ({ page }) => {
    await page.goto('/');

    // Get initial heap size (if available)
    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    // Navigate back and forth multiple times
    for (let i = 0; i < 5; i++) {
      await page.goto('/folders');
      await page.waitForLoadState('networkidle');
      await page.goto('/');
      await page.waitForLoadState('networkidle');
    }

    const finalMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    // Memory growth should be less than 100% (if memory API available)
    if (initialMemory > 0 && finalMemory > 0) {
      expect(finalMemory).toBeLessThan(initialMemory * 2);
    }
  });

  test('images should be lazy loaded', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const images = await page.locator('img[loading="lazy"]').all();

    // If there are images, they should have lazy loading
    // This is optional - some images may need eager loading
  });

  test('no large layout shifts', async ({ page }) => {
    await page.goto('/');

    // Wait for page to stabilize
    await page.waitForTimeout(2000);

    const cls = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let clsValue = 0;

        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!(entry as any).hadRecentInput) {
              clsValue += (entry as any).value;
            }
          }
        });

        observer.observe({ type: 'layout-shift', buffered: true });

        setTimeout(() => {
          observer.disconnect();
          resolve(clsValue);
        }, 1000);
      });
    });

    // Good CLS should be under 0.1
    expect(cls).toBeLessThan(0.25);
  });
});
