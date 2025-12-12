import { test, expect } from '@playwright/test';

/**
 * E2E Test: 숨긴 항목 필터 기능 검증
 *
 * 테스트 항목:
 * 1. Extension Filter에서 숨김 파일 토글 확인
 * 2. 토글 클릭 시 상태 변경 확인
 * 3. API 호출 시 include_hidden 파라미터 전달 확인
 * 4. Progress Overview 폴더 트리 로드 확인
 */

// Docker 환경에서는 8082 포트 사용
const BASE_URL = process.env.BASE_URL || 'http://localhost:8082';

test.describe('숨긴 항목 필터 기능', () => {
  test.beforeEach(async ({ page }) => {
    // 대시보드로 이동
    await page.goto(BASE_URL);
    // 페이지 로드 대기
    await page.waitForLoadState('networkidle');
  });

  test('Extension Filter에 숨김 파일 토글이 표시됨', async ({ page }) => {
    // Extension Filter 헤더 확인
    const filterHeader = page.locator('text=Extension Filter');
    await expect(filterHeader).toBeVisible({ timeout: 10000 });

    // 숨김 파일 토글 버튼 확인
    const toggleButton = page.locator('button:has-text("숨김 파일")');
    await expect(toggleButton).toBeVisible();
  });

  test('숨김 파일 토글 클릭 시 상태 변경', async ({ page }) => {
    // 토글 버튼 찾기
    const toggleButton = page.locator('button:has-text("숨김 파일")');

    // 초기 상태: 비활성화 (회색 배경)
    await expect(toggleButton).toHaveClass(/bg-gray-100/);

    // 토글 클릭
    await toggleButton.click();

    // 클릭 후: 활성화 (파란색 배경)
    await expect(toggleButton).toHaveClass(/bg-blue-100/);

    // 다시 클릭하면 원래 상태로
    await toggleButton.click();
    await expect(toggleButton).toHaveClass(/bg-gray-100/);
  });

  test('숨김 파일 토글 시 API 호출 파라미터 확인', async ({ page }) => {
    // API 요청 가로채기
    const apiCalls: string[] = [];

    page.on('request', request => {
      if (request.url().includes('/api/progress/tree')) {
        apiCalls.push(request.url());
      }
    });

    // 페이지 새로고침하여 초기 API 호출 캡처
    await page.reload();
    await page.waitForLoadState('networkidle');

    // 초기 API 호출 확인 (include_hidden=false)
    expect(apiCalls.some(url => url.includes('include_hidden=false'))).toBeTruthy();

    // 토글 클릭
    const toggleButton = page.locator('button:has-text("숨김 파일")');
    await toggleButton.click();

    // API 재호출 대기
    await page.waitForResponse(response =>
      response.url().includes('/api/progress/tree') && response.status() === 200
    );

    // include_hidden=true 파라미터 확인
    expect(apiCalls.some(url => url.includes('include_hidden=true'))).toBeTruthy();
  });

  test('폴더 트리가 정상 로드됨', async ({ page }) => {
    // Progress Overview 헤더 확인
    const header = page.locator('h3:has-text("Progress Overview")');
    await expect(header).toBeVisible({ timeout: 10000 });

    // 폴더 노드가 표시되는지 확인
    const folderNodes = page.locator('[class*="cursor-pointer"]').filter({
      has: page.locator('svg') // 폴더 아이콘이 있는 요소
    });

    // 최소 1개 이상의 폴더가 표시되어야 함
    await expect(folderNodes.first()).toBeVisible({ timeout: 15000 });
  });
});
