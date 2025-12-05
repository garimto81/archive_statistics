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
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Stats API
export const statsApi = {
  getSummary: async (): Promise<StatsSummary> => {
    const { data } = await api.get('/stats/summary');
    return data;
  },

  getFileTypes: async (limit = 20): Promise<FileTypeStats[]> => {
    const { data } = await api.get(`/stats/file-types?limit=${limit}`);
    return data;
  },

  getHistory: async (period = 'daily', days = 30): Promise<{ data: HistoryData[] }> => {
    const { data } = await api.get(`/stats/history?period=${period}&days=${days}`);
    return data;
  },
};

// Folders API
export const foldersApi = {
  getTree: async (path?: string, depth = 2): Promise<FolderTreeNode[]> => {
    const params = new URLSearchParams();
    if (path) params.append('path', path);
    params.append('depth', depth.toString());
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

export default api;
