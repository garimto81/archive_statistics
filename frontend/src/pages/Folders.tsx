/**
 * Folders Page - MasterFolderTree 통합 버전
 *
 * 레거시 FolderTree + foldersApi 대신
 * 통합 MasterFolderTree + MasterFolderDetail 사용
 *
 * PRD: PRD-0033-FOLDER-TREE-UNIFICATION.md Section 4.3
 */
import { useState, useCallback } from 'react';
import MasterFolderTree from '../components/MasterFolderTree';
import MasterFolderDetail from '../components/MasterFolderDetail';
import type { FolderWithProgress } from '../types';

export default function FoldersPage() {
  const [selectedFolder, setSelectedFolder] = useState<FolderWithProgress | null>(null);

  // 폴더 선택 핸들러
  const handleFolderSelect = useCallback((folder: FolderWithProgress) => {
    setSelectedFolder(folder);
  }, []);

  // 상세 패널 닫기
  const handleCloseDetail = useCallback(() => {
    setSelectedFolder(null);
  }, []);

  return (
    <div className="h-full flex flex-col">
      {/* 그리드 레이아웃: 트리 (1/3) + 상세 (2/3) */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 min-h-0">
        {/* 좌측: 폴더 트리 */}
        <div className="lg:col-span-1 flex flex-col min-h-0">
          <MasterFolderTree
            // 기본 설정
            initialDepth={2}
            showFiles={false}
            enableLazyLoading={true}
            enableAutoRefresh={true}
            autoRefreshInterval={60000}
            // 필터바 설정 (explorer 모드)
            showFilterBar={true}
            filterBarTitle="Folder Explorer"
            enableExtensionFilter={true}
            enableHiddenFilter={true}
            enableDisplayToggles={false}
            enableSearch={true}
            // 진행률/코덱 표시 OFF (explorer 모드)
            showProgressBar={false}
            showWorkBadge={false}
            showCodecBadge={false}
            // 이벤트 핸들러
            onFolderSelect={handleFolderSelect}
            selectedPath={selectedFolder?.path}
            // 스타일
            className="h-full"
          />
        </div>

        {/* 우측: 폴더 상세 */}
        <div className="lg:col-span-2 min-h-0">
          <MasterFolderDetail
            folder={selectedFolder}
            mode="explorer"
            onClose={handleCloseDetail}
            onFolderSelect={handleFolderSelect}
            className="h-full overflow-y-auto"
          />
        </div>
      </div>
    </div>
  );
}
