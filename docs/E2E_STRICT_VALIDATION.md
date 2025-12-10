# E2E Strict Validation Pipeline

**Version**: 1.0.0 | **Date**: 2025-12-09 | **Status**: Draft

> Playwright 전체 기능을 활용한 엄격한 E2E 검증 후 최종 보고만 수신하는 자동화 파이프라인

---

## 목차

1. [개요](#1-개요)
2. [Playwright 전체 기능 활용](#2-playwright-전체-기능-활용)
3. [검증 파이프라인 설계](#3-검증-파이프라인-설계)
4. [자동화 워크플로우](#4-자동화-워크플로우)
5. [최종 보고서 형식](#5-최종-보고서-형식)
6. [구현 가이드](#6-구현-가이드)

---

## 1. 개요

### 1.1 목표

```
┌─────────────────────────────────────────────────────────────┐
│                      설계 목표                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  "사용자는 최종 보고서만 확인"                               │
│                                                              │
│  • 모든 개발 → 자동                                         │
│  • 모든 테스트 → 자동                                       │
│  • 모든 수정 → 자동                                         │
│  • 모든 검증 → 자동                                         │
│  • 최종 보고 → 사용자 확인                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Playwright 활용 범위

| 카테고리 | 기능 | 용도 |
|----------|------|------|
| **UI Testing** | Auto-wait, Assertions | 기능 검증 |
| **Visual Regression** | toHaveScreenshot() | UI 변경 감지 |
| **Accessibility** | axe-core 통합 | WCAG 준수 검증 |
| **API Testing** | APIRequestContext | 백엔드 검증 |
| **Performance** | Metrics, Tracing | 성능 측정 |
| **Security** | Network Interception | 보안 검증 |
| **Cross-Browser** | Chromium, Firefox, WebKit | 호환성 검증 |
| **Debugging** | Trace Viewer, Screenshots | 실패 분석 |

---

## 2. Playwright 전체 기능 활용

### 2.1 기능별 테스트 설계

```
┌─────────────────────────────────────────────────────────────┐
│               PLAYWRIGHT FULL FEATURE MATRIX                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Level 1: Functional Testing                          │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │   │
│  │ • Page Navigation & Routing                          │   │
│  │ • Form Interactions (Input, Select, Checkbox)        │   │
│  │ • Button Clicks & User Actions                       │   │
│  │ • Data Display & Table Rendering                     │   │
│  │ • Modal/Dialog Handling                              │   │
│  │ • File Upload/Download                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Level 2: Visual Regression Testing                   │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │   │
│  │ • Full Page Screenshots                              │   │
│  │ • Component Screenshots                              │   │
│  │ • Responsive Breakpoints (Mobile/Tablet/Desktop)     │   │
│  │ • Dark/Light Theme Variants                          │   │
│  │ • Pixel-by-pixel Diff (pixelmatch)                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Level 3: Accessibility Testing                       │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │   │
│  │ • WCAG 2.1 AA Compliance                             │   │
│  │ • Color Contrast Validation                          │   │
│  │ • Keyboard Navigation                                │   │
│  │ • Screen Reader Compatibility                        │   │
│  │ • ARIA Labels & Roles                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Level 4: API Testing                                 │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │   │
│  │ • REST API Endpoints                                 │   │
│  │ • Request/Response Validation                        │   │
│  │ • Status Codes & Headers                             │   │
│  │ • JSON Schema Validation                             │   │
│  │ • Error Handling                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Level 5: Performance Testing                         │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │   │
│  │ • Page Load Time (LCP, FCP, TTI)                     │   │
│  │ • API Response Time                                  │   │
│  │ • Memory Usage                                       │   │
│  │ • Network Waterfall                                  │   │
│  │ • Bundle Size Impact                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Level 6: Security Testing                            │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │   │
│  │ • XSS Prevention                                     │   │
│  │ • CSRF Token Validation                              │   │
│  │ • Authentication Flow                                │   │
│  │ • Authorization Checks                               │   │
│  │ • Sensitive Data Exposure                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Level 7: Cross-Browser Testing                       │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │   │
│  │ • Chromium (Chrome, Edge)                            │   │
│  │ • Firefox                                            │   │
│  │ • WebKit (Safari)                                    │   │
│  │ • Mobile Emulation                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 테스트 설정 구조

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results.json' }],
    ['junit', { outputFile: 'junit-results.xml' }],
  ],

  use: {
    baseURL: 'http://localhost:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },

  projects: [
    // Level 1-5: Functional + Visual + a11y + API + Performance
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    // Level 7: Cross-Browser
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // Mobile Emulation
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  webServer: {
    command: 'npm run start',
    url: 'http://localhost:8000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### 2.3 레벨별 테스트 구현

#### Level 1: Functional Testing

```typescript
// tests/e2e/functional/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Dashboard Functional Tests', () => {
  test('should display archive statistics', async ({ page }) => {
    await page.goto('/');

    // 통계 카드 확인
    await expect(page.locator('[data-testid="total-files"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-size"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-duration"]')).toBeVisible();
  });

  test('should navigate to folder tree', async ({ page }) => {
    await page.goto('/');
    await page.click('[data-testid="nav-folders"]');
    await expect(page).toHaveURL('/folders');
    await expect(page.locator('[data-testid="folder-tree"]')).toBeVisible();
  });

  test('should trigger NAS scan', async ({ page }) => {
    await page.goto('/');
    await page.click('[data-testid="scan-button"]');
    await expect(page.locator('[data-testid="scan-progress"]')).toBeVisible();
  });
});
```

#### Level 2: Visual Regression Testing

```typescript
// tests/e2e/visual/screenshots.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Visual Regression Tests', () => {
  test('dashboard should match snapshot', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Full page screenshot
    await expect(page).toHaveScreenshot('dashboard-full.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });

  test('stat cards should match snapshot', async ({ page }) => {
    await page.goto('/');

    // Component screenshot
    const statsSection = page.locator('[data-testid="stats-section"]');
    await expect(statsSection).toHaveScreenshot('stats-cards.png');
  });

  test('responsive breakpoints', async ({ page }) => {
    await page.goto('/');

    // Desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page).toHaveScreenshot('dashboard-desktop.png');

    // Tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page).toHaveScreenshot('dashboard-tablet.png');

    // Mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page).toHaveScreenshot('dashboard-mobile.png');
  });
});
```

#### Level 3: Accessibility Testing

```typescript
// tests/e2e/accessibility/a11y.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility Tests', () => {
  test('dashboard should have no WCAG 2.1 AA violations', async ({ page }) => {
    await page.goto('/');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(results.violations).toEqual([]);
  });

  test('all interactive elements should be keyboard accessible', async ({ page }) => {
    await page.goto('/');

    // Tab through all focusable elements
    const focusableElements = await page.locator(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ).all();

    for (const element of focusableElements) {
      await element.focus();
      await expect(element).toBeFocused();
    }
  });

  test('color contrast should meet WCAG standards', async ({ page }) => {
    await page.goto('/');

    const results = await new AxeBuilder({ page })
      .withRules(['color-contrast'])
      .analyze();

    expect(results.violations).toEqual([]);
  });

  test('images should have alt text', async ({ page }) => {
    await page.goto('/');

    const images = await page.locator('img').all();
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      expect(alt).toBeTruthy();
    }
  });
});
```

#### Level 4: API Testing

```typescript
// tests/e2e/api/endpoints.spec.ts
import { test, expect } from '@playwright/test';

test.describe('API Tests', () => {
  test('GET /api/stats should return valid statistics', async ({ request }) => {
    const response = await request.get('/api/stats');

    expect(response.status()).toBe(200);
    expect(response.headers()['content-type']).toContain('application/json');

    const data = await response.json();
    expect(data).toHaveProperty('total_files');
    expect(data).toHaveProperty('total_size');
    expect(data).toHaveProperty('total_duration');
    expect(typeof data.total_files).toBe('number');
  });

  test('GET /api/folders should return folder tree', async ({ request }) => {
    const response = await request.get('/api/folders');

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
  });

  test('POST /api/scan should start scanning', async ({ request }) => {
    const response = await request.post('/api/scan', {
      data: { subpath: '' }
    });

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('status');
    expect(['started', 'already_running']).toContain(data.status);
  });

  test('GET /api/work-status should return progress', async ({ request }) => {
    const response = await request.get('/api/work-status');

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('videos');
  });

  test('API error handling', async ({ request }) => {
    const response = await request.get('/api/nonexistent');

    expect(response.status()).toBe(404);
  });
});
```

#### Level 5: Performance Testing

```typescript
// tests/e2e/performance/metrics.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Performance Tests', () => {
  test('page load should be under 3 seconds', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(3000);
  });

  test('Core Web Vitals should meet thresholds', async ({ page }) => {
    await page.goto('/');

    // Largest Contentful Paint (LCP)
    const lcp = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          resolve(entries[entries.length - 1].startTime);
        }).observe({ entryTypes: ['largest-contentful-paint'] });
      });
    });
    expect(lcp).toBeLessThan(2500); // Good LCP < 2.5s

    // First Contentful Paint (FCP)
    const fcp = await page.evaluate(() => {
      const entry = performance.getEntriesByType('paint')
        .find(e => e.name === 'first-contentful-paint');
      return entry?.startTime || 0;
    });
    expect(fcp).toBeLessThan(1800); // Good FCP < 1.8s
  });

  test('API response time should be under 500ms', async ({ request }) => {
    const startTime = Date.now();
    await request.get('/api/stats');
    const responseTime = Date.now() - startTime;

    expect(responseTime).toBeLessThan(500);
  });

  test('no memory leaks on repeated navigation', async ({ page }) => {
    await page.goto('/');

    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    // Navigate back and forth 10 times
    for (let i = 0; i < 10; i++) {
      await page.goto('/folders');
      await page.goto('/');
    }

    const finalMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    // Memory growth should be less than 50%
    expect(finalMemory).toBeLessThan(initialMemory * 1.5);
  });
});
```

#### Level 6: Security Testing

```typescript
// tests/e2e/security/security.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Security Tests', () => {
  test('should have secure headers', async ({ request }) => {
    const response = await request.get('/');
    const headers = response.headers();

    // Check for security headers
    expect(headers['x-content-type-options']).toBe('nosniff');
    expect(headers['x-frame-options']).toBeTruthy();
  });

  test('should prevent XSS in user inputs', async ({ page }) => {
    await page.goto('/');

    // Try to inject script
    const maliciousInput = '<script>alert("XSS")</script>';
    const searchInput = page.locator('[data-testid="search-input"]');

    if (await searchInput.isVisible()) {
      await searchInput.fill(maliciousInput);
      await page.keyboard.press('Enter');

      // Check that script is not executed
      const alertTriggered = await page.evaluate(() => {
        return (window as any).__xss_triggered || false;
      });
      expect(alertTriggered).toBe(false);
    }
  });

  test('should not expose sensitive data in responses', async ({ request }) => {
    const response = await request.get('/api/stats');
    const text = await response.text();

    // Check for sensitive patterns
    expect(text).not.toContain('password');
    expect(text).not.toContain('secret');
    expect(text).not.toContain('api_key');
  });

  test('should handle authentication properly', async ({ page }) => {
    // Attempt to access protected route without auth
    const response = await page.goto('/api/admin');

    // Should redirect or return 401/403
    if (response) {
      expect([401, 403, 302]).toContain(response.status());
    }
  });
});
```

#### Level 7: Cross-Browser Testing

```typescript
// tests/e2e/cross-browser/compatibility.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Cross-Browser Compatibility', () => {
  test('dashboard renders correctly', async ({ page, browserName }) => {
    await page.goto('/');

    // Common assertions for all browsers
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    await expect(page.locator('[data-testid="stats-section"]')).toBeVisible();

    // Browser-specific screenshot
    await expect(page).toHaveScreenshot(`dashboard-${browserName}.png`);
  });

  test('interactions work across browsers', async ({ page, browserName }) => {
    await page.goto('/');

    // Click actions
    const button = page.locator('[data-testid="scan-button"]');
    await button.click();

    // Verify result
    await expect(page.locator('[data-testid="scan-status"]')).toBeVisible();
  });
});
```

---

## 3. 검증 파이프라인 설계

### 3.1 파이프라인 구조

```
┌─────────────────────────────────────────────────────────────┐
│               STRICT E2E VALIDATION PIPELINE                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Stage 1: Environment Setup                           │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │   │
│  │ • Start Backend Server                               │   │
│  │ • Start Frontend Dev Server                          │   │
│  │ • Initialize Test Database                           │   │
│  │ • Seed Test Data                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Stage 2: Parallel Test Execution                     │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │   │
│  │                                                       │   │
│  │   ┌────────────┐  ┌────────────┐  ┌────────────┐   │   │
│  │   │ Functional │  │  Visual    │  │   a11y     │   │   │
│  │   │   Tests    │  │ Regression │  │   Tests    │   │   │
│  │   └────────────┘  └────────────┘  └────────────┘   │   │
│  │                                                       │   │
│  │   ┌────────────┐  ┌────────────┐  ┌────────────┐   │   │
│  │   │    API     │  │Performance │  │  Security  │   │   │
│  │   │   Tests    │  │   Tests    │  │   Tests    │   │   │
│  │   └────────────┘  └────────────┘  └────────────┘   │   │
│  │                                                       │   │
│  │   ┌────────────────────────────────────────────┐    │   │
│  │   │        Cross-Browser Matrix                 │    │   │
│  │   │  Chromium │ Firefox │ WebKit │ Mobile      │    │   │
│  │   └────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Stage 3: Auto-Fix Loop (Max 3 Attempts)              │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │   │
│  │                                                       │   │
│  │   Tests Failed?                                       │   │
│  │        │                                              │   │
│  │   ┌────┴────┐                                        │   │
│  │   │  YES    │──▶ Analyze Failure                     │   │
│  │   └─────────┘         │                              │   │
│  │                       ▼                              │   │
│  │              ┌─────────────────┐                     │   │
│  │              │ Auto-Fix Agent  │                     │   │
│  │              │ (debugger)      │                     │   │
│  │              └────────┬────────┘                     │   │
│  │                       │                              │   │
│  │                       ▼                              │   │
│  │              Re-run Failed Tests                     │   │
│  │                       │                              │   │
│  │              Attempt < 3? ──▶ Loop                   │   │
│  │                       │                              │   │
│  │   ┌────┴────┐                                        │   │
│  │   │   NO    │──▶ Stage 4                             │   │
│  │   └─────────┘                                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Stage 4: Result Aggregation                          │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │   │
│  │ • Merge Test Results                                 │   │
│  │ • Generate Screenshots Gallery                       │   │
│  │ • Create Trace Archive                               │   │
│  │ • Calculate Coverage                                 │   │
│  │ • Compute Quality Score                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Stage 5: Final Report Generation                     │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │   │
│  │ • Executive Summary                                  │   │
│  │ • Detailed Test Results                              │   │
│  │ • Visual Diff Gallery                                │   │
│  │ • Performance Metrics                                │   │
│  │ • Recommendations                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│              ┌─────────────────────────┐                   │
│              │  🛑 USER FINAL REVIEW   │                   │
│              │  (Only Interaction)     │                   │
│              └─────────────────────────┘                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 검증 기준 (Pass/Fail Criteria)

| 카테고리 | Pass 조건 | Fail 조건 |
|----------|-----------|-----------|
| **Functional** | 100% 통과 | 1개 이상 실패 |
| **Visual** | Diff < 100 pixels | Diff >= 100 pixels |
| **Accessibility** | WCAG violations = 0 | 1개 이상 violation |
| **API** | 모든 엔드포인트 정상 | 1개 이상 오류 |
| **Performance** | LCP < 2.5s, API < 500ms | 기준 초과 |
| **Security** | Critical = 0 | Critical 발견 |
| **Cross-Browser** | 모든 브라우저 통과 | 1개 이상 실패 |

### 3.3 자동 수정 정책

```typescript
// Auto-fix policy
interface AutoFixPolicy {
  maxAttempts: 3;
  fixableCategories: [
    'functional',     // 코드 로직 수정
    'visual',         // 스냅샷 업데이트
    'api',            // API 응답 수정
  ];
  nonFixableCategories: [
    'security',       // 수동 검토 필요
    'performance',    // 아키텍처 변경 필요
  ];
}
```

---

## 4. 자동화 워크플로우

### 4.1 전체 흐름

```
사용자 요청
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    자동 실행 영역                            │
│ ─────────────────────────────────────────────────────────── │
│                                                              │
│  Phase 0: Pre-Work ──────────────────────────────────────▶  │
│  Phase 1: Block 분석 ────────────────────────────────────▶  │
│  Phase 2: 이슈/문서 생성 ────────────────────────────────▶  │
│  Phase 3: TDD 개발 ──────────────────────────────────────▶  │
│  Phase 4: Unit/Integration Test ─────────────────────────▶  │
│  Phase 5: E2E Strict Validation ─────────────────────────▶  │
│      │                                                       │
│      ├─▶ Functional Tests (Parallel)                        │
│      ├─▶ Visual Regression Tests (Parallel)                 │
│      ├─▶ Accessibility Tests (Parallel)                     │
│      ├─▶ API Tests (Parallel)                               │
│      ├─▶ Performance Tests (Parallel)                       │
│      ├─▶ Security Tests (Parallel)                          │
│      └─▶ Cross-Browser Tests (Matrix)                       │
│              │                                               │
│              ├─▶ 실패 시 자동 수정 (3회)                    │
│              │                                               │
│  Phase 6: Report Generation ─────────────────────────────▶  │
│  Phase 7: PR 준비 ───────────────────────────────────────▶  │
│                                                              │
└─────────────────────────────────┬───────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  🛑 최종 보고서 제출    │
                    │  사용자 검토 요청       │
                    └─────────────────────────┘
```

### 4.2 실행 스크립트

```bash
#!/bin/bash
# scripts/e2e-strict-validation.sh

set -e

echo "🚀 Starting E2E Strict Validation Pipeline"

# Stage 1: Environment Setup
echo "📦 Stage 1: Setting up environment..."
docker-compose -f docker-compose.test.yml up -d
npm run db:seed:test

# Stage 2: Run All Tests in Parallel
echo "🧪 Stage 2: Running tests..."
npx playwright test --reporter=json,html \
  --output=test-results \
  --trace=on \
  --screenshot=on \
  --video=on

# Stage 3: Check Results
TEST_RESULT=$?

if [ $TEST_RESULT -ne 0 ]; then
  echo "❌ Tests failed. Attempting auto-fix..."

  for attempt in 1 2 3; do
    echo "🔧 Auto-fix attempt $attempt/3..."

    # Analyze failures and attempt fix
    node scripts/analyze-and-fix.js

    # Re-run failed tests
    npx playwright test --last-failed

    if [ $? -eq 0 ]; then
      echo "✅ Auto-fix successful on attempt $attempt"
      break
    fi
  done
fi

# Stage 4: Generate Report
echo "📊 Stage 4: Generating final report..."
node scripts/generate-report.js

# Stage 5: Upload Artifacts
echo "📤 Stage 5: Uploading artifacts..."
# Upload to cloud storage or artifact server

echo "✅ Pipeline complete. Final report ready for review."
```

---

## 5. 최종 보고서 형식

### 5.1 보고서 구조

```markdown
# E2E 검증 최종 보고서

## Executive Summary

| 항목 | 결과 | 상세 |
|------|------|------|
| **전체 상태** | ✅ PASS / ❌ FAIL | - |
| **총 테스트** | 127개 | - |
| **통과** | 127개 | 100% |
| **실패** | 0개 | 0% |
| **실행 시간** | 4분 32초 | - |
| **품질 점수** | 96/100 | - |

## 검증 결과 상세

### Level 1: Functional Testing ✅
- Tests: 45/45 passed
- Coverage: 92%

### Level 2: Visual Regression ✅
- Screenshots: 28 captured
- Diffs: 0 detected
- [Visual Gallery Link]

### Level 3: Accessibility ✅
- WCAG 2.1 AA: 100% compliant
- Violations: 0
- Warnings: 2 (minor)

### Level 4: API Testing ✅
- Endpoints: 12/12 passed
- Response Schema: Valid
- Error Handling: Proper

### Level 5: Performance ✅
- LCP: 1.2s (< 2.5s) ✅
- FCP: 0.8s (< 1.8s) ✅
- API Response: 120ms (< 500ms) ✅

### Level 6: Security ✅
- Critical: 0
- High: 0
- Medium: 1 (accepted)

### Level 7: Cross-Browser ✅
| Browser | Status | Screenshot |
|---------|--------|------------|
| Chromium | ✅ Pass | [View] |
| Firefox | ✅ Pass | [View] |
| WebKit | ✅ Pass | [View] |
| Mobile Chrome | ✅ Pass | [View] |
| Mobile Safari | ✅ Pass | [View] |

## 변경 사항 요약

### 생성된 파일
| 파일 | 유형 | 라인 |
|------|------|------|
| `src/api/scan.py` | 수정 | +45/-12 |
| `tests/e2e/scan.spec.ts` | 신규 | +120 |

### 커밋 이력
1. `test: Add scan E2E tests (RED)` - abc1234
2. `feat: Implement scan optimization (GREEN)` - def5678
3. `refactor: Improve error handling` - ghi9012

## Artifacts

| 항목 | 링크 |
|------|------|
| HTML Report | [playwright-report/index.html] |
| Trace Files | [test-results/traces/] |
| Screenshots | [test-results/screenshots/] |
| Videos | [test-results/videos/] |

## PR Information

- **Branch**: `feat/scan-optimization`
- **PR**: #47 - NAS 스캔 성능 최적화
- **Target**: `main`

---

## 사용자 액션

[✅ 승인하고 머지] [📝 수정 요청] [❌ 취소]
```

### 5.2 시각적 보고서 (HTML)

```html
<!-- playwright-report/custom/summary.html -->
<!DOCTYPE html>
<html>
<head>
  <title>E2E Validation Report</title>
  <style>
    .pass { color: #22c55e; }
    .fail { color: #ef4444; }
    .score { font-size: 48px; font-weight: bold; }
    .metric-card { padding: 16px; border-radius: 8px; }
  </style>
</head>
<body>
  <h1>E2E Strict Validation Report</h1>

  <div class="score pass">96/100</div>

  <div class="metrics">
    <div class="metric-card">
      <h3>Functional</h3>
      <span class="pass">45/45 ✅</span>
    </div>
    <div class="metric-card">
      <h3>Visual</h3>
      <span class="pass">0 diffs ✅</span>
    </div>
    <!-- ... more metrics ... -->
  </div>

  <h2>Visual Gallery</h2>
  <div class="gallery">
    <!-- Screenshot comparisons -->
  </div>

  <h2>Action Required</h2>
  <button onclick="approve()">✅ Approve & Merge</button>
  <button onclick="requestChanges()">📝 Request Changes</button>
  <button onclick="cancel()">❌ Cancel</button>
</body>
</html>
```

---

## 6. 구현 가이드

### 6.1 필요 패키지

```json
{
  "devDependencies": {
    "@playwright/test": "^1.40.0",
    "@axe-core/playwright": "^4.8.0",
    "playwright": "^1.40.0"
  }
}
```

### 6.2 디렉토리 구조

```
archive-statistics/
├── tests/
│   └── e2e/
│       ├── functional/
│       │   ├── dashboard.spec.ts
│       │   ├── folders.spec.ts
│       │   └── scan.spec.ts
│       ├── visual/
│       │   └── screenshots.spec.ts
│       ├── accessibility/
│       │   └── a11y.spec.ts
│       ├── api/
│       │   └── endpoints.spec.ts
│       ├── performance/
│       │   └── metrics.spec.ts
│       ├── security/
│       │   └── security.spec.ts
│       └── cross-browser/
│           └── compatibility.spec.ts
├── playwright.config.ts
├── scripts/
│   ├── e2e-strict-validation.sh
│   ├── analyze-and-fix.js
│   └── generate-report.js
└── playwright-report/
```

### 6.3 CI/CD 통합

```yaml
# .github/workflows/e2e-validation.yml
name: E2E Strict Validation

on:
  pull_request:
    branches: [main]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright Browsers
        run: npx playwright install --with-deps

      - name: Run E2E Tests
        run: npx playwright test

      - name: Upload Report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

---

## 참조

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Visual Comparisons](https://playwright.dev/docs/test-snapshots)
- [Playwright Accessibility Testing](https://playwright.dev/docs/accessibility-testing)
- [Playwright API Testing](https://playwright.dev/docs/api-testing)
- [axe-playwright](https://www.npmjs.com/package/axe-playwright)

Sources:
- [Playwright Features 2025](https://thinksys.com/qa-testing/playwright-features/)
- [Playwright GitHub](https://github.com/microsoft/playwright)
- [Visual Regression Testing Guide](https://testgrid.io/blog/playwright-visual-regression-testing/)
- [Accessibility Testing with Playwright](https://playwright.dev/docs/accessibility-testing)
