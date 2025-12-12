/**
 * FolderTreeWithProgress - 폴더 트리 + 진행률 통합 컴포넌트
 *
 * Gantt-chart 스타일로 폴더/파일별 진행률을 시각화.
 * - metadata db: 채워진 바 (보라색)
 * - archive db: 세로 마커선 (파란색)
 *
 * displayMode:
 * - 'progress': 작업 진행률 표시 (기본값)
 * - 'codec': 코덱 정보 표시 (Codec Explorer용)
 *
 * === BLOCK INDEX ===
 * | Block ID              | Lines       | Description              |
 * |-----------------------|-------------|--------------------------|
 * | tree.types            | 44-79       | 타입 정의 (Props)        |
 * | tree.helpers          | 81-154      | getWorkSummary 등 헬퍼   |
 * | tree.file_node        | 156-237     | FileNode 컴포넌트        |
 * | tree.folder_node      | 239-444     | FolderNode 컴포넌트      |
 * | tree.legend           | 446-490     | ProgressLegend 컴포넌트  |
 * | tree.main             | 492-658     | 메인 컴포넌트 (export)   |
 * | tree.detail_panel     | 660-916     | FolderProgressDetail     |
 * ====================
 *
 * Block: components.folder-tree-progress
 */
import { useState, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  FileVideo,
  RefreshCw,
  AlertCircle,
  Film,
  Music,
} from 'lucide-react';
import clsx from 'clsx';
import { progressApi } from '../services/api';
import ProgressBar from './ProgressBar';
import type { FolderWithProgress, FileWithProgress, WorkSummary, FolderCodecSummary } from '../types';

// === BLOCK: tree.types ===
// Description: Props 및 내부 타입 정의
// Dependencies: ../types (FolderWithProgress, FileWithProgress, WorkSummary, FolderCodecSummary)
// AI Context: 컴포넌트 구조 이해 시 이 블록만 읽으면 됨

/** 표시 모드: progress(작업 진행률) 또는 codec(코덱 정보) */
type DisplayMode = 'progress' | 'codec';

interface FolderTreeWithProgressProps {
  initialPath?: string;
  initialDepth?: number;
  showFiles?: boolean;
  selectedExtensions?: string[];
  /** 표시 모드: 'progress' (기본) 또는 'codec' */
  displayMode?: DisplayMode;
  /** Lazy Loading 활성화 (폴더 클릭 시 자식 동적 로드) */
  enableLazyLoading?: boolean;
  /** 숨김 파일 표시 여부 (외부에서 제어) */
  showHiddenFiles?: boolean;
  onFolderSelect?: (folder: FolderWithProgress) => void;
  onFileSelect?: (file: FileWithProgress) => void;
}

interface FolderNodeProps {
  folder: FolderWithProgress;
  level: number;
  showFiles: boolean;
  selectedPath?: string;
  displayMode: DisplayMode;
  onFolderSelect?: (folder: FolderWithProgress) => void;
  onFileSelect?: (file: FileWithProgress) => void;
  onLoadChildren?: (path: string) => void;
  isLoadingChildren?: boolean;
}

interface FileNodeProps {
  file: FileWithProgress;
  level: number;
  selectedPath?: string;
  displayMode: DisplayMode;
  onSelect?: (file: FileWithProgress) => void;
}
// === END BLOCK: tree.types ===

// === BLOCK: tree.helpers ===
// Description: getWorkSummary, updateFolderChildren 등 유틸리티 함수
// Dependencies: FolderWithProgress, WorkSummary types
// AI Context: work_summary 계산 로직 디버깅 시 이 블록 참조

// 디버깅 플래그 (콘솔 로그 활성화)
const DEBUG_WORK_SUMMARY = true;

/**
 * 폴더의 작업 진행률 (work_summary 기반)
 * - 담당자가 입력한 엑셀 작업 현황만 표시
 * - 하이어라키 합산: task_count=0이어도 total_done이 있으면 표시
 */
function getWorkSummary(folder: FolderWithProgress): WorkSummary | null {
  // 타입에서 직접 접근 (더 이상 any 캐스팅 불필요)
  const summary = folder.work_summary;

  // 디버깅 로그: 폴더별 work_summary 상태 추적
  if (DEBUG_WORK_SUMMARY && folder.depth <= 2) {
    console.log(`[getWorkSummary] 폴더: ${folder.name}`, {
      depth: folder.depth,
      path: folder.path,
      hasWorkSummary: !!summary,
      summary: summary ? {
        task_count: summary.task_count,
        total_files: summary.total_files,
        total_done: summary.total_done,
        combined_progress: summary.combined_progress,
      } : null,
      childrenCount: folder.children?.length || 0,
    });
  }

  // null/undefined 체크
  if (!summary) {
    if (DEBUG_WORK_SUMMARY && folder.depth <= 2) {
      console.warn(`[getWorkSummary] ⚠️ ${folder.name}: work_summary가 없음!`);
    }
    return null;
  }

  // 모든 값이 0이면 표시하지 않음
  if (summary.task_count === 0 && summary.total_done === 0 && summary.total_files === 0) {
    if (DEBUG_WORK_SUMMARY && folder.depth <= 2) {
      console.log(`[getWorkSummary] ${folder.name}: 모든 값이 0이므로 null 반환`);
    }
    return null;
  }

  return summary;
}

// Note: calculateFolderMetadataProgress, calculateFolderArchiveProgress 함수 제거됨
// work_summary 기반으로 단순화됨

/**
 * 폴더 트리에서 특정 경로의 자식을 업데이트하는 헬퍼 함수
 * Lazy Loading에서 동적으로 로드된 자식을 기존 트리에 병합
 */
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
// === END BLOCK: tree.helpers ===

// === BLOCK: tree.file_node ===
// Description: 파일 노드 렌더링 컴포넌트
// Dependencies: FileWithProgress, DisplayMode, ProgressBar
// AI Context: 파일 표시 UI 수정 시 이 블록만 수정

function FileNode({ file, level, selectedPath, displayMode, onSelect }: FileNodeProps) {
  const isSelected = selectedPath === file.path;
  const hasProgress = file.metadata_progress && file.metadata_progress.hand_count > 0;
  const isCodecMode = displayMode === 'codec';

  return (
    <div
      className={clsx(
        'flex items-center py-1.5 px-2 cursor-pointer rounded transition-colors',
        isSelected ? 'bg-purple-50 text-purple-700' : 'hover:bg-gray-50'
      )}
      style={{ paddingLeft: `${level * 16 + 8}px` }}
      onClick={() => onSelect?.(file)}
    >
      {/* Spacer for alignment */}
      <span className="w-5 h-5 flex items-center justify-center mr-1">
        <span className="w-4" />
      </span>

      {/* File Icon */}
      <FileVideo className="w-4 h-4 text-purple-400 mr-2 flex-shrink-0" />

      {/* File Name */}
      <span className="text-xs font-medium truncate max-w-[180px]" title={file.name}>
        {file.name}
      </span>

      {/* Issue #29: 파일 메타데이터 (용량 · 코덱 · 재생시간) - 항상 표시 */}
      <div className="flex items-center gap-2 ml-2 flex-shrink-0 text-xs">
        {/* 용량 */}
        <span className="text-gray-500 font-mono" title="파일 용량">
          {file.size_formatted}
        </span>

        {/* 구분자 */}
        <span className="text-gray-300">·</span>

        {/* 코덱 (비디오/오디오) */}
        <div className="flex items-center gap-1">
          {file.video_codec ? (
            <span className="inline-flex items-center px-1 py-0.5 rounded bg-blue-50 text-blue-600" title="비디오 코덱">
              <Film className="w-3 h-3 mr-0.5" />
              {file.video_codec}
            </span>
          ) : (
            <span className="text-gray-300" title="비디오 코덱 없음">-</span>
          )}
          {file.audio_codec && (
            <span className="inline-flex items-center px-1 py-0.5 rounded bg-green-50 text-green-600" title="오디오 코덱">
              <Music className="w-3 h-3 mr-0.5" />
              {file.audio_codec}
            </span>
          )}
        </div>

        {/* 구분자 */}
        <span className="text-gray-300">·</span>

        {/* 재생 시간 */}
        <span className="text-gray-500 font-mono" title="재생 시간">
          {file.duration_formatted}
        </span>
      </div>

      {/* Progress Mode: Show progress bar */}
      {!isCodecMode && hasProgress && file.metadata_progress && (
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
// === END BLOCK: tree.file_node ===

// === BLOCK: tree.folder_node ===
// Description: 폴더 노드 렌더링 컴포넌트 (재귀적)
// Dependencies: FolderWithProgress, DisplayMode, ProgressBar, FileNode, getWorkSummary
// AI Context: 폴더 트리 UI 및 Lazy Loading 수정 시 이 블록 참조

function FolderNode({
  folder,
  level,
  showFiles,
  selectedPath,
  displayMode,
  onFolderSelect,
  onFileSelect,
  onLoadChildren,
  isLoadingChildren,
}: FolderNodeProps) {
  const [isOpen, setIsOpen] = useState(level < 1);
  const hasChildren = folder.children && folder.children.length > 0;
  const hasFiles = showFiles && folder.files && folder.files.length > 0;
  const isSelected = selectedPath === folder.path;
  const isCodecMode = displayMode === 'codec';

  // 작업 진행률 요약 (work_summary) - progress 모드에서만 사용
  const workSummary = !isCodecMode ? getWorkSummary(folder) : null;

  // 코덱 요약 (codec_summary) - codec 모드에서만 사용
  const codecSummary = folder.codec_summary as FolderCodecSummary | null | undefined;

  // 폴더에 자식이 있을 수 있는지 (folder_count > 0)
  const mayHaveChildren = folder.folder_count > 0;

  const handleClick = () => {
    const willOpen = !isOpen;

    // Lazy Loading: 자식이 없지만 있을 수 있는 경우 로드 요청
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

        {/* Issue #29: NAS 데이터 (파일 수/전체, 용량/전체) */}
        <span className="text-xs text-gray-500 ml-2 flex-shrink-0 font-mono" title="NAS 데이터">
          {folder.root_stats ? (
            <>
              <span className="text-blue-600">({folder.file_count}/{folder.root_stats.total_files})</span>
              <span className="text-gray-400 mx-0.5">·</span>
              <span className="text-purple-600">({folder.size_formatted}/{folder.root_stats.total_size_formatted})</span>
            </>
          ) : (
            // root_stats가 없으면 기존 표시 유지
            <>{folder.file_count}개 · {folder.size_formatted}</>
          )}
        </span>

        {/* Issue #29: 구분자 */}
        {!isCodecMode && folder.root_stats && (
          <span className="text-gray-300 mx-1 flex-shrink-0">|</span>
        )}

        {/* Codec Mode: Show codec summary */}
        {isCodecMode && (
          <div className="flex items-center gap-2 ml-3 flex-shrink-0">
            {codecSummary?.top_video_codec && (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-blue-100 text-blue-700">
                <Film className="w-3 h-3 mr-0.5" />
                {codecSummary.top_video_codec}
              </span>
            )}
            {codecSummary?.top_audio_codec && (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-green-100 text-green-700">
                <Music className="w-3 h-3 mr-0.5" />
                {codecSummary.top_audio_codec}
              </span>
            )}
            {codecSummary && (
              <span className="text-xs text-gray-400">
                ({codecSummary.files_with_codec}/{codecSummary.total_files})
              </span>
            )}
            {!codecSummary && (
              <span className="text-xs text-gray-300">코덱 정보 없음</span>
            )}
          </div>
        )}

        {/* Progress Mode: Progress Bar */}
        {!isCodecMode && (
          <>
            <div className="flex-1 max-w-[150px] ml-3">
              {workSummary ? (
                <ProgressBar
                  metadataProgress={workSummary.combined_progress}
                  isComplete={workSummary.combined_progress >= 100}
                  size="sm"
                  showLabel={false}
                  showPercentage={false}
                />
              ) : (
                /* 작업 없는 폴더: 회색 빈 프로그레스바 */
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div className="h-1.5 rounded-full bg-gray-300 w-0" />
                </div>
              )}
            </div>

            {/* Progress Text */}
            <div className="flex items-center gap-1 ml-2 flex-shrink-0 text-xs min-w-[100px]">
              {workSummary ? (
                <>
                  <span className={clsx(
                    workSummary.combined_progress >= 100 ? 'text-green-600 font-medium' : 'text-blue-600'
                  )}>
                    {workSummary.combined_progress.toFixed(0)}%
                  </span>
                  <span className="text-gray-400">
                    ({workSummary.total_done}/{workSummary.total_files})
                  </span>
                  {/* 시트 원본값 표시 */}
                  <span
                    className="text-orange-500 ml-1 cursor-help"
                    title={`📊 시트: ${workSummary.sheets_excel_done}/${workSummary.sheets_total_videos}`}
                  >
                    📊
                  </span>
                </>
              ) : (
                <span className="text-gray-300">-</span>
              )}
            </div>
          </>
        )}
      </div>

      {/* Children Folders */}
      {hasChildren && isOpen && (
        <div>
          {folder.children.map((child) => (
            <FolderNode
              key={child.id}
              folder={child}
              level={level + 1}
              showFiles={showFiles}
              selectedPath={selectedPath}
              displayMode={displayMode}
              onFolderSelect={onFolderSelect}
              onFileSelect={onFileSelect}
              onLoadChildren={onLoadChildren}
            />
          ))}
        </div>
      )}

      {/* Loading indicator for lazy loading */}
      {isOpen && !hasChildren && mayHaveChildren && isLoadingChildren && (
        <div className="flex items-center py-2" style={{ paddingLeft: `${(level + 1) * 16 + 8}px` }}>
          <RefreshCw className="w-4 h-4 text-gray-400 animate-spin mr-2" />
          <span className="text-xs text-gray-400">로딩 중...</span>
        </div>
      )}

      {/* Files */}
      {hasFiles && isOpen && folder.files && (
        <div>
          {folder.files.map((file) => (
            <FileNode
              key={file.id}
              file={file}
              level={level + 1}
              selectedPath={selectedPath}
              displayMode={displayMode}
              onSelect={onFileSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}
// === END BLOCK: tree.folder_node ===

// === BLOCK: tree.legend ===
// Description: 범례 컴포넌트 (Progress/Codec 모드별)
// Dependencies: DisplayMode
// AI Context: 범례 UI 수정 시 이 블록만 수정

function ProgressLegend({ displayMode }: { displayMode: DisplayMode }) {
  if (displayMode === 'codec') {
    return (
      <div className="flex items-center gap-4 text-xs text-gray-500 px-4 py-2 bg-gray-50 border-b border-gray-100">
        <div className="flex items-center gap-1">
          <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">
            <Film className="w-3 h-3 mr-0.5" />
            Video
          </span>
          <span>비디오 코덱</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-green-100 text-green-700">
            <Music className="w-3 h-3 mr-0.5" />
            Audio
          </span>
          <span>오디오 코덱</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-gray-400">(N/M)</span>
          <span>코덱 정보 있는 파일 수</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-4 text-xs text-gray-500 px-4 py-2 bg-gray-50 border-b border-gray-100">
      {/* Issue #29: NAS/Sheets 데이터 분리 범례 */}
      <div className="flex items-center gap-1">
        <span className="text-blue-600 font-mono">(N/T)</span>
        <span>NAS 파일</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="text-purple-600 font-mono">(N/T)</span>
        <span>용량</span>
      </div>
      <div className="flex items-center gap-0.5 text-gray-300">|</div>
      <div className="flex items-center gap-1">
        <div className="w-4 h-1.5 bg-blue-500 rounded-full" />
        <span>Sheets 진행률</span>
      </div>
      <div className="flex items-center gap-1">
        <div className="w-4 h-1.5 bg-green-500 rounded-full" />
        <span>완료</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="text-orange-500">📊</span>
        <span>시트 원본</span>
      </div>
    </div>
  );
}
// === END BLOCK: tree.legend ===

// === BLOCK: tree.main ===
// Description: 메인 FolderTreeWithProgress export 컴포넌트
// Dependencies: progressApi, useQuery, FolderNode, ProgressLegend
// AI Context: API 호출, 상태관리, Lazy Loading 로직 수정 시 참조

export default function FolderTreeWithProgress({
  initialPath,
  initialDepth = 2,
  showFiles = false,
  selectedExtensions,
  displayMode = 'progress',
  enableLazyLoading = false,
  showHiddenFiles = false,
  onFolderSelect,
  onFileSelect,
}: FolderTreeWithProgressProps) {
  const [selectedPath, setSelectedPath] = useState<string | undefined>();
  const [loadingPaths, setLoadingPaths] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();

  const isCodecMode = displayMode === 'codec';

  // include_codecs 파라미터 추가 (codec 모드일 때)
  const {
    data: folders,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['folder-tree-progress', initialPath, initialDepth, showFiles, selectedExtensions, displayMode, showHiddenFiles],
    queryFn: () => progressApi.getTreeWithProgress(
      initialPath,
      initialDepth,
      showFiles,
      selectedExtensions,
      isCodecMode,  // include_codecs
      showHiddenFiles // include_hidden
    ),
    refetchInterval: 60000, // 60초마다 자동 갱신
    staleTime: 30000,
  });

  // Lazy Loading: 폴더 자식 로드
  const handleLoadChildren = useCallback(async (path: string) => {
    if (!enableLazyLoading || loadingPaths.has(path)) return;

    setLoadingPaths(prev => new Set(prev).add(path));

    try {
      const children = await progressApi.getTreeWithProgress(
        path,
        2, // 하위 2단계
        showFiles,
        selectedExtensions,
        isCodecMode,
        showHiddenFiles // include_hidden
      );

      // 캐시 업데이트
      queryClient.setQueryData(
        ['folder-tree-progress', initialPath, initialDepth, showFiles, selectedExtensions, displayMode, showHiddenFiles],
        (old: FolderWithProgress[] | undefined) => {
          if (!old) return old;
          return updateFolderChildren(old, path, children);
        }
      );
    } catch (err) {
      console.error('Failed to load children:', err);
    } finally {
      setLoadingPaths(prev => {
        const next = new Set(prev);
        next.delete(path);
        return next;
      });
    }
  }, [enableLazyLoading, loadingPaths, showFiles, selectedExtensions, isCodecMode, showHiddenFiles, queryClient, initialPath, initialDepth, displayMode]);

  const handleFolderSelect = useCallback(
    (folder: FolderWithProgress) => {
      setSelectedPath(folder.path);
      onFolderSelect?.(folder);
    },
    [onFolderSelect]
  );

  const handleFileSelect = useCallback(
    (file: FileWithProgress) => {
      setSelectedPath(file.path);
      onFileSelect?.(file);
    },
    [onFileSelect]
  );

  // 제목 (모드에 따라 변경)
  const title = isCodecMode ? 'Codec Explorer' : 'Progress Overview';

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-100 flex items-center justify-between flex-shrink-0">
        <h3 className="font-semibold text-gray-900">{title}</h3>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className={clsx(
            'p-1.5 rounded-md transition-colors',
            isFetching
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'hover:bg-gray-100 text-gray-500'
          )}
          title="새로고침"
        >
          <RefreshCw className={clsx('w-4 h-4', isFetching && 'animate-spin')} />
        </button>
      </div>

      {/* Legend */}
      <ProgressLegend displayMode={displayMode} />

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-12 text-red-500">
            <AlertCircle className="w-6 h-6 mb-2" />
            <span className="text-sm">데이터를 불러오는데 실패했습니다</span>
          </div>
        ) : !folders || folders.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p className="text-sm">폴더가 없습니다.</p>
            <p className="text-xs mt-1">스캔을 실행하여 데이터를 수집하세요.</p>
          </div>
        ) : (
          <div className="p-2">
            {/* 디버깅: API 응답 데이터 로그 (useEffect로 이동 권장) */}
            {(() => {
              if (DEBUG_WORK_SUMMARY) {
                console.log('[FolderTreeWithProgress] API 응답:', {
                  folderCount: folders.length,
                  folders: folders.map(f => ({
                    name: f.name,
                    hasWorkSummary: !!f.work_summary,
                    workSummary: f.work_summary,
                    childrenCount: f.children?.length || 0,
                  })),
                });
              }
              return null;
            })()}
            {folders.map((folder) => (
              <FolderNode
                key={folder.id}
                folder={folder}
                level={0}
                showFiles={showFiles}
                selectedPath={selectedPath}
                displayMode={displayMode}
                onFolderSelect={handleFolderSelect}
                onFileSelect={handleFileSelect}
                onLoadChildren={enableLazyLoading ? handleLoadChildren : undefined}
                isLoadingChildren={loadingPaths.has(folder.path)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
// === END BLOCK: tree.main ===

// === BLOCK: tree.detail_panel ===
// Description: 선택된 폴더의 상세 진행률 패널
// Dependencies: progressApi, getWorkSummary, FileWithProgress
// AI Context: 상세 패널 UI 및 데이터 표시 수정 시 참조

/**
 * FolderProgressDetail - 단일 폴더 상세 진행률
 *
 * 특정 폴더의 상세 진행률을 표시 (파일 목록 포함)
 */
interface FolderProgressDetailProps {
  folderPath: string;
  onFileSelect?: (file: FileWithProgress) => void;
}

export function FolderProgressDetail({
  folderPath,
  onFileSelect,
}: FolderProgressDetailProps) {
  const { data: folder, isLoading, error } = useQuery({
    queryKey: ['folder-progress-detail', folderPath],
    queryFn: () => progressApi.getFolderDetail(folderPath, true),
    enabled: !!folderPath,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <RefreshCw className="w-5 h-5 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error || !folder) {
    return (
      <div className="text-center py-8 text-gray-500 text-sm">
        폴더 정보를 불러올 수 없습니다.
      </div>
    );
  }

  // work_summary 또는 work_statuses 가져오기
  const workSummary = getWorkSummary(folder);
  const workStatuses = (folder as any).work_statuses as Array<{
    id: number;
    category: string;
    pic?: string;
    status: string;
    total_videos: number;
    excel_done: number;
    progress_percent: number;
    notes1?: string;
    notes2?: string;
  }> | undefined;

  // 디버깅 로그
  console.log('[FolderProgressDetail] Debug Info:', {
    folderPath,
    folderName: folder.name,
    hasFolder: !!folder,
    workSummary,
    workStatusesCount: workStatuses?.length || 0,
    workStatuses,
  });

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      {/* Header */}
      <div className="mb-4">
        <h4 className="font-semibold text-gray-900 truncate">{folder.name}</h4>
        <p className="text-xs text-gray-500 truncate">{folder.path}</p>
      </div>

      {/* 데이터 비교 테이블 */}
      <div className="mb-4">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-1.5 text-gray-500 font-medium">구분</th>
              <th className="text-right py-1.5 text-gray-500 font-medium">값</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-gray-100">
              <td className="py-1.5 text-gray-600">📁 NAS 파일 수</td>
              <td className="py-1.5 text-right font-mono font-medium">{folder.file_count}</td>
            </tr>
            {workSummary && (
              <>
                <tr className="border-b border-gray-100 bg-blue-50">
                  <td className="py-1.5 text-blue-700">📊 시트 전체 (total_videos)</td>
                  <td className="py-1.5 text-right font-mono font-medium text-blue-700">
                    {workSummary.sheets_total_videos}
                  </td>
                </tr>
                <tr className="border-b border-gray-100 bg-green-50">
                  <td className="py-1.5 text-green-700">✅ 시트 완료 (excel_done)</td>
                  <td className="py-1.5 text-right font-mono font-medium text-green-700">
                    {workSummary.sheets_excel_done}
                  </td>
                </tr>
                <tr className="bg-gray-50">
                  <td className="py-1.5 text-gray-700 font-medium">📈 진행률 (시트 기준)</td>
                  <td className="py-1.5 text-right font-mono font-medium">
                    <span className={clsx(
                      (workSummary as any).actual_progress >= 100 ? 'text-green-600' : 'text-blue-600'
                    )}>
                      {((workSummary as any).actual_progress || workSummary.combined_progress).toFixed(1)}%
                    </span>
                  </td>
                </tr>
                {/* 데이터 불일치 경고 */}
                {(workSummary as any).data_source_mismatch && (
                  <tr className="bg-orange-50">
                    <td className="py-1.5 text-orange-700 font-medium">⚠️ 데이터 불일치</td>
                    <td className="py-1.5 text-right font-mono font-medium text-orange-700">
                      {(workSummary as any).mismatch_count > 0 ? '+' : ''}{(workSummary as any).mismatch_count}
                      <span className="text-xs ml-1">
                        ({(workSummary as any).mismatch_count > 0 ? '시트 > NAS' : 'NAS > 시트'})
                      </span>
                    </td>
                  </tr>
                )}
              </>
            )}
          </tbody>
        </table>

        {/* Progress Bar */}
        {workSummary && (
          <div className="mt-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={clsx(
                  'h-2 rounded-full transition-all duration-300',
                  ((workSummary as any).actual_progress || workSummary.combined_progress) >= 100 ? 'bg-green-500' : 'bg-blue-500'
                )}
                style={{ width: `${Math.min((workSummary as any).actual_progress || workSummary.combined_progress, 100)}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-2 mb-4 text-xs">
        <div className="bg-gray-50 p-2 rounded">
          <span className="text-gray-500">파일 수</span>
          <span className="float-right font-medium">{folder.file_count}</span>
        </div>
        <div className="bg-gray-50 p-2 rounded">
          <span className="text-gray-500">용량</span>
          <span className="float-right font-medium">{folder.size_formatted}</span>
        </div>
      </div>

      {/* 📊 구글 시트 원본 데이터 (전체 행) */}
      {workStatuses && workStatuses.length > 0 && (
        <div className="mb-4">
          <h5 className="text-xs font-medium text-blue-600 mb-2 flex items-center gap-1">
            📊 Google Sheets 원본 데이터 ({workStatuses.length}행)
          </h5>
          <div className="space-y-3">
            {workStatuses.map((ws) => (
              <div key={ws.id} className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs">
                {/* 헤더: Category + Status */}
                <div className="flex justify-between items-center mb-2 pb-2 border-b border-blue-200">
                  <span className="font-semibold text-blue-800">{ws.category}</span>
                  <span className={clsx(
                    'px-2 py-0.5 rounded text-xs font-medium',
                    ws.status === 'completed' || ws.status === '완료' ? 'bg-green-100 text-green-700' :
                    ws.status === 'in_progress' || ws.status === '작업 중' ? 'bg-yellow-100 text-yellow-700' :
                    ws.status === '검토' ? 'bg-purple-100 text-purple-700' :
                    'bg-gray-100 text-gray-600'
                  )}>
                    {ws.status}
                  </span>
                </div>

                {/* 데이터 테이블 */}
                <table className="w-full text-xs">
                  <tbody>
                    <tr>
                      <td className="py-1 text-gray-500 w-24">PIC (담당자)</td>
                      <td className="py-1 font-medium text-gray-700">{ws.pic || '-'}</td>
                    </tr>
                    <tr>
                      <td className="py-1 text-gray-500">Total</td>
                      <td className="py-1 font-mono font-medium text-blue-700">{ws.total_videos}</td>
                    </tr>
                    <tr>
                      <td className="py-1 text-gray-500">Excel Done</td>
                      <td className="py-1 font-mono font-medium text-green-700">{ws.excel_done}</td>
                    </tr>
                    <tr>
                      <td className="py-1 text-gray-500">Progress</td>
                      <td className="py-1 font-mono font-medium">
                        <span className={ws.progress_percent >= 100 ? 'text-green-600' : 'text-blue-600'}>
                          {ws.progress_percent.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                    {ws.notes1 && (
                      <tr>
                        <td className="py-1 text-gray-500">Notes 1</td>
                        <td className="py-1 text-gray-600 break-words">{ws.notes1}</td>
                      </tr>
                    )}
                    {ws.notes2 && (
                      <tr>
                        <td className="py-1 text-gray-500">Notes 2</td>
                        <td className="py-1 text-gray-600 break-words">{ws.notes2}</td>
                      </tr>
                    )}
                  </tbody>
                </table>

                {/* Mini Progress Bar */}
                <div className="w-full bg-blue-200 rounded-full h-1.5 mt-2">
                  <div
                    className={clsx(
                      'h-1.5 rounded-full transition-all',
                      ws.progress_percent >= 100 ? 'bg-green-500' : 'bg-blue-500'
                    )}
                    style={{ width: `${Math.min(ws.progress_percent, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No work status message */}
      {(!workStatuses || workStatuses.length === 0) && !workSummary && (
        <div className="text-center py-4 text-gray-400 text-xs">
          이 폴더에 등록된 작업이 없습니다.
        </div>
      )}

      {/* Files */}
      {folder.files && folder.files.length > 0 && (
        <div>
          <h5 className="text-xs font-medium text-gray-500 mb-2">파일 목록 ({folder.files.length})</h5>
          <div className="max-h-[200px] overflow-y-auto space-y-1">
            {folder.files.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-2 p-1.5 rounded hover:bg-gray-50 cursor-pointer text-xs"
                onClick={() => onFileSelect?.(file)}
              >
                <FileVideo className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                <span className="truncate flex-1">{file.name}</span>
                <span className="text-gray-400 flex-shrink-0">{file.duration_formatted}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
// === END BLOCK: tree.detail_panel ===
