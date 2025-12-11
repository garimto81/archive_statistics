/**
 * WorkStatusSummary - Work Status 요약 패널
 *
 * archive db에서 동기화된 작업 현황을 요약하여 표시.
 * 전체 진행률, 상태별 작업 수를 보여줌.
 *
 * Block: components.work-status-summary
 */
import { useQuery } from '@tanstack/react-query';
import { ClipboardList, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { dataSourcesApi } from '../services/api';

export default function WorkStatusSummary() {
  const { data, isLoading } = useQuery({
    queryKey: ['work-status-summary'],
    queryFn: dataSourcesApi.getWorkStatusSummary,
    refetchInterval: 60000,
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-1/3"></div>
          <div className="h-8 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const progress = data?.overall_progress || 0;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <ClipboardList className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Work Status</h3>
          <span className="text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">
            archive db
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-600">Overall Progress</span>
          <span className="font-medium text-gray-900">{progress.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-blue-500 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-2 text-center">
        <div className="p-2 bg-gray-50 rounded-lg">
          <div className="text-lg font-semibold text-gray-900">{data?.total_tasks || 0}</div>
          <div className="text-xs text-gray-500">Total</div>
        </div>
        <div className="p-2 bg-green-50 rounded-lg">
          <div className="flex items-center justify-center gap-1">
            <CheckCircle className="w-3 h-3 text-green-600" />
            <span className="text-lg font-semibold text-green-700">{data?.completed || 0}</span>
          </div>
          <div className="text-xs text-green-600">Done</div>
        </div>
        <div className="p-2 bg-yellow-50 rounded-lg">
          <div className="flex items-center justify-center gap-1">
            <Clock className="w-3 h-3 text-yellow-600" />
            <span className="text-lg font-semibold text-yellow-700">{data?.in_progress || 0}</span>
          </div>
          <div className="text-xs text-yellow-600">In Progress</div>
        </div>
        <div className="p-2 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-center gap-1">
            <AlertCircle className="w-3 h-3 text-gray-500" />
            <span className="text-lg font-semibold text-gray-600">{data?.pending || 0}</span>
          </div>
          <div className="text-xs text-gray-500">Pending</div>
        </div>
      </div>

      {/* Last Sync */}
      {data?.last_sync && (
        <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500 text-center">
          Last sync: {new Date(data.last_sync).toLocaleTimeString('ko-KR')}
        </div>
      )}
    </div>
  );
}
