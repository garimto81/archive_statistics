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
