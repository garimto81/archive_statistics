/**
 * Dashboard - 메인 대시보드 페이지
 *
 * 아카이브 통계 요약 및 데이터 소스 현황을 한눈에 보여주는 대시보드.
 * Phase 2: Gantt-chart 스타일 폴더 트리 + 진행률 통합
 * Phase 3: 확장자 필터 GUI 추가 (Issue #7)
 *
 * Layout:
 * - Extension Filter: 파일 확장자 필터 (다중 선택)
 * - Stats Cards: 전체 파일 수, 용량, 미디어 재생시간, 파일 타입 수
 * - Left: Progress Overview (폴더 트리 + 진행률)
 * - Right: Folder Detail, Data Source Status
 *
 * Block: pages.dashboard
 */
import { useState, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Files, HardDrive, Clock, FileType } from 'lucide-react';
import StatCard from '../components/StatCard';
import FolderTreeWithProgress, {
  FolderProgressDetail,
} from '../components/FolderTreeWithProgress';
import DataSourceStatus from '../components/DataSourceStatus';
import ExtensionFilter from '../components/ExtensionFilter';
import { statsApi, progressApi } from '../services/api';
import type { FolderWithProgress, FileWithProgress } from '../types';

export default function Dashboard() {
  const [selectedFolder, setSelectedFolder] = useState<FolderWithProgress | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileWithProgress | null>(null);
  const [selectedExtensions, setSelectedExtensions] = useState<Set<string>>(new Set());

  // Convert Set to array for API calls
  const extensionsArray = useMemo(
    () => (selectedExtensions.size > 0 ? Array.from(selectedExtensions) : undefined),
    [selectedExtensions]
  );

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['stats-summary', extensionsArray],
    queryFn: () => statsApi.getSummary(extensionsArray),
  });

  const { data: progressSummary } = useQuery({
    queryKey: ['progress-summary'],
    queryFn: progressApi.getSummary,
    refetchInterval: 60000,
  });

  const handleFolderSelect = useCallback((folder: FolderWithProgress) => {
    setSelectedFolder(folder);
    setSelectedFile(null);
  }, []);

  const handleFileSelect = useCallback((file: FileWithProgress) => {
    setSelectedFile(file);
  }, []);

  if (summaryLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Extension Filter */}
      <ExtensionFilter
        selectedExtensions={selectedExtensions}
        onChange={setSelectedExtensions}
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Files"
          value={summary?.total_files.toLocaleString() || '0'}
          subtitle={progressSummary ? `${progressSummary.matching.files_with_hands} with hands` : undefined}
          icon={<Files className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Total Size"
          value={summary?.total_size_formatted || '0 B'}
          subtitle={`${summary?.total_folders || 0} folders`}
          icon={<HardDrive className="w-6 h-6" />}
          color="green"
        />
        <StatCard
          title="Media Duration"
          value={summary?.total_duration_formatted || '0h'}
          subtitle={progressSummary ? `${progressSummary.metadata_db.total_hands} hands analyzed` : undefined}
          icon={<Clock className="w-6 h-6" />}
          color="purple"
        />
        <StatCard
          title="Match Rate"
          value={progressSummary ? `${progressSummary.matching.match_rate}%` : '0%'}
          subtitle={progressSummary ? `${progressSummary.archive_db.completed}/${progressSummary.archive_db.total_tasks} completed` : undefined}
          icon={<FileType className="w-6 h-6" />}
          color="orange"
        />
      </div>

      {/* Main Content: Flex Layout + Independent Scroll */}
      <div className="flex flex-col lg:flex-row gap-6" style={{ height: 'calc(100vh - 280px)' }}>
        {/* Left: Progress Overview - Independent Scroll */}
        <div className="flex-[2] min-h-0 overflow-y-auto">
          <FolderTreeWithProgress
            initialDepth={3}
            showFiles={true}
            onFolderSelect={handleFolderSelect}
            onFileSelect={handleFileSelect}
          />
        </div>

        {/* Right Panel: Detail & Data Sources - Independent Scroll */}
        <div className="flex-1 min-h-0 overflow-y-auto space-y-4">
          {/* Selected Folder Detail */}
          {selectedFolder && (
            <FolderProgressDetail
              folderPath={selectedFolder.path}
              onFileSelect={handleFileSelect}
            />
          )}

          {/* Selected File Detail */}
          {selectedFile && selectedFile.metadata_progress && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <h4 className="font-semibold text-gray-900 mb-2 text-sm">File Detail</h4>
              <p className="text-xs text-gray-500 truncate mb-3">{selectedFile.name}</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-gray-50 p-2 rounded">
                  <span className="text-gray-500">Duration</span>
                  <span className="float-right font-medium">{selectedFile.duration_formatted}</span>
                </div>
                <div className="bg-gray-50 p-2 rounded">
                  <span className="text-gray-500">Size</span>
                  <span className="float-right font-medium">{selectedFile.size_formatted}</span>
                </div>
                <div className="bg-purple-50 p-2 rounded">
                  <span className="text-purple-600">Hands</span>
                  <span className="float-right font-medium">
                    {selectedFile.metadata_progress.hand_count}
                  </span>
                </div>
                <div className="bg-purple-50 p-2 rounded">
                  <span className="text-purple-600">Progress</span>
                  <span className="float-right font-medium">
                    {selectedFile.metadata_progress.progress_percent.toFixed(1)}%
                  </span>
                </div>
                <div className="col-span-2 bg-purple-50 p-2 rounded">
                  <span className="text-purple-600">Timecode</span>
                  <span className="float-right font-medium">
                    {selectedFile.metadata_progress.max_timecode_formatted}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Data Source Status - Compact */}
          <DataSourceStatus />

          {/* Quick Stats */}
          {progressSummary && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <h4 className="font-semibold text-gray-900 mb-3 text-sm">Progress Summary</h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">NAS Folders</span>
                  <span className="font-medium">{progressSummary.nas.total_folders}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">NAS Files</span>
                  <span className="font-medium">{progressSummary.nas.total_files}</span>
                </div>
                <hr className="my-2" />
                <div className="flex justify-between items-center">
                  <span className="text-blue-600">[archive] Tasks</span>
                  <span className="font-medium">{progressSummary.archive_db.total_tasks}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-blue-600">[archive] Completed</span>
                  <span className="font-medium text-green-600">{progressSummary.archive_db.completed}</span>
                </div>
                <hr className="my-2" />
                <div className="flex justify-between items-center">
                  <span className="text-purple-600">[metadata] Hands</span>
                  <span className="font-medium">{progressSummary.metadata_db.total_hands}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-purple-600">[metadata] Worksheets</span>
                  <span className="font-medium">{progressSummary.metadata_db.worksheets}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
