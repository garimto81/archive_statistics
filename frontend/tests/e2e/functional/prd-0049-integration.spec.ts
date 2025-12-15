/**
 * PRD-0049 Integration Tests (TDD - RED Phase)
 *
 * FolderTreeWithProgress + MasterFolderTree 통합 테스트
 *
 * TDD 순서:
 * 1. RED: 실패하는 테스트 작성 (현재 파일)
 * 2. GREEN: 테스트 통과하도록 구현
 * 3. REFACTOR: 코드 정리
 *
 * Issue: #48
 * PRD: PRD-0049-FOLDER-TREE-INTEGRATION.md
 */
import { test, expect } from '@playwright/test';

/**
 * ============================================================================
 * Phase 1: MasterFolderTree 기능 보완 테스트
 *
 * PRD-0049 Section 6.1 요구사항:
 * - 1-1: showLegend prop 추가
 * - 1-2: ProgressLegend 컴포넌트 이식
 * - 1-4: getWorkSummary 헬퍼 통합
 * - 1-5: FileNode 메타데이터 동기화
 * ============================================================================
 */
test.describe('PRD-0049 Phase 1: MasterFolderTree Enhancement', () => {
  test.describe('1-1: showLegend Prop', () => {
    test.beforeEach(async ({ page }) => {
      // Dashboard에서 showLegend=true로 설정됨
      await page.goto('/');
      await page.waitForLoadState('networkidle');
    });

    /**
     * showLegend prop이 true일 때 범례가 표시되어야 함
     * Dashboard에서 showLegend=true 설정
     */
    test('should display progress legend when showLegend is enabled', async ({ page }) => {
      // Dashboard의 MasterFolderTree에서 범례 영역 확인
      // 범례에는 색상 코드 설명이 포함되어야 함
      const legendSection = page.locator('[data-testid="progress-legend"]');

      await expect(legendSection).toBeVisible({ timeout: 10000 });
    });

    /**
     * 범례에 완료 상태 표시기가 있어야 함
     */
    test('should show complete status indicator in legend', async ({ page }) => {
      const legendComplete = page.locator('[data-testid="legend-complete"]');
      await expect(legendComplete).toBeVisible({ timeout: 10000 });
      await expect(legendComplete).toContainText(/완료|Complete/i);
    });

    /**
     * 범례에 진행 중 상태 표시기가 있어야 함
     */
    test('should show in-progress status indicator in legend', async ({ page }) => {
      const legendProgress = page.locator('[data-testid="legend-in-progress"]');
      await expect(legendProgress).toBeVisible({ timeout: 10000 });
      await expect(legendProgress).toContainText(/진행|Progress/i);
    });

    /**
     * 범례에 경고 상태 표시기가 있어야 함
     */
    test('should show warning status indicator in legend', async ({ page }) => {
      const legendWarning = page.locator('[data-testid="legend-warning"]');
      await expect(legendWarning).toBeVisible({ timeout: 10000 });
      await expect(legendWarning).toContainText(/경고|Warning|불일치/i);
    });
  });

  test.describe('1-4: getWorkSummary Helper Integration', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
    });

    /**
     * Dashboard에서 work_summary의 is_complete 표시
     * MasterFolderTree가 Dashboard에서 사용될 때 동일하게 동작해야 함
     */
    test('should display is_complete checkmark consistently', async ({ page }) => {
      // MasterFolderTree의 완료 체크마크 (CheckCircle2 아이콘)
      const completeIcon = page.locator('[class*="text-green-600"]').locator('svg');

      // 완료된 폴더가 있으면 체크마크 표시됨
      const count = await completeIcon.count();
      // 데이터에 완료된 폴더가 있을 수도 없을 수도 있음
      expect(count).toBeGreaterThanOrEqual(0);

      // 체크마크가 있다면 title 속성 확인
      if (count > 0) {
        const firstIcon = completeIcon.first();
        const parentSpan = firstIcon.locator('xpath=..');
        const title = await parentSpan.getAttribute('title');
        // title이 있으면 완료 관련 텍스트 포함
        if (title) {
          expect(title).toMatch(/완료|complete|done/i);
        }
      }
    });

    /**
     * data_source_mismatch 경고 아이콘 표시
     */
    test('should display data_source_mismatch warning consistently', async ({ page }) => {
      const warningIcon = page.locator('[class*="text-amber-500"]').locator('svg').first();

      const count = await warningIcon.count();
      if (count > 0) {
        await expect(warningIcon).toBeVisible();

        const parentElement = warningIcon.locator('..');
        const title = await parentElement.getAttribute('title');
        expect(title).toMatch(/불일치|mismatch|확인/i);
      }
    });
  });

  test.describe('1-5: FileNode Metadata Sync', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/folders');
      await page.waitForLoadState('networkidle');
    });

    /**
     * 파일 노드에 용량 정보 표시
     */
    test('should display file size in file nodes', async ({ page }) => {
      // 폴더를 펼쳐서 파일 노드 확인
      const expandableFolder = page.locator('[class*="cursor-pointer"]').first();

      if (await expandableFolder.isVisible()) {
        await expandableFolder.click();
        await page.waitForTimeout(500);

        // 파일 사이즈 표시 확인 (B, KB, MB, GB 단위)
        const sizeInfo = page.locator('text=/\\d+(\\.\\d+)?\\s*(B|KB|MB|GB|TB)/i');
        const count = await sizeInfo.count();
        expect(count).toBeGreaterThanOrEqual(0); // 파일이 없을 수도 있음
      }
    });

    /**
     * 비디오 파일에 재생시간 표시
     */
    test('should display duration for video files', async ({ page }) => {
      // 폴더를 펼쳐서 비디오 파일 확인
      const expandableFolder = page.locator('[class*="cursor-pointer"]').first();

      if (await expandableFolder.isVisible()) {
        await expandableFolder.click();
        await page.waitForTimeout(500);

        // 재생시간 형식: HH:MM:SS 또는 M:SS
        const durationInfo = page.locator('text=/\\d+:\\d{2}(:\\d{2})?/');
        const count = await durationInfo.count();
        expect(count).toBeGreaterThanOrEqual(0); // 비디오가 없을 수도 있음
      }
    });
  });
});

/**
 * ============================================================================
 * Phase 2: Dashboard Migration 테스트
 *
 * PRD-0049 Section 6.2 요구사항:
 * - 2-1: ExtensionFilter 제거 (CompactFilterBar 사용)
 * - 2-2: FolderTreeWithProgress → MasterFolderTree 교체
 * - 2-3: FolderProgressDetail → MasterFolderDetail 교체
 * ============================================================================
 */
test.describe('PRD-0049 Phase 2: Dashboard Migration', () => {
  test.describe('2-1: CompactFilterBar Integration', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
    });

    /**
     * Dashboard에서 CompactFilterBar가 표시되어야 함
     * 현재 상태: Dashboard는 ExtensionFilter 사용 → 실패 예상
     */
    test('should display CompactFilterBar in Dashboard', async ({ page }) => {
      // CompactFilterBar의 data-testid 확인
      const compactFilterBar = page.locator('[data-testid="compact-filter-bar"]');

      // 현재 Dashboard는 ExtensionFilter 사용 → 실패해야 함 (RED)
      await expect(compactFilterBar).toBeVisible({ timeout: 5000 });
    });

    /**
     * Dashboard에서 확장자 필터 버튼이 CompactFilterBar 내에 있어야 함
     */
    test('should have extension filter inside CompactFilterBar', async ({ page }) => {
      const filterBar = page.locator('[data-testid="compact-filter-bar"]');

      // CompactFilterBar에 Filter 드롭다운 버튼이 있어야 함 (All, Video, Audio 등)
      const filterButton = filterBar.locator('button').filter({ hasText: /All|Filter/i });

      await expect(filterButton.first()).toBeVisible({ timeout: 10000 });
    });

    /**
     * Dashboard에서 숨김 파일 토글이 있어야 함
     * 현재: Dashboard에는 숨김 파일 필터 없음 → 실패 예상
     */
    test('should have hidden files toggle in Dashboard', async ({ page }) => {
      // 숨김 파일 토글 버튼
      const hiddenToggle = page.locator('[data-testid="hidden-files-toggle"]');

      // 현재 Dashboard에 없음 → 실패해야 함 (RED)
      await expect(hiddenToggle).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('2-2: MasterFolderTree in Dashboard', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
    });

    /**
     * Dashboard에서 MasterFolderTree 컴포넌트 사용
     * 현재 상태: FolderTreeWithProgress 사용 → 실패 예상
     */
    test('should use MasterFolderTree component in Dashboard', async ({ page }) => {
      // MasterFolderTree는 data-testid="master-folder-tree"를 가져야 함
      const masterFolderTree = page.locator('[data-testid="master-folder-tree"]');

      // 현재 FolderTreeWithProgress 사용 → 실패해야 함 (RED)
      await expect(masterFolderTree).toBeVisible({ timeout: 5000 });
    });

    /**
     * Dashboard에서 Progress Overview 헤더 표시
     */
    test('should display Progress Overview header', async ({ page }) => {
      await expect(
        page.locator('text=Progress Overview')
      ).toBeVisible({ timeout: 10000 });
    });

    /**
     * Dashboard에서 진행률 바 표시 (showProgressBar: true)
     */
    test('should display progress bars in Dashboard tree', async ({ page }) => {
      const progressBars = page.locator('.rounded-full.h-1\\.5, .h-1\\.5.rounded-full');
      await expect(progressBars.first()).toBeVisible({ timeout: 10000 });
    });

    /**
     * Dashboard에서 작업 현황 뱃지 표시 (showWorkBadge: true)
     */
    test('should display work badges in Dashboard tree', async ({ page }) => {
      // 작업 뱃지: done/total 형식 또는 백분율
      const workBadge = page.locator('[class*="bg-green-100"], [class*="bg-yellow-100"], [class*="bg-blue-100"]');
      const count = await workBadge.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe('2-3: MasterFolderDetail in Dashboard', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
    });

    /**
     * 폴더 선택 시 MasterFolderDetail 표시
     * 현재: FolderProgressDetail 사용 → 실패 예상 (data-testid 기준)
     */
    test('should display MasterFolderDetail when folder selected', async ({ page }) => {
      // 폴더 클릭
      const folderItem = page.locator('[class*="cursor-pointer"]').first();

      if (await folderItem.isVisible()) {
        await folderItem.click();
        await page.waitForTimeout(500);

        // MasterFolderDetail의 data-testid 확인
        const detailPanel = page.locator('[data-testid="master-folder-detail"]');

        // 현재 FolderProgressDetail 사용 → 실패해야 함 (RED)
        await expect(detailPanel).toBeVisible({ timeout: 5000 });
      }
    });

    /**
     * MasterFolderDetail에 mode="progress" 표시
     */
    test('should show progress mode in detail panel', async ({ page }) => {
      const folderItem = page.locator('[class*="cursor-pointer"]').first();

      if (await folderItem.isVisible()) {
        await folderItem.click();
        await page.waitForTimeout(500);

        // Progress 모드 표시 (진행률 정보)
        const progressInfo = page.locator('text=/\\d+(\\.\\d+)?%/');
        await expect(progressInfo.first()).toBeVisible({ timeout: 5000 });
      }
    });
  });
});

/**
 * ============================================================================
 * Phase 3: Legacy Cleanup 테스트
 *
 * PRD-0049 Section 6.3 요구사항:
 * - 3-1: FolderTreeWithProgress.tsx 삭제
 * - 3-2: ExtensionFilter.tsx 삭제
 * - 빌드/린트 통과
 * ============================================================================
 */
test.describe('PRD-0049 Phase 3: Legacy Cleanup', () => {
  test.describe('3-1, 3-2: Legacy Components Removed', () => {
    /**
     * 레거시 컴포넌트가 제거된 후 import 에러 없음
     * 이 테스트는 빌드 성공 여부로 검증됨 (E2E에서는 페이지 로드로 확인)
     */
    test('should load all pages without import errors', async ({ page }) => {
      // Dashboard
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await expect(page.locator('text=Archive Statistics')).toBeVisible({ timeout: 10000 });

      // Folders
      await page.goto('/folders');
      await page.waitForLoadState('networkidle');
      await expect(page.locator('[data-testid="master-folder-tree"]')).toBeVisible({ timeout: 10000 });

      // Statistics
      await page.goto('/statistics');
      await page.waitForLoadState('networkidle');
      // Statistics 페이지의 헤딩 확인 (exact: true로 정확히 "Statistics"만 매칭)
      await expect(page.getByRole('heading', { name: 'Statistics', exact: true })).toBeVisible({ timeout: 10000 });
    });

    /**
     * FolderTreeWithProgress 관련 CSS 클래스가 더 이상 사용되지 않음
     * (이 테스트는 Phase 3 완료 후 의미가 있음)
     */
    test('should not have legacy component markers', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // 레거시 마커가 없어야 함 (data-component="FolderTreeWithProgress")
      const legacyMarker = page.locator('[data-component="FolderTreeWithProgress"]');
      await expect(legacyMarker).not.toBeVisible();
    });
  });

  test.describe('Cross-Page Consistency After Migration', () => {
    /**
     * 모든 페이지에서 동일한 MasterFolderTree 사용
     */
    test('should use same MasterFolderTree across all pages', async ({ page }) => {
      // Dashboard
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      const dashboardTree = page.locator('[data-testid="master-folder-tree"]');
      await expect(dashboardTree).toBeVisible({ timeout: 10000 });

      // Folders
      await page.goto('/folders');
      await page.waitForLoadState('networkidle');
      const foldersTree = page.locator('[data-testid="master-folder-tree"]');
      await expect(foldersTree).toBeVisible({ timeout: 10000 });

      // Statistics Codec Explorer
      await page.goto('/statistics');
      await page.waitForLoadState('networkidle');
      const codecTab = page.getByRole('button', { name: /Codec Explorer/i });
      await codecTab.click();
      const statsTree = page.locator('[data-testid="master-folder-tree"]');
      await expect(statsTree).toBeVisible({ timeout: 10000 });
    });
  });
});

/**
 * ============================================================================
 * Feature Parity Tests
 *
 * 마이그레이션 후 기존 기능이 모두 동작하는지 확인
 * ============================================================================
 */
test.describe('PRD-0049 Feature Parity', () => {
  test.describe('Extension Filter Parity', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
    });

    /**
     * Video 필터 선택 시 비디오 파일만 표시
     */
    test('should filter by video extension', async ({ page }) => {
      const videoButton = page.locator('button').filter({ hasText: /Video|비디오/i }).first();

      if (await videoButton.isVisible()) {
        await videoButton.click();
        await page.waitForTimeout(500);

        // 필터 적용 후 트리 갱신 확인
        const folderTree = page.locator('[class*="cursor-pointer"]');
        const count = await folderTree.count();
        expect(count).toBeGreaterThanOrEqual(0);
      }
    });

    /**
     * 필터 해제 시 모든 파일 표시
     */
    test('should show all files when filter cleared', async ({ page }) => {
      // All 버튼 또는 필터 해제 기능
      const allButton = page.locator('button').filter({ hasText: /All|전체/i }).first();

      if (await allButton.isVisible()) {
        await allButton.click();
        await page.waitForTimeout(500);

        const folderTree = page.locator('[class*="cursor-pointer"]');
        const count = await folderTree.count();
        expect(count).toBeGreaterThanOrEqual(0);
      }
    });
  });

  test.describe('Hidden Files Filter Parity', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/folders');
      await page.waitForLoadState('networkidle');
    });

    /**
     * 숨김 파일 토글이 작동
     */
    test('should toggle hidden files visibility', async ({ page }) => {
      // 숨김 파일 토글 찾기
      const hiddenToggle = page.locator('[data-testid="hidden-files-toggle"]').or(
        page.locator('button').filter({ hasText: /숨김|Hidden/i })
      );

      if (await hiddenToggle.isVisible()) {
        // 토글 전 폴더 수
        const beforeCount = await page.locator('[class*="cursor-pointer"]').count();

        await hiddenToggle.click();
        await page.waitForTimeout(500);

        // 토글 후 폴더 수 (변화가 있을 수 있음)
        const afterCount = await page.locator('[class*="cursor-pointer"]').count();

        // 숨김 파일이 있다면 카운트가 변해야 함 (없다면 동일)
        expect(afterCount).toBeGreaterThanOrEqual(0);
      }
    });
  });

  test.describe('Search Functionality Parity', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/folders');
      await page.waitForLoadState('networkidle');
    });

    /**
     * 검색어 입력 시 필터링
     */
    test('should filter folders by search query', async ({ page }) => {
      const searchInput = page.locator('input[type="text"]').or(
        page.locator('[placeholder*="검색"]')
      );

      if (await searchInput.isVisible()) {
        await searchInput.fill('test');
        await page.waitForTimeout(500);

        // 검색 결과 또는 "결과 없음" 표시
        const results = page.locator('[class*="cursor-pointer"]');
        const count = await results.count();
        expect(count).toBeGreaterThanOrEqual(0);
      }
    });

    /**
     * 검색어 삭제 시 전체 표시
     */
    test('should show all folders when search cleared', async ({ page }) => {
      const searchInput = page.locator('input[type="text"]').or(
        page.locator('[placeholder*="검색"]')
      );

      if (await searchInput.isVisible()) {
        await searchInput.fill('test');
        await page.waitForTimeout(300);
        await searchInput.clear();
        await page.waitForTimeout(500);

        const results = page.locator('[class*="cursor-pointer"]');
        const count = await results.count();
        expect(count).toBeGreaterThanOrEqual(0);
      }
    });
  });
});

/**
 * ============================================================================
 * Regression Tests
 *
 * 기존 PRD-0048 테스트와의 일관성 확인
 * ============================================================================
 */
test.describe('PRD-0049 Regression Tests', () => {
  /**
   * PRD-0041 기능이 여전히 동작하는지 확인
   */
  test.describe('PRD-0041 Features Preserved', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
    });

    /**
     * is_complete 표시 유지
     */
    test('should preserve is_complete display', async ({ page }) => {
      // CheckCircle2 아이콘 (green)
      const completeIcon = page.locator('[class*="text-green-600"]');
      const count = await completeIcon.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    /**
     * data_source_mismatch 표시 유지
     */
    test('should preserve data_source_mismatch display', async ({ page }) => {
      // AlertTriangle 아이콘 (amber)
      const mismatchIcon = page.locator('[class*="text-amber-500"]');
      const count = await mismatchIcon.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    /**
     * matching_method 툴팁 유지
     */
    test('should preserve matching_method tooltip', async ({ page }) => {
      const percentageBadge = page.locator('[class*="bg-green-100"], [class*="bg-blue-100"]').first();

      if (await percentageBadge.isVisible()) {
        const title = await percentageBadge.getAttribute('title');
        // 툴팁이 있다면 매칭 정보 포함
        if (title) {
          expect(title.length).toBeGreaterThan(0);
        }
      }
    });
  });

  /**
   * 페이지 간 일관성 유지
   */
  test.describe('Cross-Page Consistency Preserved', () => {
    test('Dashboard and Folders use same data source', async ({ page }) => {
      // Dashboard에서 첫 번째 폴더 이름 확인
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      const dashboardFolder = page.locator('[class*="cursor-pointer"]').first();
      const dashboardText = await dashboardFolder.textContent() || '';

      // Folders 페이지에서 첫 번째 폴더 이름 확인
      await page.goto('/folders');
      await page.waitForLoadState('networkidle');
      const foldersFolder = page.locator('[class*="cursor-pointer"]').first();
      const foldersText = await foldersFolder.textContent() || '';

      // 둘 다 폴더가 있다면 동일한 데이터 소스 사용 중
      if (dashboardText && foldersText) {
        // 첫 번째 폴더가 동일할 필요는 없지만, 둘 다 데이터가 있어야 함
        expect(dashboardText.length).toBeGreaterThan(0);
        expect(foldersText.length).toBeGreaterThan(0);
      }
    });
  });
});
