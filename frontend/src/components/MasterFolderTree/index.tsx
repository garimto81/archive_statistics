/**
 * MasterFolderTree - 통합 폴더 트리 컴포넌트
 *
 * 모든 폴더 트리 기능을 포함하며, Props로 필요한 기능만 활성화
 * - Dashboard: showProgressBar, showWorkBadge, showFiles
 * - Folders: 기본 탐색, 검색
 * - Statistics: showCodecBadge
 *
 * PRD: PRD-0033-FOLDER-TREE-UNIFICATION.md
 */
import { useState, useCallback, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  FileVideo,
  RefreshCw,
  Film,
  Music,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import clsx from 'clsx';
import { progressApi, statsApi } from '../../services/api';
import ProgressBar from '../ProgressBar';
import CompactFilterBar from './CompactFilterBar';
import type { FolderWithProgress, FileWithProgress, WorkSummary, FolderCodecSummary } from '../../types';

// ============================================================================
// Types
// ============================================================================

export interface MasterFolderTreeProps {
  // 데이터 옵션
  initialPath?: string;
  initialDepth?: number;

  // 표시 옵션
  showFiles?: boolean;
  showProgressBar?: boolean;
  showWorkBadge?: boolean;
  showCodecBadge?: boolean;
  showSizeInfo?: boolean;
  showFileCount?: boolean;
  showLegend?: boolean;  // PRD-0049: 범례 표시

  // 필터 옵션
  selectedExtensions?: string[];
  showHiddenFiles?: boolean;
  searchQuery?: string;

  // 동작 옵션
  enableLazyLoading?: boolean;
  enableAutoRefresh?: boolean;
  autoRefreshInterval?: number;

  // 상세 패널 옵션 (외부에서 처리하는 경우 'none')
  detailPanelMode?: 'none' | 'progress' | 'codec' | 'explorer';

  // 필터바 옵션
  showFilterBar?: boolean;
  filterBarTitle?: string;
  enableExtensionFilter?: boolean;
  enableHiddenFilter?: boolean;
  enableDisplayToggles?: boolean;
  enableSearch?: boolean;

  // 콜백
  onFolderSelect?: (folder: FolderWithProgress) => void;
  onFileSelect?: (file: FileWithProgress) => void;
  onFolderExpand?: (folder: FolderWithProgress) => void;

  // 외부 선택 상태
  selectedPath?: string;

  // 스타일 옵션
  className?: string;
  height?: string | number;
  compact?: boolean;
}

interface FolderNodeProps {
  folder: FolderWithProgress;
  level: number;
  showFiles: boolean;
  showProgressBar: boolean;
  showWorkBadge: boolean;
  showCodecBadge: boolean;
  selectedPath?: string;
  onFolderSelect?: (folder: FolderWithProgress) => void;
  onFileSelect?: (file: FileWithProgress) => void;
  onLoadChildren?: (path: string) => void;
  isLoadingChildren?: boolean;
  searchQuery?: string;
}

interface FileNodeProps {
  file: FileWithProgress;
  level: number;
  showProgressBar: boolean;
  showCodecBadge: boolean;
  selectedPath?: string;
  onSelect?: (file: FileWithProgress) => void;
}

// ============================================================================
// Helpers
// ============================================================================

function getWorkSummary(folder: FolderWithProgress): WorkSummary | null {
  const summary = folder.work_summary;
  if (!summary) return null;
  if (summary.task_count === 0 && summary.total_done === 0 && summary.total_files === 0) {
    return null;
  }
  return summary;
}

function updateFolderChildren(
  folders: FolderWithProgress[],
  parentPath: string,
  children: FolderWithProgress[]
): FolderWithProgress[] {
  return folders.map(folder => {
    if (folder.path === parentPath) {
      return { ...folder, children };
    }
    if (folder.children && folder.children.length > 0) {
      return {
        ...folder,
        children: updateFolderChildren(folder.children, parentPath, children)
      };
    }
    return folder;
  });
}

function filterFoldersBySearch(
  folders: FolderWithProgress[],
  query: string
): FolderWithProgress[] {
  if (!query) return folders;
  const lowerQuery = query.toLowerCase();

  return folders.reduce<FolderWithProgress[]>((acc, folder) => {
    const nameMatches = folder.name.toLowerCase().includes(lowerQuery);
    const filteredChildren = folder.children
      ? filterFoldersBySearch(folder.children, query)
      : [];

    if (nameMatches || filteredChildren.length > 0) {
      acc.push({
        ...folder,
        children: filteredChildren.length > 0 ? filteredChildren : folder.children
      });
    }
    return acc;
  }, []);
}

// ============================================================================
// FileNode Component
// ============================================================================

function FileNode({
  file,
  level,
  showProgressBar,
  showCodecBadge,
  selectedPath,
  onSelect
}: FileNodeProps) {
  const isSelected = selectedPath === file.path;
  const hasProgress = file.metadata_progress && file.metadata_progress.hand_count > 0;

  return (
    <div
      className={clsx(
        'flex items-center py-1.5 px-2 cursor-pointer rounded transition-colors',
        isSelected ? 'bg-purple-50 text-purple-700' : 'hover:bg-gray-50'
      )}
      style={{ paddingLeft: `${level * 16 + 8}px` }}
      onClick={() => onSelect?.(file)}
    >
      <span className="w-5 h-5 flex items-center justify-center mr-1">
        <span className="w-4" />
      </span>

      <FileVideo className="w-4 h-4 text-purple-400 mr-2 flex-shrink-0" />

      <span className="text-xs font-medium truncate max-w-[180px]" title={file.name}>
        {file.name}
      </span>

      {/* 파일 메타데이터 */}
      <div className="flex items-center gap-2 ml-2 flex-shrink-0 text-xs">
        <span className="text-gray-500 font-mono">{file.size_formatted}</span>
        <span className="text-gray-300">·</span>

        {showCodecBadge && (
          <div className="flex items-center gap-1">
            {file.video_codec ? (
              <span className="inline-flex items-center px-1 py-0.5 rounded bg-blue-50 text-blue-600">
                <Film className="w-3 h-3 mr-0.5" />
                {file.video_codec}
              </span>
            ) : (
              <span className="text-gray-300">-</span>
            )}
            {file.audio_codec && (
              <span className="inline-flex items-center px-1 py-0.5 rounded bg-green-50 text-green-600">
                <Music className="w-3 h-3 mr-0.5" />
                {file.audio_codec}
              </span>
            )}
          </div>
        )}

        <span className="text-gray-300">·</span>
        <span className="text-gray-500 font-mono">{file.duration_formatted}</span>
      </div>

      {/* Progress Bar */}
      {showProgressBar && hasProgress && file.metadata_progress && (
        <>
          <div className="flex-1 max-w-[120px] ml-2">
            <ProgressBar
              metadataProgress={file.metadata_progress.progress_percent}
              isComplete={file.metadata_progress.is_complete}
              size="sm"
              showLabel={false}
              showPercentage={false}
            />
          </div>
          <span
            className={clsx(
              'text-xs ml-1 flex-shrink-0',
              file.metadata_progress.is_complete ? 'text-green-600' : 'text-gray-500'
            )}
          >
            {file.metadata_progress.progress_percent.toFixed(0)}%
            {file.metadata_progress.is_complete && ' ✓'}
          </span>
        </>
      )}
    </div>
  );
}

// ============================================================================
// FolderNode Component
// ============================================================================

function FolderNode({
  folder,
  level,
  showFiles,
  showProgressBar,
  showWorkBadge,
  showCodecBadge,
  selectedPath,
  onFolderSelect,
  onFileSelect,
  onLoadChildren,
  isLoadingChildren,
  searchQuery,
}: FolderNodeProps) {
  const [isOpen, setIsOpen] = useState(level < 1 || !!searchQuery);
  const hasChildren = folder.children && folder.children.length > 0;
  const hasFiles = showFiles && folder.files && folder.files.length > 0;
  const isSelected = selectedPath === folder.path;

  const workSummary = showProgressBar ? getWorkSummary(folder) : null;
  const codecSummary = folder.codec_summary as FolderCodecSummary | null | undefined;
  const mayHaveChildren = folder.folder_count > 0;

  const handleClick = () => {
    const willOpen = !isOpen;
    if (willOpen && !hasChildren && mayHaveChildren && onLoadChildren) {
      onLoadChildren(folder.path);
    }
    if (hasChildren || hasFiles || mayHaveChildren) {
      setIsOpen(willOpen);
    }
    onFolderSelect?.(folder);
  };

  return (
    <div>
      {/* Folder Row */}
      <div
        className={clsx(
          'flex items-center py-1.5 px-2 cursor-pointer rounded-md transition-colors',
          isSelected ? 'bg-primary-100 text-primary-700' : 'hover:bg-gray-50'
        )}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={handleClick}
      >
        {/* Expand/Collapse Icon */}
        <span className="w-5 h-5 flex items-center justify-center mr-1 flex-shrink-0">
          {isLoadingChildren ? (
            <RefreshCw className="w-4 h-4 text-gray-400 animate-spin" />
          ) : hasChildren || hasFiles || mayHaveChildren ? (
            isOpen ? (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-500" />
            )
          ) : (
            <span className="w-4" />
          )}
        </span>

        {/* Folder Icon */}
        <span className="flex-shrink-0">
          {isOpen ? (
            <FolderOpen className="w-5 h-5 text-yellow-500 mr-2" />
          ) : (
            <Folder className="w-5 h-5 text-yellow-500 mr-2" />
          )}
        </span>

        {/* Folder Name */}
        <span className="text-sm font-medium truncate max-w-[160px]" title={folder.name}>
          {folder.name}
        </span>

        {/* File Count & Size - 필터 적용 시 filtered_* 값 사용 */}
        {/* v1.35.3: folder.file_count 사용 (root_stats.total_files 대신) */}
        <span className="text-xs text-gray-500 ml-2 flex-shrink-0 font-mono">
          <span className={folder.filtered_file_count !== folder.file_count ? 'text-blue-600' : ''}>
            {(folder.filtered_file_count ?? folder.file_count).toLocaleString()}
          </span>
          /{folder.file_count.toLocaleString()}
          <span className="mx-1 text-gray-300">·</span>
          <span className={folder.filtered_size !== folder.size ? 'text-blue-600' : ''}>
            {folder.filtered_size_formatted ?? folder.size_formatted}
          </span>
        </span>

        {/* Work Badge (Progress Mode) - PRD-0041 Enhanced */}
        {showWorkBadge && workSummary && (
          <div className="flex items-center gap-1 ml-2 flex-shrink-0">
            {/* Done/Total Badge */}
            <span
              className={clsx(
                'px-1.5 py-0.5 text-xs rounded',
                workSummary.is_complete
                  ? 'bg-green-100 text-green-700'
                  : workSummary.combined_progress >= 100
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-blue-100 text-blue-700'
              )}
              title={workSummary.matching_method
                ? `매칭: ${workSummary.matching_method} (${((workSummary.matching_score || 0) * 100).toFixed(0)}%)`
                : undefined}
            >
              {workSummary.total_done}/{workSummary.total_files}
            </span>

            {/* Complete Badge (PRD-0041: is_complete) */}
            {workSummary.is_complete && (
              <span title="100% 완료 (done = total = NAS files)">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
              </span>
            )}

            {/* Mismatch Warning (PRD-0041: data_source_mismatch) */}
            {workSummary.data_source_mismatch && (
              <span title={`데이터 불일치: 시트(${workSummary.sheets_total_videos}) vs NAS(${workSummary.total_files}) 차이 ${workSummary.mismatch_count || 0}`}>
                <AlertTriangle className="w-4 h-4 text-amber-500" />
              </span>
            )}
          </div>
        )}

        {/* Codec Badge (Codec Mode) */}
        {showCodecBadge && codecSummary && codecSummary.video_codecs && (
          <div className="ml-2 flex items-center gap-1 flex-shrink-0">
            {Object.entries(codecSummary.video_codecs)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 2)
              .map(([codec, count]) => (
                <span
                  key={codec}
                  className="px-1.5 py-0.5 text-xs rounded bg-orange-100 text-orange-700"
                >
                  {codec}: {count}
                </span>
              ))}
          </div>
        )}

        {/* Progress Bar - PRD-0041: use is_complete for accurate completion */}
        {showProgressBar && workSummary && (
          <div className="flex-1 max-w-[150px] ml-3">
            <ProgressBar
              metadataProgress={workSummary.combined_progress}
              isComplete={workSummary.is_complete || workSummary.combined_progress >= 100}
              size="sm"
              showLabel={false}
              showPercentage={false}
            />
          </div>
        )}
      </div>

      {/* Children */}
      {isOpen && (
        <div>
          {/* Files */}
          {hasFiles &&
            folder.files?.map((file) => (
              <FileNode
                key={file.id}
                file={file}
                level={level + 1}
                showProgressBar={showProgressBar}
                showCodecBadge={showCodecBadge}
                selectedPath={selectedPath}
                onSelect={onFileSelect}
              />
            ))}

          {/* Subfolders */}
          {hasChildren &&
            folder.children?.map((child) => (
              <FolderNode
                key={child.id}
                folder={child}
                level={level + 1}
                showFiles={showFiles}
                showProgressBar={showProgressBar}
                showWorkBadge={showWorkBadge}
                showCodecBadge={showCodecBadge}
                selectedPath={selectedPath}
                onFolderSelect={onFolderSelect}
                onFileSelect={onFileSelect}
                onLoadChildren={onLoadChildren}
                isLoadingChildren={isLoadingChildren}
                searchQuery={searchQuery}
              />
            ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function MasterFolderTree({
  // 데이터 옵션
  initialPath,
  initialDepth = 2,

  // 표시 옵션
  showFiles = false,
  showProgressBar = false,
  showWorkBadge = false,
  showCodecBadge = false,
  showLegend = false,  // PRD-0049: 범례 표시

  // 필터 옵션 (외부에서 제어)
  selectedExtensions: externalExtensions,
  showHiddenFiles: externalShowHidden,
  searchQuery: externalSearchQuery,

  // 동작 옵션
  enableLazyLoading = true,
  enableAutoRefresh = false,
  autoRefreshInterval = 60000,

  // 필터바 옵션
  showFilterBar = true,
  filterBarTitle = 'Folder Tree',
  enableExtensionFilter = false,
  enableHiddenFilter = false,
  enableDisplayToggles = false,
  enableSearch = false,

  // 콜백
  onFolderSelect,
  onFileSelect,

  // 외부 선택 상태
  selectedPath: externalSelectedPath,

  // 스타일 옵션
  className,
  height,
}: MasterFolderTreeProps) {
  const queryClient = useQueryClient();

  // 내부 상태 (필터바 사용 시)
  const [internalExtensions, setInternalExtensions] = useState<string[]>([]);
  const [internalShowHidden, setInternalShowHidden] = useState(false);
  const [internalSearchQuery, setInternalSearchQuery] = useState('');
  const [internalShowProgress, setInternalShowProgress] = useState(showProgressBar);
  const [internalShowCodec, setInternalShowCodec] = useState(showCodecBadge);
  const [internalShowFiles, setInternalShowFiles] = useState(showFiles);

  // 최종 값 (외부 > 내부)
  const extensions = externalExtensions ?? internalExtensions;
  const showHidden = externalShowHidden ?? internalShowHidden;
  const searchQuery = externalSearchQuery ?? internalSearchQuery;
  const effectiveShowProgress = internalShowProgress;
  const effectiveShowCodec = internalShowCodec;
  const effectiveShowFiles = internalShowFiles;

  const [internalSelectedPath, setInternalSelectedPath] = useState<string | undefined>();
  const [loadingPath, setLoadingPath] = useState<string | null>(null);

  // 최종 선택 경로 (외부 > 내부)
  const selectedPath = externalSelectedPath ?? internalSelectedPath;

  // 확장자 목록 조회
  const { data: availableExtensions = [] } = useQuery({
    queryKey: ['available-extensions'],
    queryFn: statsApi.getAvailableExtensions,
    staleTime: 5 * 60 * 1000,
    enabled: enableExtensionFilter,
  });

  // 폴더 트리 데이터 조회
  // staleTime: 30초 동안 캐시된 데이터 사용 (필터 변경 시 딜레이 감소)
  const {
    data: treeData,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['master-folder-tree', initialPath, initialDepth, extensions, showHidden, effectiveShowCodec],
    queryFn: () =>
      progressApi.getTreeWithProgress(
        initialPath,
        initialDepth,
        effectiveShowFiles,
        extensions.length > 0 ? extensions : undefined,
        effectiveShowCodec,
        showHidden
      ),
    staleTime: 30 * 1000, // 30초 캐시
    refetchInterval: enableAutoRefresh ? autoRefreshInterval : false,
  });

  // Lazy Loading: 자식 폴더 로드
  const handleLoadChildren = useCallback(
    async (path: string) => {
      if (!enableLazyLoading) return;
      setLoadingPath(path);
      try {
        const childData = await progressApi.getTreeWithProgress(
          path,
          1,
          effectiveShowFiles,
          extensions.length > 0 ? extensions : undefined,
          effectiveShowCodec,
          showHidden
        );
        // API가 path의 자식 폴더들을 FolderWithProgress[] 배열로 반환함
        // 예: path=WSOP2010 요청 → [Masters] 반환 (WSOP2010의 자식들)
        if (childData && childData.length > 0) {
          queryClient.setQueryData(
            ['master-folder-tree', initialPath, initialDepth, extensions, showHidden, effectiveShowCodec],
            (oldData: FolderWithProgress[] | undefined) => {
              if (!oldData) return oldData;
              return updateFolderChildren(oldData, path, childData);
            }
          );
        }
      } finally {
        setLoadingPath(null);
      }
    },
    [enableLazyLoading, queryClient, initialPath, initialDepth, extensions, showHidden, effectiveShowCodec, effectiveShowFiles]
  );

  // 폴더 선택 핸들러
  const handleFolderSelect = useCallback(
    (folder: FolderWithProgress) => {
      setInternalSelectedPath(folder.path);
      onFolderSelect?.(folder);
    },
    [onFolderSelect]
  );

  // 파일 선택 핸들러
  const handleFileSelect = useCallback(
    (file: FileWithProgress) => {
      setInternalSelectedPath(file.path);
      onFileSelect?.(file);
    },
    [onFileSelect]
  );

  // 표시 옵션 변경 핸들러
  const handleDisplayChange = (key: 'showProgress' | 'showCodec' | 'showFiles', value: boolean) => {
    if (key === 'showProgress') setInternalShowProgress(value);
    if (key === 'showCodec') setInternalShowCodec(value);
    if (key === 'showFiles') setInternalShowFiles(value);
  };

  // 검색 필터 적용
  const filteredTree = useMemo(() => {
    if (!treeData) return [];
    return filterFoldersBySearch(treeData, searchQuery);
  }, [treeData, searchQuery]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-6 h-6 text-gray-400 animate-spin" />
      </div>
    );
  }

  return (
    <div
      data-testid="master-folder-tree"
      className={clsx('bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col', className)}
      style={{ height: height ? (typeof height === 'number' ? `${height}px` : height) : undefined }}
    >
      {/* Compact Filter Bar */}
      {showFilterBar && (
        <CompactFilterBar
          title={filterBarTitle}
          filters={{
            extensions: enableExtensionFilter
              ? {
                  enabled: true,
                  selected: internalExtensions,
                  available: availableExtensions,
                  onChange: setInternalExtensions,
                }
              : undefined,
            hidden: enableHiddenFilter
              ? {
                  enabled: true,
                  show: internalShowHidden,
                  onChange: setInternalShowHidden,
                }
              : undefined,
            display: enableDisplayToggles
              ? {
                  showProgress: internalShowProgress,
                  showCodec: internalShowCodec,
                  showFiles: internalShowFiles,
                  onChange: handleDisplayChange,
                }
              : undefined,
          }}
          onRefresh={() => refetch()}
          searchQuery={enableSearch ? internalSearchQuery : undefined}
          onSearchChange={enableSearch ? setInternalSearchQuery : undefined}
        />
      )}

      {/* Progress Legend (PRD-0049) */}
      {showLegend && (
        <div data-testid="progress-legend" className="px-4 py-2 border-b border-gray-100 bg-gray-50">
          <div className="flex items-center gap-4 text-xs">
            <div data-testid="legend-complete" className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-green-500"></span>
              <span className="text-gray-600">완료 (Complete)</span>
            </div>
            <div data-testid="legend-in-progress" className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-blue-500"></span>
              <span className="text-gray-600">진행 중 (In Progress)</span>
            </div>
            <div data-testid="legend-warning" className="flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-amber-500" />
              <span className="text-gray-600">불일치 (Warning)</span>
            </div>
          </div>
        </div>
      )}

      {/* Tree Content */}
      <div className="flex-1 overflow-y-auto p-2">
        {filteredTree.length > 0 ? (
          filteredTree.map((folder) => (
            <FolderNode
              key={folder.id}
              folder={folder}
              level={0}
              showFiles={effectiveShowFiles}
              showProgressBar={effectiveShowProgress}
              showWorkBadge={showWorkBadge}
              showCodecBadge={effectiveShowCodec}
              selectedPath={selectedPath}
              onFolderSelect={handleFolderSelect}
              onFileSelect={handleFileSelect}
              onLoadChildren={handleLoadChildren}
              isLoadingChildren={loadingPath === folder.path}
              searchQuery={searchQuery}
            />
          ))
        ) : (
          <div className="text-center text-gray-500 py-8">
            {searchQuery ? 'No folders match your search' : 'No folders found'}
          </div>
        )}
      </div>
    </div>
  );
}

// Re-export types
export type { FolderWithProgress, FileWithProgress };
