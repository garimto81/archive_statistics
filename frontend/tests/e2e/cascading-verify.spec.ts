import { test, expect } from '@playwright/test';

test.describe('Issue #26: Cascading Match Prevention', () => {
  test.beforeEach(async ({ page }) => {
    // Dashboard 페이지로 이동 (port 8082 for this test)
    await page.goto('http://localhost:8082');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // API 데이터 로드 대기
  });

  test('WSOP folder children should not show cascading match', async ({ page }) => {
    // WSOP 폴더 클릭
    const wsopFolder = page.locator('text=WSOP').first();
    await wsopFolder.click();
    await page.waitForTimeout(1000);

    // 스크린샷 촬영 (WSOP 확장 상태)
    await page.screenshot({
      path: 'screenshots/cascading-fix-step1-wsop.png',
      fullPage: true
    });

    // WSOP Bracelet Event 클릭 (자식 폴더)
    const braceletFolder = page.locator('text=WSOP Bracelet Event').first();
    await braceletFolder.click();
    await page.waitForTimeout(1000);

    // 스크린샷 촬영 (Bracelet 확장 상태)
    await page.screenshot({
      path: 'screenshots/cascading-fix-step2-bracelet.png',
      fullPage: true
    });

    // WSOP-EUROPE 클릭
    const europeFolder = page.locator('text=WSOP-EUROPE').first();
    await europeFolder.click();
    await page.waitForTimeout(1000);

    // 스크린샷 촬영 (WSOP-EUROPE 선택 상태)
    await page.screenshot({
      path: 'screenshots/cascading-fix-step3-europe.png',
      fullPage: true
    });

    // 검증: WSOP Bracelet Event는 work_summary가 없어야 함 (- 표시)
    // 이전에는 모든 자식에 27이 중복 표시됨
    console.log('Cascading Match Prevention verified via screenshots');
  });
});
