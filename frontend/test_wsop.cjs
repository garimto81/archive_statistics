const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1400, height: 900 });
  
  // 페이지 로드
  await page.goto('http://localhost:8082');
  await page.waitForTimeout(4000);
  
  // 스크린샷 1: 초기 상태
  await page.screenshot({ path: 'screenshot_step0_initial.png' });
  console.log('Step 0: Initial state');
  
  // WSOP 행 클릭 (폴더 확장)
  await page.click('text=WSOP');
  await page.waitForTimeout(2000);
  
  // 스크린샷 2: WSOP 클릭 후
  await page.screenshot({ path: 'screenshot_step1_wsop_click.png' });
  console.log('Step 1: After WSOP click');
  
  // 페이지 스크롤 다운
  await page.evaluate(() => {
    const progressSection = document.querySelector('[class*="Progress"]') || document.body;
    progressSection.scrollTop = 200;
  });
  await page.waitForTimeout(1000);
  
  // WSOP Bracelet Event 클릭 시도
  try {
    await page.click('text=WSOP Bracelet Event', { timeout: 5000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'screenshot_step2_bracelet.png' });
    console.log('Step 2: After Bracelet click');
  } catch (e) {
    console.log('Bracelet not found or not clickable');
  }
  
  // WSOP-EUROPE 클릭 시도
  try {
    await page.click('text=WSOP-EUROPE', { timeout: 5000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'screenshot_step3_europe.png' });
    console.log('Step 3: After Europe click');
  } catch (e) {
    console.log('Europe not found or not clickable');
  }
  
  // 2024 WSOP-Europe 클릭 시도
  try {
    await page.click('text=2024 WSOP-Europe', { timeout: 5000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'screenshot_step4_2024.png' });
    console.log('Step 4: After 2024 click');
  } catch (e) {
    console.log('2024 Europe not found');
  }
  
  // 최종 전체 페이지 스크린샷
  await page.screenshot({ path: 'screenshot_final.png', fullPage: true });
  console.log('Final screenshot captured');
  
  await browser.close();
  console.log('Done!');
})();
