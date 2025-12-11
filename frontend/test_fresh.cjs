const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  // 새로운 컨텍스트로 캐시 없이 시작
  const context = await browser.newContext({
    bypassCSP: true,
    ignoreHTTPSErrors: true
  });
  const page = await context.newPage();
  await page.setViewportSize({ width: 1400, height: 900 });
  
  // 캐시 비활성화
  await page.route('**/*', route => {
    route.continue({ headers: { ...route.request().headers(), 'Cache-Control': 'no-cache' } });
  });
  
  // 페이지 로드
  await page.goto('http://localhost:8082', { waitUntil: 'networkidle' });
  await page.waitForTimeout(5000);
  
  // WSOP 클릭
  await page.click('text=WSOP');
  await page.waitForTimeout(2000);
  
  // WSOP Bracelet Event 클릭
  try {
    await page.click('text=WSOP Bracelet Event', { timeout: 5000 });
    await page.waitForTimeout(2000);
  } catch(e) {}
  
  // 스크린샷
  await page.screenshot({ path: 'screenshot_fresh_cache.png' });
  console.log('Fresh screenshot captured!');
  
  await browser.close();
})();
