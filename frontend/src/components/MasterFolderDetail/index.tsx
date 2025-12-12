/**
 * MasterFolderDetail - 통합 폴더 상세 패널
 *
 * mode에 따라 다른 섹션을 렌더링:
 * - progress: 진행률 상세 + 작업 현황 (Dashboard)
 * - codec: 코덱 분포 + 파일 목록 (Statistics)
 * - explorer: 파일 타입 분포 + 하위 폴더 (Folders)
 *
 * PRD: PRD-0033-FOLDER-TREE-UNIFICATION.md Section 6
 */
import { useQuery } from '@tanstack/react-query';
import {
  X,
  Folder,
  Files,
  HardDrive,
  Clock,
  Film,
  Music,
  FileVideo,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Target,
} from 'lucide-react';
import clsx from 'clsx';
import { progressApi } from '../../services/api';
import type { FolderWithProgress, FileWithProgress, WorkStatus } from '../../types';

// ============================================================================
// Types
// ============================================================================

export type DetailMode = 'progress' | 'codec' | 'explorer';

export interface MasterFolderDetailProps {
  folder: FolderWithProgress | null;
  mode: DetailMode;
  onClose?: () => void;
  onFolderSelect?: (folder: FolderWithProgress) => void;
  className?: string;
}

// ============================================================================
// Empty State
// ============================================================================

function EmptyState({ mode }: { mode: DetailMode }) {
  const messages = {
    progress: '폴더를 선택하면 진행률 상세 정보를 확인할 수 있습니다.',
    codec: '폴더를 선택하면 코덱 상세 정보를 확인할 수 있습니다.',
    explorer: '폴더를 선택하면 상세 정보를 확인할 수 있습니다.',
  };

  const icons = {
    progress: <AlertCircle className="w-12 h-12 mx-auto mb-3 text-gray-300" />,
    codec: <Film className="w-12 h-12 mx-auto mb-3 text-gray-300" />,
    explorer: <Folder className="w-12 h-12 mx-auto mb-3 text-gray-300" />,
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center text-gray-500">
      {icons[mode]}
      <p className="text-sm">{messages[mode]}</p>
    </div>
  );
}

// ============================================================================
// Detail Header
// ============================================================================

function DetailHeader({
  folder,
  onClose,
}: {
  folder: FolderWithProgress;
  onClose?: () => void;
}) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-2">
        <Folder className="w-5 h-5 text-yellow-500" />
        <h3 className="text-lg font-semibold text-gray-900 truncate max-w-[250px]">
          {folder.name}
        </h3>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
        >
          <X className="w-5 h-5" />
        </button>
      )}
    </div>
  );
}

// ============================================================================
// Basic Stats
// ============================================================================

function BasicStats({ folder }: { folder: FolderWithProgress }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      <div className="bg-gray-50 rounded-lg p-3">
        <div className="flex items-center gap-1.5 text-gray-500 text-xs mb-1">
          <Files className="w-3.5 h-3.5" />
          Files
        </div>
        <div className="text-lg font-semibold text-gray-900">
          {folder.file_count.toLocaleString()}
        </div>
      </div>
      <div className="bg-gray-50 rounded-lg p-3">
        <div className="flex items-center gap-1.5 text-gray-500 text-xs mb-1">
          <Folder className="w-3.5 h-3.5" />
          Folders
        </div>
        <div className="text-lg font-semibold text-gray-900">
          {folder.folder_count.toLocaleString()}
        </div>
      </div>
      <div className="bg-gray-50 rounded-lg p-3">
        <div className="flex items-center gap-1.5 text-gray-500 text-xs mb-1">
          <HardDrive className="w-3.5 h-3.5" />
          Size
        </div>
        <div className="text-lg font-semibold text-gray-900">{folder.size_formatted}</div>
      </div>
      <div className="bg-gray-50 rounded-lg p-3">
        <div className="flex items-center gap-1.5 text-gray-500 text-xs mb-1">
          <Clock className="w-3.5 h-3.5" />
          Duration
        </div>
        <div className="text-lg font-semibold text-gray-900">
          {folder.duration_formatted || '-'}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Progress Section (Dashboard Mode)
// ============================================================================

function ProgressSection({ folder }: { folder: FolderWithProgress }) {
  const workSummary = folder.work_summary;
  const workStatuses = folder.work_statuses as WorkStatus[] | undefined;

  if (!workSummary && (!workStatuses || workStatuses.length === 0)) {
    return (
      <div className="text-center text-gray-500 py-4">
        <p className="text-sm">이 폴더에 대한 작업 현황이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Work Summary - PRD-0041 Enhanced */}
      {workSummary && (
        <div className={clsx(
          'rounded-lg p-4',
          workSummary.is_complete ? 'bg-green-50' : 'bg-blue-50'
        )}>
          <div className="flex items-center justify-between mb-2">
            <h4 className={clsx(
              'font-medium',
              workSummary.is_complete ? 'text-green-900' : 'text-blue-900'
            )}>
              작업 진행률
              {workSummary.is_complete && (
                <span className="ml-2 inline-flex items-center gap-1 text-green-600">
                  <CheckCircle2 className="w-4 h-4" />
                  완료
                </span>
              )}
            </h4>
            {/* Matching Info Badge */}
            {workSummary.matching_method && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-gray-200 text-gray-700">
                <Target className="w-3 h-3" />
                {workSummary.matching_method}
                {workSummary.matching_score !== undefined && (
                  <span className="text-gray-500">
                    ({(workSummary.matching_score * 100).toFixed(0)}%)
                  </span>
                )}
              </span>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className={clsx(
                'h-3 rounded-full overflow-hidden',
                workSummary.is_complete ? 'bg-green-200' : 'bg-blue-200'
              )}>
                <div
                  className={clsx(
                    'h-full rounded-full transition-all',
                    workSummary.is_complete ? 'bg-green-500'
                      : workSummary.combined_progress >= 100 ? 'bg-emerald-500'
                      : 'bg-blue-500'
                  )}
                  style={{ width: `${Math.min(workSummary.combined_progress, 100)}%` }}
                />
              </div>
            </div>
            <span className={clsx(
              'text-lg font-semibold',
              workSummary.is_complete ? 'text-green-900' : 'text-blue-900'
            )}>
              {workSummary.combined_progress.toFixed(0)}%
            </span>
          </div>
          <div className={clsx(
            'mt-2 text-sm',
            workSummary.is_complete ? 'text-green-700' : 'text-blue-700'
          )}>
            완료: {workSummary.total_done} / 전체: {workSummary.total_files}
          </div>

          {/* PRD-0041: Data Source Mismatch Warning */}
          {workSummary.data_source_mismatch && (
            <div className="mt-3 flex items-start gap-2 p-2 rounded bg-amber-100 text-amber-800 text-sm">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-medium">데이터 불일치 감지</span>
                <p className="text-amber-700 text-xs mt-0.5">
                  Google Sheets: {workSummary.sheets_total_videos}개 /
                  NAS: {workSummary.total_files}개
                  (차이: {workSummary.mismatch_count || 0}개)
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Work Status List */}
      {workStatuses && workStatuses.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-900 mb-2">Google Sheets 원본 데이터</h4>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {workStatuses.map((status, index) => (
              <div
                key={status.id || index}
                className="flex items-center justify-between bg-gray-50 rounded-lg p-3"
              >
                <div className="flex items-center gap-2">
                  {status.excel_done === status.total_videos ? (
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-yellow-500" />
                  )}
                  <span className="text-sm font-medium truncate max-w-[180px]">
                    {status.category}
                  </span>
                </div>
                <span className="text-sm text-gray-600">
                  {status.excel_done}/{status.total_videos}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Codec Section (Statistics Mode)
// ============================================================================

function CodecSection({ folder }: { folder: FolderWithProgress }) {
  const codecSummary = folder.codec_summary;

  // 폴더 상세 정보 (파일 목록 포함)
  const { data: folderDetail } = useQuery({
    queryKey: ['folder-detail-codec', folder.path],
    queryFn: () => progressApi.getFolderDetail(folder.path, true),
    staleTime: 30 * 1000,
  });

  const files = folderDetail?.files || folder.files || [];

  return (
    <div className="space-y-4">
      {/* Codec Distribution */}
      {codecSummary && codecSummary.video_codecs && (
        <div>
          <h4 className="font-medium text-gray-900 mb-2">비디오 코덱 분포</h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(codecSummary.video_codecs)
              .sort(([, a], [, b]) => (b as number) - (a as number))
              .map(([codec, count]) => (
                <span
                  key={codec}
                  className="inline-flex items-center gap-1 px-2 py-1 text-sm rounded-lg bg-blue-100 text-blue-700"
                >
                  <Film className="w-3.5 h-3.5" />
                  {codec}: {count as number}
                </span>
              ))}
          </div>
        </div>
      )}

      {codecSummary && codecSummary.audio_codecs && (
        <div>
          <h4 className="font-medium text-gray-900 mb-2">오디오 코덱 분포</h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(codecSummary.audio_codecs)
              .sort(([, a], [, b]) => (b as number) - (a as number))
              .map(([codec, count]) => (
                <span
                  key={codec}
                  className="inline-flex items-center gap-1 px-2 py-1 text-sm rounded-lg bg-green-100 text-green-700"
                >
                  <Music className="w-3.5 h-3.5" />
                  {codec}: {count as number}
                </span>
              ))}
          </div>
        </div>
      )}

      {/* File List with Codec Info */}
      {files.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-900 mb-2">
            파일 목록 ({files.length}개)
          </h4>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {files.slice(0, 20).map((file: FileWithProgress) => (
              <div
                key={file.id}
                className="flex items-center gap-2 bg-gray-50 rounded-lg p-2 text-sm"
              >
                <FileVideo className="w-4 h-4 text-purple-400 flex-shrink-0" />
                <span className="truncate flex-1">{file.name}</span>
                {file.video_codec && (
                  <span className="px-1.5 py-0.5 text-xs rounded bg-blue-50 text-blue-600">
                    {file.video_codec}
                  </span>
                )}
              </div>
            ))}
            {files.length > 20 && (
              <div className="text-center text-gray-500 text-sm py-2">
                +{files.length - 20}개 더...
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Explorer Section (Folders Mode)
// ============================================================================

function ExplorerSection({
  folder,
  onFolderSelect,
}: {
  folder: FolderWithProgress;
  onFolderSelect?: (folder: FolderWithProgress) => void;
}) {
  const children = folder.children || [];

  return (
    <div className="space-y-4">
      {/* Path */}
      <div className="text-sm text-gray-500 break-all bg-gray-50 rounded-lg p-3">
        {folder.path}
      </div>

      {/* Subfolders */}
      {children.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-900 mb-2">
            하위 폴더 ({children.length}개)
          </h4>
          <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
            {children.slice(0, 10).map((child) => (
              <button
                key={child.id}
                onClick={() => onFolderSelect?.(child)}
                className="flex items-center gap-2 bg-gray-50 rounded-lg p-2 text-left hover:bg-gray-100 transition-colors"
              >
                <Folder className="w-4 h-4 text-yellow-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{child.name}</div>
                  <div className="text-xs text-gray-500">{child.size_formatted}</div>
                </div>
              </button>
            ))}
          </div>
          {children.length > 10 && (
            <div className="text-center text-gray-500 text-sm py-2">
              +{children.length - 10}개 더...
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function MasterFolderDetail({
  folder,
  mode,
  onClose,
  onFolderSelect,
  className,
}: MasterFolderDetailProps) {
  if (!folder) {
    return <EmptyState mode={mode} />;
  }

  return (
    <div
      className={clsx(
        'bg-white rounded-xl shadow-sm border border-gray-100 p-6',
        className
      )}
    >
      {/* Header */}
      <DetailHeader folder={folder} onClose={onClose} />

      {/* Basic Stats */}
      <BasicStats folder={folder} />

      {/* Mode-specific Content */}
      {mode === 'progress' && <ProgressSection folder={folder} />}
      {mode === 'codec' && <CodecSection folder={folder} />}
      {mode === 'explorer' && <ExplorerSection folder={folder} onFolderSelect={onFolderSelect} />}
    </div>
  );
}

// Re-export types
export type { FolderWithProgress };
