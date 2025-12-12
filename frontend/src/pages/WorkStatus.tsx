import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Upload,
  Download,
  Plus,
  Edit2,
  Trash2,
  LayoutGrid,
  Table,
  Users,
  User,
  BarChart3,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Cloud,
  CloudOff,
  AlertCircle,
} from 'lucide-react';
import clsx from 'clsx';
import { archivingStatusApi, workerStatsApi, syncApi } from '../services/api';
import type { WorkStatus, WorkerStats } from '../types';

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-700',
  in_progress: 'bg-blue-100 text-blue-700',
  review: 'bg-yellow-100 text-yellow-700',
  completed: 'bg-green-100 text-green-700',
};

const STATUS_LABELS: Record<string, string> = {
  pending: '대기',
  in_progress: '작업 중',
  review: '검토',
  completed: '완료',
};

// Sync Status Indicator Component
function SyncStatusIndicator() {
  const queryClient = useQueryClient();

  const { data: syncStatus } = useQuery({
    queryKey: ['sync-status'],
    queryFn: syncApi.getStatus,
    refetchInterval: (query) => {
      // Poll more frequently when syncing
      const data = query.state.data;
      if (data?.status === 'syncing') return 1000;
      return 30000; // 30 seconds when idle
    },
  });

  const syncMutation = useMutation({
    mutationFn: syncApi.trigger,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-status'] });
      queryClient.invalidateQueries({ queryKey: ['work-status'] });
      queryClient.invalidateQueries({ queryKey: ['worker-stats'] });
    },
  });

  if (!syncStatus?.enabled) {
    return null;
  }

  const formatTime = (isoString: string | null) => {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const isSyncing = syncStatus.status === 'syncing';
  const hasError = syncStatus.status === 'error';

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-gray-50 rounded-lg border border-gray-200">
      {/* Status Icon */}
      <div className="flex items-center gap-2">
        {isSyncing ? (
          <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />
        ) : hasError ? (
          <CloudOff className="w-4 h-4 text-red-500" />
        ) : (
          <Cloud className="w-4 h-4 text-green-500" />
        )}
        <span className="text-sm font-medium text-gray-700">Google Sheets</span>
      </div>

      {/* Last Sync Time */}
      <div className="text-xs text-gray-500">
        {isSyncing ? (
          <span className="text-blue-600">Syncing...</span>
        ) : hasError ? (
          <span className="text-red-600 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            Error
          </span>
        ) : (
          <span>Last: {formatTime(syncStatus.last_sync)}</span>
        )}
      </div>

      {/* Sync Result */}
      {syncStatus.last_result && !isSyncing && !hasError && (
        <div className="text-xs text-gray-400">
          ({syncStatus.last_result.synced_count} synced)
        </div>
      )}

      {/* Manual Sync Button */}
      <button
        onClick={() => syncMutation.mutate()}
        disabled={isSyncing || syncMutation.isPending}
        className={clsx(
          'p-1.5 rounded-md transition-colors',
          isSyncing || syncMutation.isPending
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-primary-100 text-primary-600 hover:bg-primary-200'
        )}
        title="Sync Now"
      >
        <RefreshCw
          className={clsx(
            'w-4 h-4',
            (isSyncing || syncMutation.isPending) && 'animate-spin'
          )}
        />
      </button>

      {/* Error Tooltip */}
      {hasError && syncStatus.error && (
        <div className="relative group">
          <AlertCircle className="w-4 h-4 text-red-500 cursor-help" />
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
            {syncStatus.error}
          </div>
        </div>
      )}
    </div>
  );
}

// Worker Card Component
function WorkerCard({ worker, onClick }: { worker: WorkerStats; onClick: () => void }) {
  const completedTasks = worker.status_breakdown.completed || 0;
  const totalTasks = worker.task_count;

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow cursor-pointer"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center">
          <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
            <User className="w-5 h-5 text-primary-600" />
          </div>
          <div className="ml-3">
            <h3 className="font-semibold text-gray-900">{worker.pic}</h3>
            <p className="text-sm text-gray-500">{worker.task_count} tasks</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-primary-600">
            {worker.progress_percent.toFixed(0)}%
          </div>
          <div className="text-xs text-gray-500">
            {completedTasks}/{totalTasks} done
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mt-4">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-primary-500 h-2 rounded-full transition-all"
            style={{ width: `${worker.progress_percent}%` }}
          />
        </div>
      </div>

      {/* Stats */}
      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-500">Videos:</span>
          <span className="ml-2 font-medium">{worker.total_videos.toLocaleString()}</span>
        </div>
        <div>
          <span className="text-gray-500">Done:</span>
          <span className="ml-2 font-medium">{worker.total_done.toLocaleString()}</span>
        </div>
      </div>

      {/* Archives */}
      <div className="mt-3 flex flex-wrap gap-1">
        {worker.archives.slice(0, 3).map((archive) => (
          <span
            key={archive}
            className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
          >
            {archive}
          </span>
        ))}
        {worker.archives.length > 3 && (
          <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded">
            +{worker.archives.length - 3}
          </span>
        )}
      </div>
    </div>
  );
}

// Worker Detail Modal
function WorkerDetailModal({
  pic,
  onClose,
}: {
  pic: string;
  onClose: () => void;
}) {
  const { data: workerDetail, isLoading } = useQuery({
    queryKey: ['worker-detail', pic],
    queryFn: () => workerStatsApi.getByPic(pic),
  });

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-6">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (!workerDetail) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-3xl w-full mx-4 max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
              <User className="w-6 h-6 text-primary-600" />
            </div>
            <div className="ml-4">
              <h2 className="text-xl font-bold text-gray-900">{workerDetail.pic}</h2>
              <p className="text-sm text-gray-500">
                {workerDetail.task_count} tasks | {workerDetail.total_videos.toLocaleString()} videos
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {/* Summary Stats */}
        <div className="px-6 py-4 bg-gray-50 grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-primary-600">
              {workerDetail.progress_percent.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">Progress</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {workerDetail.total_videos.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">Total Videos</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {workerDetail.total_done.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {(workerDetail.total_videos - workerDetail.total_done).toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">Remaining</div>
          </div>
        </div>

        {/* Tasks Table */}
        <div className="overflow-auto max-h-[400px]">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Archive
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Progress
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {workerDetail.tasks.map((task) => (
                <tr key={task.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {task.archive_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {task.category}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={clsx(
                        'px-2 py-1 text-xs font-medium rounded-full',
                        STATUS_COLORS[task.status] || STATUS_COLORS.pending
                      )}
                    >
                      {STATUS_LABELS[task.status] || task.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                        <div
                          className="bg-primary-500 h-2 rounded-full"
                          style={{ width: `${task.progress_percent}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-500">
                        {task.excel_done}/{task.total_videos}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default function WorkStatusPage() {
  const queryClient = useQueryClient();
  const [viewMode, setViewMode] = useState<'table' | 'kanban'>('table');
  const [activeTab, setActiveTab] = useState<'tasks' | 'workers'>('tasks');
  const [selectedWorker, setSelectedWorker] = useState<string | null>(null);
  const [, setEditingItem] = useState<WorkStatus | null>(null);
  const [, setIsModalOpen] = useState(false);
  const [showArchiveBreakdown, setShowArchiveBreakdown] = useState(false);

  const { data: workStatusData, isLoading } = useQuery({
    queryKey: ['work-status'],
    queryFn: () => archivingStatusApi.getAll(),
  });

  const { data: workerStatsData, isLoading: isLoadingWorkers } = useQuery({
    queryKey: ['worker-stats'],
    queryFn: () => workerStatsApi.getAll(),
  });

  useQuery({
    queryKey: ['archives'],
    queryFn: archivingStatusApi.getArchives,
  });

  const deleteMutation = useMutation({
    mutationFn: archivingStatusApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work-status'] });
      queryClient.invalidateQueries({ queryKey: ['worker-stats'] });
      setIsModalOpen(false);
      setEditingItem(null);
    },
  });

  const handleExport = async () => {
    const blob = await archivingStatusApi.exportCSV();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `work_status_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const result = await archivingStatusApi.importCSV(file, true);
      alert(`Import complete: ${result.imported_rows} rows imported`);
      queryClient.invalidateQueries({ queryKey: ['work-status'] });
      queryClient.invalidateQueries({ queryKey: ['worker-stats'] });
    } catch (error) {
      alert('Import failed');
    }
    e.target.value = '';
  };

  if (isLoading || isLoadingWorkers) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const items = workStatusData?.items || [];
  const workers = workerStatsData?.workers || [];
  const summary = workerStatsData?.summary;

  // Group by status for kanban view
  const kanbanColumns = {
    pending: items.filter((i) => i.status === 'pending'),
    in_progress: items.filter((i) => i.status === 'in_progress'),
    review: items.filter((i) => i.status === 'review'),
    completed: items.filter((i) => i.status === 'completed'),
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-gray-900">Archiving Status</h1>
            <SyncStatusIndicator />
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Total: {workStatusData?.total_videos.toLocaleString()} videos |
            Done: {workStatusData?.total_done.toLocaleString()} |
            Progress: {workStatusData?.overall_progress.toFixed(1)}%
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Tab Toggle */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('tasks')}
              className={clsx(
                'flex items-center px-3 py-1.5 rounded-md text-sm font-medium',
                activeTab === 'tasks' ? 'bg-white shadow-sm' : 'text-gray-600'
              )}
            >
              <Table className="w-4 h-4 mr-1.5" />
              Tasks
            </button>
            <button
              onClick={() => setActiveTab('workers')}
              className={clsx(
                'flex items-center px-3 py-1.5 rounded-md text-sm font-medium',
                activeTab === 'workers' ? 'bg-white shadow-sm' : 'text-gray-600'
              )}
            >
              <Users className="w-4 h-4 mr-1.5" />
              Workers
            </button>
          </div>

          {activeTab === 'tasks' && (
            <>
              {/* View Toggle */}
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('table')}
                  aria-label="Table view"
                  className={clsx(
                    'p-2 rounded-md',
                    viewMode === 'table' ? 'bg-white shadow-sm' : ''
                  )}
                >
                  <Table className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('kanban')}
                  aria-label="Kanban view"
                  className={clsx(
                    'p-2 rounded-md',
                    viewMode === 'kanban' ? 'bg-white shadow-sm' : ''
                  )}
                >
                  <LayoutGrid className="w-4 h-4" />
                </button>
              </div>

              {/* Import */}
              <label className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 cursor-pointer">
                <Upload className="w-4 h-4 mr-2" />
                Import CSV
                <input type="file" accept=".csv" className="hidden" onChange={handleImport} />
              </label>

              {/* Export */}
              <button
                onClick={handleExport}
                className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </button>

              {/* Add */}
              <button className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                <Plus className="w-4 h-4 mr-2" />
                Add Task
              </button>
            </>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="flex justify-between text-sm mb-2">
          <span className="font-medium">Overall Progress</span>
          <span>{workStatusData?.overall_progress.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-primary-500 h-3 rounded-full transition-all"
            style={{ width: `${workStatusData?.overall_progress || 0}%` }}
          />
        </div>
      </div>

      {/* Workers Tab Content */}
      {activeTab === 'workers' && (
        <div className="space-y-6">
          {/* Summary Cards */}
          {summary && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Users className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-gray-900">{summary.total_workers}</div>
                    <div className="text-sm text-gray-500">Total Workers</div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <BarChart3 className="w-5 h-5 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-gray-900">
                      {summary.total_videos.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-500">Total Videos</div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <BarChart3 className="w-5 h-5 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-green-600">
                      {summary.total_done.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-500">Completed</div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                    <BarChart3 className="w-5 h-5 text-orange-600" />
                  </div>
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-orange-600">
                      {(summary.total_videos - summary.total_done).toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-500">Remaining</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Status & Archive Breakdown */}
          {summary && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Status Breakdown */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <h3 className="font-semibold text-gray-900 mb-4">Status Breakdown</h3>
                <div className="space-y-3">
                  {Object.entries(summary.by_status).map(([status, count]) => (
                    <div key={status} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <span
                          className={clsx(
                            'px-2 py-1 text-xs font-medium rounded-full',
                            STATUS_COLORS[status] || STATUS_COLORS.pending
                          )}
                        >
                          {STATUS_LABELS[status] || status}
                        </span>
                      </div>
                      <span className="font-medium text-gray-900">{count} tasks</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Archive Breakdown */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <button
                  onClick={() => setShowArchiveBreakdown(!showArchiveBreakdown)}
                  className="flex items-center justify-between w-full"
                >
                  <h3 className="font-semibold text-gray-900">Archive Breakdown</h3>
                  {showArchiveBreakdown ? (
                    <ChevronUp className="w-5 h-5 text-gray-500" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-500" />
                  )}
                </button>
                {showArchiveBreakdown && (
                  <div className="mt-4 space-y-2">
                    {Object.entries(summary.by_archive)
                      .sort(([, a], [, b]) => b - a)
                      .map(([archive, videos]) => (
                        <div key={archive} className="flex items-center justify-between">
                          <span className="text-sm text-gray-700">{archive}</span>
                          <span className="text-sm font-medium text-gray-900">
                            {videos.toLocaleString()} videos
                          </span>
                        </div>
                      ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Worker Cards Grid */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Workers ({workers.length})</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {workers.map((worker) => (
                <WorkerCard
                  key={worker.pic}
                  worker={worker}
                  onClick={() => setSelectedWorker(worker.pic)}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tasks Tab Content */}
      {activeTab === 'tasks' && (
        <>
          {viewMode === 'table' ? (
            /* Table View */
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Archive
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Category
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      PIC
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Progress
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Notes
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {items.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {item.archive_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {item.category}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {item.pic || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={clsx(
                            'px-2 py-1 text-xs font-medium rounded-full',
                            STATUS_COLORS[item.status] || STATUS_COLORS.pending
                          )}
                        >
                          {STATUS_LABELS[item.status] || item.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                            <div
                              className="bg-primary-500 h-2 rounded-full"
                              style={{ width: `${item.progress_percent}%` }}
                            />
                          </div>
                          <span className="text-sm text-gray-500">
                            {item.excel_done}/{item.total_videos}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                        {item.notes1 || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                        <button
                          onClick={() => {
                            setEditingItem(item);
                            setIsModalOpen(true);
                          }}
                          className="text-primary-600 hover:text-primary-800 mr-3"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            if (confirm('Delete this item?')) {
                              deleteMutation.mutate(item.id);
                            }
                          }}
                          className="text-red-600 hover:text-red-800"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            /* Kanban View */
            <div className="grid grid-cols-4 gap-4">
              {Object.entries(kanbanColumns).map(([status, items]) => (
                <div key={status} className="bg-gray-50 rounded-xl p-4">
                  <h3 className="font-semibold text-gray-700 mb-4 flex items-center">
                    <span
                      className={clsx(
                        'w-3 h-3 rounded-full mr-2',
                        status === 'pending' && 'bg-gray-400',
                        status === 'in_progress' && 'bg-blue-500',
                        status === 'review' && 'bg-yellow-500',
                        status === 'completed' && 'bg-green-500'
                      )}
                    />
                    {STATUS_LABELS[status]} ({items.length})
                  </h3>
                  <div className="space-y-3">
                    {items.map((item) => (
                      <div
                        key={item.id}
                        className="bg-white rounded-lg p-4 shadow-sm border border-gray-100"
                      >
                        <div className="font-medium text-gray-900">{item.category}</div>
                        <div className="text-sm text-gray-500 mt-1">{item.archive_name}</div>
                        {item.pic && (
                          <div className="text-xs text-gray-400 mt-2">{item.pic}</div>
                        )}
                        <div className="mt-3">
                          <div className="flex justify-between text-xs text-gray-500 mb-1">
                            <span>Progress</span>
                            <span>{item.progress_percent.toFixed(0)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-1.5">
                            <div
                              className="bg-primary-500 h-1.5 rounded-full"
                              style={{ width: `${item.progress_percent}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Worker Detail Modal */}
      {selectedWorker && (
        <WorkerDetailModal
          pic={selectedWorker}
          onClose={() => setSelectedWorker(null)}
        />
      )}
    </div>
  );
}
