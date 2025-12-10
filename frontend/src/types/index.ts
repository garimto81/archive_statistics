// Statistics Types
export interface StatsSummary {
  total_files: number;
  total_size: number;
  total_size_formatted: string;
  total_duration: number;
  total_duration_formatted: string;
  total_folders: number;
  file_type_count: number;
  last_scan_at: string | null;
}

export interface FileTypeStats {
  extension: string;
  mime_type: string | null;
  file_count: number;
  total_size: number;
  total_size_formatted: string;
  percentage: number;
}

// Codec Statistics Types
export interface CodecStats {
  codec_name: string;
  codec_type: 'video' | 'audio';
  file_count: number;
  total_size: number;
  total_size_formatted: string;
  total_duration: number;
  total_duration_formatted: string;
  percentage: number;
}

export interface CodecSummary {
  video_codecs: CodecStats[];
  audio_codecs: CodecStats[];
  total_video_files: number;
  total_audio_analyzed: number;
}

// Codecs by Extension Types
export interface CodecCount {
  codec_name: string;
  file_count: number;
  percentage: number;
}

export interface ExtensionCodecStats {
  extension: string;
  total_files: number;
  video_codecs: CodecCount[];
  audio_codecs: CodecCount[];
}

export interface CodecsByExtensionResponse {
  extensions: ExtensionCodecStats[];
  total_extensions: number;
}

export interface FolderTreeNode {
  id: number;
  name: string;
  path: string;
  size: number;
  size_formatted: string;
  file_count: number;
  folder_count: number;
  duration: number;
  depth: number;
  children: FolderTreeNode[];
}

export interface HistoryData {
  date: string;
  total_size: number;
  total_files: number;
  total_folders: number;
  total_duration: number;
  size_change: number | null;
}

// Work Status Types
export interface Archive {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkStatus {
  id: number;
  archive_id: number;
  archive_name: string | null;
  category: string;
  pic: string | null;
  status: string;
  total_videos: number;
  excel_done: number;
  progress_percent: number;
  notes1: string | null;
  notes2: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkStatusListResponse {
  items: WorkStatus[];
  total_count: number;
  total_videos: number;
  total_done: number;
  overall_progress: number;
}

export interface WorkStatusCreate {
  archive_id: number;
  category: string;
  pic?: string;
  status?: string;
  total_videos?: number;
  excel_done?: number;
  notes1?: string;
  notes2?: string;
}

export interface WorkStatusUpdate {
  category?: string;
  pic?: string;
  status?: string;
  total_videos?: number;
  excel_done?: number;
  notes1?: string;
  notes2?: string;
}

// Scan Types
export interface ScanStatus {
  is_scanning: boolean;
  scan_id: number | null;
  progress: number;
  current_folder: string | null;
  files_scanned: number;
  total_files_estimated: number;
  started_at: string | null;
  elapsed_seconds: number | null;
  estimated_remaining_seconds: number | null;
  logs: string[];
  media_files_processed: number;
  total_duration_found: number;
  active_viewers: number;
}

export interface ScanHistory {
  id: number;
  scan_type: string;
  status: string;
  total_size: number;
  total_files: number;
  total_folders: number;
  total_duration: number;
  new_files: number;
  deleted_files: number;
  size_change: number;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
}

// Worker Stats Types
export interface WorkerTask {
  id: number;
  archive_id: number;
  archive_name: string | null;
  category: string;
  status: string;
  total_videos: number;
  excel_done: number;
  progress_percent: number;
  notes1: string | null;
  notes2: string | null;
}

export interface WorkerStats {
  pic: string;
  task_count: number;
  total_videos: number;
  total_done: number;
  progress_percent: number;
  archives: string[];
  status_breakdown: Record<string, number>;
}

export interface WorkerStatsSummary {
  total_workers: number;
  total_videos: number;
  total_done: number;
  overall_progress: number;
  by_status: Record<string, number>;
  by_archive: Record<string, number>;
}

export interface WorkerStatsListResponse {
  workers: WorkerStats[];
  summary: WorkerStatsSummary;
}

export interface WorkerDetailResponse extends WorkerStats {
  tasks: WorkerTask[];
}

// Data Sources Types
export interface DataSourceStatus {
  name: string;
  type: string;
  enabled: boolean;
  status: string;
  last_sync: string | null;
  next_sync: string | null;
  record_count: number;
  details: {
    created?: number;
    updated?: number;
    worksheets?: number;
    note?: string;
  } | null;
}

export interface AllDataSourcesResponse {
  archive_db: DataSourceStatus;
  metadata_db: DataSourceStatus;
  iconik_db: DataSourceStatus;
}

export interface WorkStatusSummary {
  total_tasks: number;
  completed: number;
  in_progress: number;
  pending: number;
  overall_progress: number;
  last_sync: string | null;
}

export interface HandAnalysisSummary {
  total_hands: number;
  worksheets_count: number;
  by_worksheet: Array<{ worksheet: string; count: number }>;
  last_sync: string | null;
}

// Progress Types (간트차트용)

/**
 * WorkSummary - 폴더별 작업 진행률 요약
 * Backend progress_service.py에서 생성되며, 하이어라키 합산값을 포함
 */
export interface WorkSummary {
  task_count: number;           // 직접 매칭된 작업 수
  total_files: number;          // NAS 파일 수 (진행률 계산 기준)
  total_done: number;           // excel_done 합계
  combined_progress: number;    // NAS 기준 진행률 (90%+ = 100%)
  sheets_total_videos: number;  // 구글 시트 total_videos
  sheets_excel_done: number;    // 구글 시트 excel_done
  actual_progress?: number;     // 시트 기준 진행률 (optional)
  data_source_mismatch?: boolean; // NAS vs 시트 불일치 여부
  mismatch_count?: number;      // 차이값
}

export interface WorkStatusInfo {
  id: number;
  category: string;
  pic: string | null;
  status: string;
  total_videos: number;
  excel_done: number;
  progress_percent: number;
  notes1: string | null;
  notes2: string | null;
}

export interface HandAnalysisInfo {
  worksheet: string;
  hand_count: number;
  max_timecode_sec: number;
  max_timecode_formatted: string;
}

export interface MetadataProgress {
  hand_count: number;
  max_timecode_sec: number;
  max_timecode_formatted: string;
  progress_percent: number;
  is_complete: boolean;
}

export interface FileWithProgress {
  id: number;
  name: string;
  path: string;
  size: number;
  size_formatted: string;
  duration: number;
  duration_formatted: string;
  extension: string | null;
  metadata_progress?: MetadataProgress;
}

export interface FolderWithProgress {
  id: number;
  name: string;
  path: string;
  size: number;
  size_formatted: string;
  file_count: number;
  folder_count: number;
  duration: number;
  duration_formatted: string;
  depth: number;
  // Progress 데이터 (Backend work_summary 기반)
  work_summary?: WorkSummary;       // 트리 뷰용 요약 (하이어라키 합산 포함)
  work_statuses?: WorkStatusInfo[]; // 상세 패널용 목록
  work_status?: WorkStatusInfo;     // deprecated: 하위 호환용
  hand_analysis?: HandAnalysisInfo;
  children: FolderWithProgress[];
  files?: FileWithProgress[];
}

export interface ProgressSummary {
  nas: {
    total_folders: number;
    total_files: number;
  };
  archive_db: {
    total_tasks: number;
    completed: number;
    in_progress: number;
  };
  metadata_db: {
    total_hands: number;
    worksheets: number;
    matched_files: number;
  };
  matching: {
    files_with_hands: number;
    match_rate: number;
  };
}

// Folder Mapping Types (폴더-작업 연결 관리)

export interface UnmappedFolder {
  id: number;
  path: string;
  name: string;
  depth: number;
  file_count: number;
}

export interface FolderMapping {
  folder_id: number;
  folder_path: string;
  folder_name: string;
  work_status_id: number | null;
  work_status_category: string | null;
}

export interface WorkStatusOption {
  id: number;
  category: string;
  archive_name: string | null;
  total_videos: number;
  excel_done: number;
}

export interface AutoMatchResult {
  dry_run: boolean;
  total_unmatched: number;
  matched_count: number;
  matches: Array<{
    folder_id: number;
    folder_path: string;
    folder_name: string;
    work_status_id: number;
    work_status_category: string;
  }>;
}

export interface BulkConnectResult {
  success_count: number;
  error_count: number;
  errors: string[];
}
