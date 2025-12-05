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
} from 'lucide-react';
import clsx from 'clsx';
import { workStatusApi } from '../services/api';
import type { WorkStatus } from '../types';

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

export default function WorkStatusPage() {
  const queryClient = useQueryClient();
  const [viewMode, setViewMode] = useState<'table' | 'kanban'>('table');
  const [, setEditingItem] = useState<WorkStatus | null>(null);
  const [, setIsModalOpen] = useState(false);

  const { data: workStatusData, isLoading } = useQuery({
    queryKey: ['work-status'],
    queryFn: () => workStatusApi.getAll(),
  });

  useQuery({
    queryKey: ['archives'],
    queryFn: workStatusApi.getArchives,
  });

  const deleteMutation = useMutation({
    mutationFn: workStatusApi.delete,
    onSuccess: () => {
      setIsModalOpen(false);
      setEditingItem(null);
    },
  });

  const handleExport = async () => {
    const blob = await workStatusApi.exportCSV();
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
      const result = await workStatusApi.importCSV(file, true);
      alert(`Import complete: ${result.imported_rows} rows imported`);
      queryClient.invalidateQueries({ queryKey: ['work-status'] });
    } catch (error) {
      alert('Import failed');
    }
    e.target.value = '';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const items = workStatusData?.items || [];

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
          <h1 className="text-2xl font-bold text-gray-900">Work Status</h1>
          <p className="text-sm text-gray-500 mt-1">
            Total: {workStatusData?.total_videos.toLocaleString()} videos |
            Done: {workStatusData?.total_done.toLocaleString()} |
            Progress: {workStatusData?.overall_progress.toFixed(1)}%
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* View Toggle */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('table')}
              className={clsx(
                'p-2 rounded-md',
                viewMode === 'table' ? 'bg-white shadow-sm' : ''
              )}
            >
              <Table className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('kanban')}
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

      {/* Content */}
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
    </div>
  );
}
