/**
 * Level 4: API Testing
 *
 * Tests for REST API endpoints:
 * - Response validation
 * - Schema validation
 * - Error handling
 */
import { test, expect } from '@playwright/test';

const API_BASE = 'http://localhost:8000';

test.describe('API Endpoint Tests', () => {
  test.describe('Health Check', () => {
    test('GET /health should return healthy status', async ({ request }) => {
      const response = await request.get(`${API_BASE}/health`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data.status).toBe('healthy');
    });
  });

  test.describe('Statistics API', () => {
    test('GET /api/stats/summary should return valid statistics', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/stats/summary`);

      expect(response.status()).toBe(200);
      expect(response.headers()['content-type']).toContain('application/json');

      const data = await response.json();

      // Validate schema - actual fields from API
      expect(data).toHaveProperty('total_files');
      expect(data).toHaveProperty('total_size');
      expect(data).toHaveProperty('total_duration');
      expect(data).toHaveProperty('total_size_formatted');
      expect(data).toHaveProperty('total_duration_formatted');

      // Validate types
      expect(typeof data.total_files).toBe('number');
      expect(typeof data.total_size).toBe('number');
      expect(typeof data.total_duration).toBe('number');

      // Values should be non-negative
      expect(data.total_files).toBeGreaterThanOrEqual(0);
      expect(data.total_size).toBeGreaterThanOrEqual(0);
      expect(data.total_duration).toBeGreaterThanOrEqual(0);
    });

    test('GET /api/stats/file-types should return file type distribution', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/stats/file-types`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(Array.isArray(data)).toBe(true);
    });
  });

  test.describe('Folders API', () => {
    test('GET /api/folders/tree should return folder tree', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/folders/tree`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(Array.isArray(data)).toBe(true);
    });

    test('GET /api/folders/tree with depth parameter', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/folders/tree?depth=1`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(Array.isArray(data)).toBe(true);
    });
  });

  test.describe('Scan API', () => {
    test('POST /api/scan/start should start or report status', async ({ request }) => {
      const response = await request.post(`${API_BASE}/api/scan/start`, {
        data: { scan_type: 'full' },
      });

      // May return 200 (started/already running), 422 (validation), or other status
      expect([200, 400, 409, 422]).toContain(response.status());

      const data = await response.json();
      // Response structure may vary based on status
      expect(data).toBeDefined();
    });

    test('GET /api/scan/status should return scan status', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/scan/status`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data).toHaveProperty('is_scanning');
    });
  });

  test.describe('Work Status API', () => {
    test('GET /api/work-status should return progress data', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/work-status`);

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data).toBeDefined();
    });
  });

  test.describe('Error Handling', () => {
    test('GET /api/nonexistent should return 404', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/nonexistent`);

      expect(response.status()).toBe(404);
    });

    test('POST to read-only endpoint should handle gracefully', async ({ request }) => {
      const response = await request.post(`${API_BASE}/api/stats/summary`, {
        data: { invalid: 'data' },
      });

      // Should return method not allowed or similar
      expect([200, 405, 404, 422]).toContain(response.status());
    });
  });
});
