import axios from 'axios';
import type {
  StatsSummary,
  FileTypeStats,
  FolderTreeNode,
  HistoryData,
  WorkStatusListResponse,
  WorkStatus,
  WorkStatusCreate,
  WorkStatusUpdate,
  Archive,
  ScanStatus,
  ScanHistory,
  WorkerStatsListResponse,
  WorkerStatsSummary,
  WorkerDetailResponse,
  AllDataSourcesResponse,
  WorkStatusSummary,
  HandAnalysisSummary,
  FolderWithProgress,
  ProgressSummary,
  CodecSummary,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Stats API
export const statsApi = {
  getSummary: async (extensions?: string[]): Promise<StatsSummary> => {
    const params = new URLSearchParams();
    if (extensions && extensions.length > 0) {
      params.append('extensions', extensions.join(','));
    }
    const url = params.toString() ? `/stats/summary?${params}` : '/stats/summary';
    const { data } = await api.get(url);
    return data;
  },

  getFileTypes: async (limit = 20, extensions?: string[]): Promise<FileTypeStats[]> => {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (extensions && extensions.length > 0) {
      params.append('extensions', extensions.join(','));
    }
    const { data } = await api.get(`/stats/file-types?${params}`);
    return data;
  },

  getHistory: async (period = 'daily', days = 30): Promise<{ data: HistoryData[] }> => {
    const { data } = await api.get(`/stats/history?period=${period}&days=${days}`);
    return data;
  },

  getAvailableExtensions: async (): Promise<string[]> => {
    const { data } = await api.get('/stats/available-extensions');
    return data;
  },

  getCodecs: async (limit = 10, extensions?: string[]): Promise<CodecSummary> => {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (extensions && extensions.length > 0) {
      params.append('extensions', extensions.join(','));
    }
    const { data } = await api.get(`/stats/codecs?${params}`);
    return data;
  },
};

// Folders API
export const foldersApi = {
  getTree: async (path?: string, depth = 2, extensions?: string[]): Promise<FolderTreeNode[]> => {
    const params = new URLSearchParams();
    if (path) params.append('path', path);
    params.append('depth', depth.toString());
    if (extensions && extensions.length > 0) {
      params.append('extensions', extensions.join(','));
    }
    const { data } = await api.get(`/folders/tree?${params}`);
    return data;
  },

  getDetails: async (path: string) => {
    const { data } = await api.get(`/folders/details?path=${encodeURIComponent(path)}`);
    return data;
  },

  getTopFolders: async (limit = 10): Promise<FolderTreeNode[]> => {
    const { data } = await api.get(`/folders/top?limit=${limit}`);
    return data;
  },
};

// Work Status API
export const workStatusApi = {
  getArchives: async (): Promise<Archive[]> => {
    const { data } = await api.get('/work-status/archives');
    return data;
  },

  createArchive: async (archive: { name: string; description?: string }): Promise<Archive> => {
    const { data } = await api.post('/work-status/archives', archive);
    return data;
  },

  getAll: async (filters?: {
    archive_id?: number;
    status?: string;
    pic?: string;
  }): Promise<WorkStatusListResponse> => {
    const params = new URLSearchParams();
    if (filters?.archive_id) params.append('archive_id', filters.archive_id.toString());
    if (filters?.status) params.append('status', filters.status);
    if (filters?.pic) params.append('pic', filters.pic);
    const { data } = await api.get(`/work-status?${params}`);
    return data;
  },

  getById: async (id: number): Promise<WorkStatus> => {
    const { data } = await api.get(`/work-status/${id}`);
    return data;
  },

  create: async (workStatus: WorkStatusCreate): Promise<WorkStatus> => {
    const { data } = await api.post('/work-status', workStatus);
    return data;
  },

  update: async (id: number, workStatus: WorkStatusUpdate): Promise<WorkStatus> => {
    const { data } = await api.put(`/work-status/${id}`, workStatus);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/work-status/${id}`);
  },

  importCSV: async (file: File, replace = false): Promise<{
    success: boolean;
    total_rows: number;
    imported_rows: number;
    skipped_rows: number;
    errors: string[];
  }> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post(`/work-status/import?replace=${replace}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  exportCSV: async (): Promise<Blob> => {
    const { data } = await api.get('/work-status/export/csv', {
      responseType: 'blob',
    });
    return data;
  },
};

// Generate unique client ID for viewer tracking
const getClientId = (): string => {
  let clientId = localStorage.getItem('archive_stats_client_id');
  if (!clientId) {
    clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('archive_stats_client_id', clientId);
  }
  return clientId;
};

// Scan API
export const scanApi = {
  getStatus: async (): Promise<ScanStatus> => {
    const clientId = getClientId();
    const { data } = await api.get(`/scan/status?client_id=${clientId}`);
    return data;
  },

  start: async (scanType = 'manual', path?: string): Promise<{
    scan_id: number;
    message: string;
    status: string;
  }> => {
    const { data } = await api.post('/scan/start', { scan_type: scanType, path });
    return data;
  },

  stop: async (): Promise<void> => {
    await api.post('/scan/stop');
  },

  getHistory: async (limit = 10): Promise<ScanHistory[]> => {
    const { data } = await api.get(`/scan/history?limit=${limit}`);
    return data;
  },
};

// Worker Stats API
export const workerStatsApi = {
  getAll: async (): Promise<WorkerStatsListResponse> => {
    const { data } = await api.get('/worker-stats');
    return data;
  },

  getSummary: async (): Promise<WorkerStatsSummary> => {
    const { data } = await api.get('/worker-stats/summary');
    return data;
  },

  getByPic: async (pic: string): Promise<WorkerDetailResponse> => {
    const { data } = await api.get(`/worker-stats/${encodeURIComponent(pic)}`);
    return data;
  },
};

// Sync API - Google Sheets Synchronization
export interface SyncStatus {
  enabled: boolean;
  status: 'idle' | 'syncing' | 'error';
  last_sync: string | null;
  next_sync: string | null;
  error: string | null;
  interval_minutes: number;
  last_result: {
    total_records: number;
    synced_count: number;
    created_count: number;
    updated_count: number;
  } | null;
}

export interface SyncTriggerResponse {
  success: boolean;
  synced_at: string;
  total_records: number;
  synced_count: number;
  created_count: number;
  updated_count: number;
  error: string | null;
  message: string;
}

export const syncApi = {
  getStatus: async (): Promise<SyncStatus> => {
    const { data } = await api.get('/sync/status');
    return data;
  },

  trigger: async (): Promise<SyncTriggerResponse> => {
    const { data } = await api.post('/sync/trigger');
    return data;
  },
};

// Data Sources API - 통합 데이터 소스 상태
export const dataSourcesApi = {
  getStatus: async (): Promise<AllDataSourcesResponse> => {
    const { data } = await api.get('/data-sources/status');
    return data;
  },

  getWorkStatusSummary: async (): Promise<WorkStatusSummary> => {
    const { data } = await api.get('/data-sources/work-status/summary');
    return data;
  },

  getHandAnalysisSummary: async (): Promise<HandAnalysisSummary> => {
    const { data } = await api.get('/data-sources/hand-analysis/summary');
    return data;
  },
};

// Progress API - 간트차트용 폴더 트리 + 진행률
export const progressApi = {
  getTreeWithProgress: async (
    path?: string,
    depth = 2,
    includeFiles = false,
    extensions?: string[]
  ): Promise<FolderWithProgress[]> => {
    const params = new URLSearchParams();
    if (path) params.append('path', path);
    params.append('depth', depth.toString());
    params.append('include_files', includeFiles.toString());
    if (extensions && extensions.length > 0) {
      params.append('extensions', extensions.join(','));
    }
    const { data } = await api.get(`/progress/tree?${params}`);
    return data;
  },

  getFolderDetail: async (
    folderPath: string,
    includeFiles = true
  ): Promise<FolderWithProgress> => {
    const params = new URLSearchParams();
    params.append('include_files', includeFiles.toString());
    const { data } = await api.get(
      `/progress/folder/${encodeURIComponent(folderPath)}?${params}`
    );
    return data;
  },

  getFileDetail: async (filePath: string) => {
    const { data } = await api.get(
      `/progress/file/${encodeURIComponent(filePath)}`
    );
    return data;
  },

  getSummary: async (extensions?: string[]): Promise<ProgressSummary> => {
    const params = new URLSearchParams();
    if (extensions && extensions.length > 0) {
      params.append('extensions', extensions.join(','));
    }
    const url = params.toString() ? `/progress/summary?${params}` : '/progress/summary';
    const { data } = await api.get(url);
    return data;
  },
};

export default api;
