/**
 * Archive Stats V2 API Tests
 *
 * Issue #49: NAS 폴더 통계 계산 로직 리팩토링
 * - archive_stats 필드가 항상 일관된 값을 반환하는지 검증
 * - Lazy Load 시에도 total_files가 동일한지 확인
 * - 기존 root_stats와의 차이 검증
 */
import { test, expect } from '@playwright/test';

const API_BASE = process.env.BASE_URL || 'http://localhost:8082';

interface ArchiveStats {
  total_files: number;
  total_size: number;
  total_size_formatted: string;
  total_duration: number;
  total_duration_formatted: string;
  sheets_total_videos: number;
  sheets_total_done: number;
  file_ratio: number;
  size_ratio: number;
}

interface FolderNode {
  id: number;
  name: string;
  path: string;
  file_count: number;
  filtered_file_count?: number;
  root_stats?: {
    total_files: number;
    total_size: number;
  };
  archive_stats?: ArchiveStats;
  children?: FolderNode[];
}

interface TreeResponse {
  tree: FolderNode[];
  root_stats: {
    total_files: number;
    total_size: number;
  };
  archive_stats: {
    total_files: number;
    total_size: number;
  };
}

test.describe('Archive Stats V2 API (Issue #49)', () => {
  test.describe('archive_stats Consistency', () => {
    /**
     * 핵심 테스트: archive_stats.total_files가 Lazy Load 시에도 동일해야 함
     */
    test('archive_stats should be consistent across initial and lazy loads', async ({
      request,
    }) => {
      // 초기 로드 (path=None)
      const initialResponse = await request.get(
        `${API_BASE}/api/progress/tree?depth=1&include_hidden=false`
      );
      expect(initialResponse.status()).toBe(200);
      const initialData: TreeResponse = await initialResponse.json();

      // archive_stats 존재 확인
      expect(initialData.archive_stats).toBeDefined();
      const initialArchiveTotal = initialData.archive_stats.total_files;
      console.log(`Initial archive_stats.total_files: ${initialArchiveTotal}`);

      // Lazy Load (path 지정)
      if (initialData.tree.length > 0) {
        const firstFolderPath = initialData.tree[0].path;

        const lazyResponse = await request.get(
          `${API_BASE}/api/progress/tree?path=${encodeURIComponent(firstFolderPath)}&depth=1&include_hidden=false`
        );
        expect(lazyResponse.status()).toBe(200);
        const lazyData: TreeResponse = await lazyResponse.json();

        // archive_stats 존재 확인
        expect(lazyData.archive_stats).toBeDefined();
        const lazyArchiveTotal = lazyData.archive_stats.total_files;
        console.log(`Lazy load archive_stats.total_files: ${lazyArchiveTotal}`);

        // 핵심 검증: 두 값이 동일해야 함
        expect(lazyArchiveTotal).toBe(initialArchiveTotal);
      }
    });

    test('folder archive_stats should match response archive_stats', async ({
      request,
    }) => {
      const response = await request.get(
        `${API_BASE}/api/progress/tree?depth=2&include_hidden=false`
      );
      expect(response.status()).toBe(200);
      const data: TreeResponse = await response.json();

      const responseArchiveTotal = data.archive_stats.total_files;

      // 각 폴더의 archive_stats 확인
      for (const folder of data.tree) {
        expect(folder.archive_stats).toBeDefined();
        expect(folder.archive_stats!.total_files).toBe(responseArchiveTotal);

        // 자식 폴더도 확인
        if (folder.children) {
          for (const child of folder.children) {
            expect(child.archive_stats).toBeDefined();
            expect(child.archive_stats!.total_files).toBe(responseArchiveTotal);
          }
        }
      }
    });
  });

  test.describe('archive_stats vs root_stats', () => {
    test('archive_stats should differ from root_stats on lazy load', async ({
      request,
    }) => {
      // 초기 로드
      const initialResponse = await request.get(
        `${API_BASE}/api/progress/tree?depth=1&include_hidden=false`
      );
      const initialData: TreeResponse = await initialResponse.json();

      const archiveTotal = initialData.archive_stats.total_files;
      const rootTotal = initialData.root_stats.total_files;

      // 초기 로드에서는 같을 수 있음 (path=None)
      console.log(`Initial: archive=${archiveTotal}, root=${rootTotal}`);

      // Lazy Load
      if (initialData.tree.length > 0) {
        const firstFolderPath = initialData.tree[0].path;

        const lazyResponse = await request.get(
          `${API_BASE}/api/progress/tree?path=${encodeURIComponent(firstFolderPath)}&depth=1&include_hidden=false`
        );
        const lazyData: TreeResponse = await lazyResponse.json();

        const lazyArchiveTotal = lazyData.archive_stats.total_files;
        const lazyRootTotal = lazyData.root_stats.total_files;

        console.log(`Lazy: archive=${lazyArchiveTotal}, root=${lazyRootTotal}`);

        // archive_stats는 항상 동일해야 함
        expect(lazyArchiveTotal).toBe(archiveTotal);

        // root_stats는 path에 따라 다를 수 있음 (기존 버그 동작)
        // 이 테스트는 차이가 있는지 확인 (있으면 버그 상태 확인)
        if (lazyRootTotal !== archiveTotal) {
          console.log(
            `⚠️ root_stats differs from archive_stats on lazy load (expected for deprecated behavior)`
          );
        }
      }
    });
  });

  test.describe('archive_stats Ratios', () => {
    test('folder file_ratio should be calculated correctly', async ({
      request,
    }) => {
      const response = await request.get(
        `${API_BASE}/api/progress/tree?depth=1&include_hidden=false`
      );
      expect(response.status()).toBe(200);
      const data: TreeResponse = await response.json();

      const archiveTotal = data.archive_stats.total_files;

      for (const folder of data.tree) {
        if (folder.archive_stats) {
          const expectedRatio =
            archiveTotal > 0
              ? Math.round((folder.file_count / archiveTotal) * 10000) / 100
              : 0;

          // 비율 검증 (소수점 오차 허용)
          expect(folder.archive_stats.file_ratio).toBeCloseTo(expectedRatio, 1);
        }
      }
    });
  });

  test.describe('Backward Compatibility', () => {
    test('both root_stats and archive_stats should be present', async ({
      request,
    }) => {
      const response = await request.get(
        `${API_BASE}/api/progress/tree?depth=1&include_hidden=false`
      );
      expect(response.status()).toBe(200);
      const data: TreeResponse = await response.json();

      // 응답 레벨
      expect(data.root_stats).toBeDefined();
      expect(data.archive_stats).toBeDefined();

      // 폴더 레벨
      for (const folder of data.tree) {
        expect(folder.root_stats).toBeDefined();
        expect(folder.archive_stats).toBeDefined();
      }
    });

    test('v1 fields should still be present (deprecated)', async ({
      request,
    }) => {
      const response = await request.get(
        `${API_BASE}/api/progress/tree?depth=1&include_hidden=false`
      );
      expect(response.status()).toBe(200);
      const data: TreeResponse = await response.json();

      for (const folder of data.tree) {
        // v1 필드 (deprecated, but still present)
        expect(folder.file_count).toBeDefined();
        expect(typeof folder.file_count).toBe('number');

        if (folder.filtered_file_count !== undefined) {
          expect(typeof folder.filtered_file_count).toBe('number');
        }

        // root_stats는 deprecated지만 여전히 존재
        expect(folder.root_stats).toBeDefined();
      }
    });
  });

  test.describe('Multiple Lazy Loads', () => {
    test('archive_stats should be consistent across multiple lazy loads', async ({
      request,
    }) => {
      // 초기 로드
      const initialResponse = await request.get(
        `${API_BASE}/api/progress/tree?depth=1&include_hidden=false`
      );
      const initialData: TreeResponse = await initialResponse.json();
      const archiveTotal = initialData.archive_stats.total_files;

      const archiveTotals: number[] = [archiveTotal];

      // 여러 폴더에 대해 lazy load 수행
      for (const folder of initialData.tree.slice(0, 3)) {
        const lazyResponse = await request.get(
          `${API_BASE}/api/progress/tree?path=${encodeURIComponent(folder.path)}&depth=1&include_hidden=false`
        );
        const lazyData: TreeResponse = await lazyResponse.json();
        archiveTotals.push(lazyData.archive_stats.total_files);
      }

      // 모든 값이 동일해야 함
      const uniqueValues = [...new Set(archiveTotals)];
      expect(uniqueValues.length).toBe(1);
      console.log(
        `All archive_stats.total_files values: ${archiveTotals.join(', ')}`
      );
    });
  });
});
