const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // 페이지 로드
  await page.goto('http://localhost:8082');
  await page.waitForTimeout(3000);
  
  // WSOP 폴더 클릭 (확장)
  const wsopFolder = await page.locator('text=WSOP').first();
  if (wsopFolder) {
    await wsopFolder.click();
    await page.waitForTimeout(1000);
  }
  
  // WSOP Bracelet Event 클릭
  const braceletFolder = await page.locator('text=WSOP Bracelet Event').first();
  if (braceletFolder) {
    await braceletFolder.click();
    await page.waitForTimeout(1000);
  }
  
  // WSOP-EUROPE 클릭
  const europeFolder = await page.locator('text=WSOP-EUROPE').first();
  if (europeFolder) {
    await europeFolder.click();
    await page.waitForTimeout(1000);
  }
  
  // 스크린샷
  await page.screenshot({ path: 'screenshot_wsop_expanded.png', fullPage: true });
  
  console.log('Screenshot saved!');
  await browser.close();
})();
