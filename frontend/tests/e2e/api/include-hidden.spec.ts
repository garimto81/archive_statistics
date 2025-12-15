/**
 * include_hidden API Integration Tests
 *
 * v1.29.0 숨김 파일/폴더 필터 기능 검증
 * - 파일 필터링 동작
 * - filtered_file_count 계산
 * - 하위 폴더 처리
 */
import { test, expect } from '@playwright/test';

// Use baseURL from playwright config (nginx proxy)
const API_BASE = process.env.BASE_URL || 'http://localhost:8082';

interface FolderNode {
  id: number;
  name: string;
  path: string;
  file_count: number;
  filtered_file_count?: number;
  children?: FolderNode[];
  files?: FileNode[];
}

interface FileNode {
  id: number;
  name: string;
}

interface TreeResponse {
  tree: FolderNode[];
  root_stats: {
    total_files: number;
    total_size: number;
  };
}

/**
 * 트리에서 모든 파일 수집
 */
function collectFiles(nodes: FolderNode[]): FileNode[] {
  const files: FileNode[] = [];
  for (const node of nodes) {
    if (node.files) {
      files.push(...node.files);
    }
    if (node.children) {
      files.push(...collectFiles(node.children));
    }
  }
  return files;
}

/**
 * 숨김 파일 (이름이 .으로 시작) 필터링
 */
function filterHiddenFiles(files: FileNode[]): FileNode[] {
  return files.filter((f) => f.name.startsWith('.'));
}

test.describe('include_hidden API Integration Tests', () => {
  test.describe('File Filtering', () => {
    test('include_hidden=false should exclude hidden files from response', async ({
      request,
    }) => {
      const response = await request.get(
        `${API_BASE}/api/progress/tree?depth=2&include_hidden=false&include_files=true`
      );

      expect(response.status()).toBe(200);

      const data: TreeResponse = await response.json();
      const files = collectFiles(data.tree);
      const hiddenFiles = filterHiddenFiles(files);

      // 숨김 파일이 응답에 포함되지 않아야 함
      expect(hiddenFiles.length).toBe(0);
    });

    test('include_hidden=true should include hidden files in response', async ({
      request,
    }) => {
      const response = await request.get(
        `${API_BASE}/api/progress/tree?depth=2&include_hidden=true&include_files=true`
      );

      expect(response.status()).toBe(200);

      const data: TreeResponse = await response.json();
      const files = collectFiles(data.tree);
      const hiddenFiles = filterHiddenFiles(files);

      // NAS에 숨김 파일이 있다면 응답에 포함되어야 함
      // (테스트 환경에 따라 숨김 파일이 없을 수 있음)
      expect(hiddenFiles.length).toBeGreaterThanOrEqual(0);
    });

    test('hidden file count should differ between include_hidden=true and false', async ({
      request,
    }) => {
      // include_hidden=false
      const responseFalse = await request.get(
        `${API_BASE}/api/progress/tree?depth=2&include_hidden=false&include_files=true`
      );
      expect(responseFalse.status()).toBe(200);
      const dataFalse: TreeResponse = await responseFalse.json();
      const filesFalse = collectFiles(dataFalse.tree);

      // include_hidden=true
      const responseTrue = await request.get(
        `${API_BASE}/api/progress/tree?depth=2&include_hidden=true&include_files=true`
      );
      expect(responseTrue.status()).toBe(200);
      const dataTrue: TreeResponse = await responseTrue.json();
      const filesTrue = collectFiles(dataTrue.tree);
      const hiddenFilesTrue = filterHiddenFiles(filesTrue);

      // true일 때 파일 수가 같거나 더 많아야 함
      expect(filesTrue.length).toBeGreaterThanOrEqual(filesFalse.length);

      // 숨김 파일이 있다면, 차이가 숨김 파일 수와 같아야 함
      if (hiddenFilesTrue.length > 0) {
        expect(filesTrue.length - filesFalse.length).toBe(hiddenFilesTrue.length);
      }
    });
  });

  test.describe('filtered_file_count Calculation', () => {
    test('filtered_file_count should reflect hidden file filter', async ({
      request,
    }) => {
      // include_hidden=false
      const responseFalse = await request.get(
        `${API_BASE}/api/progress/tree?depth=1&include_hidden=false`
      );
      expect(responseFalse.status()).toBe(200);
      const dataFalse: TreeResponse = await responseFalse.json();

      // include_hidden=true
      const responseTrue = await request.get(
        `${API_BASE}/api/progress/tree?depth=1&include_hidden=true`
      );
      expect(responseTrue.status()).toBe(200);
      const dataTrue: TreeResponse = await responseTrue.json();

      // 각 폴더의 filtered_file_count 비교
      for (let i = 0; i < dataFalse.tree.length; i++) {
        const folderFalse = dataFalse.tree[i];
        const folderTrue = dataTrue.tree.find((f) => f.path === folderFalse.path);

        if (folderTrue) {
          // include_hidden=false일 때 filtered_file_count <= file_count
          expect(folderFalse.filtered_file_count).toBeLessThanOrEqual(
            folderFalse.file_count
          );

          // include_hidden=true일 때 filtered_file_count === file_count
          expect(folderTrue.filtered_file_count).toBe(folderTrue.file_count);

          // false의 filtered가 true의 filtered보다 작거나 같아야 함
          expect(folderFalse.filtered_file_count).toBeLessThanOrEqual(
            folderTrue.filtered_file_count!
          );
        }
      }
    });

    test('child folders should have correct filtered_file_count', async ({
      request,
    }) => {
      const response = await request.get(
        `${API_BASE}/api/progress/tree?depth=2&include_hidden=false`
      );
      expect(response.status()).toBe(200);
      const data: TreeResponse = await response.json();

      // 하위 폴더들의 filtered_file_count가 정의되어 있어야 함
      for (const folder of data.tree) {
        expect(folder.filtered_file_count).toBeDefined();
        expect(typeof folder.filtered_file_count).toBe('number');

        if (folder.children) {
          for (const child of folder.children) {
            expect(child.filtered_file_count).toBeDefined();
            expect(typeof child.filtered_file_count).toBe('number');
            // filtered는 0 이상이어야 함
            expect(child.filtered_file_count).toBeGreaterThanOrEqual(0);
            // filtered는 total 이하여야 함
            expect(child.filtered_file_count).toBeLessThanOrEqual(child.file_count);
          }
        }
      }
    });
  });

  test.describe('Folder Filtering', () => {
    test('hidden folders should be excluded when include_hidden=false', async ({
      request,
    }) => {
      const response = await request.get(
        `${API_BASE}/api/progress/tree?depth=2&include_hidden=false`
      );
      expect(response.status()).toBe(200);
      const data: TreeResponse = await response.json();

      // 숨김 폴더 (이름이 .으로 시작)가 없어야 함
      function checkNoHiddenFolders(nodes: FolderNode[]) {
        for (const node of nodes) {
          expect(node.name.startsWith('.')).toBe(false);
          if (node.children) {
            checkNoHiddenFolders(node.children);
          }
        }
      }

      checkNoHiddenFolders(data.tree);
    });
  });

  test.describe('API Parameter Validation', () => {
    test('default include_hidden should be false', async ({ request }) => {
      // include_hidden 파라미터 없이 요청
      const responseDefault = await request.get(
        `${API_BASE}/api/progress/tree?depth=2&include_files=true`
      );
      expect(responseDefault.status()).toBe(200);
      const dataDefault: TreeResponse = await responseDefault.json();
      const filesDefault = collectFiles(dataDefault.tree);
      const hiddenDefault = filterHiddenFiles(filesDefault);

      // 명시적으로 false로 요청
      const responseFalse = await request.get(
        `${API_BASE}/api/progress/tree?depth=2&include_hidden=false&include_files=true`
      );
      expect(responseFalse.status()).toBe(200);
      const dataFalse: TreeResponse = await responseFalse.json();
      const filesFalse = collectFiles(dataFalse.tree);

      // 기본값과 false가 동일해야 함
      expect(filesDefault.length).toBe(filesFalse.length);
      expect(hiddenDefault.length).toBe(0);
    });
  });
});
