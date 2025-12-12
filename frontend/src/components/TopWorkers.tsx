/**
 * TopWorkers - 상위 작업자 랭킹 컴포넌트
 *
 * 작업 진행률 기준 상위 작업자들을 표시.
 * PRD-0040: Archiving Status UI 요구사항 구현.
 *
 * Block: archiving.status
 */
import { useQuery } from '@tanstack/react-query';
import { Users, Trophy, TrendingUp } from 'lucide-react';
import { workerStatsApi } from '../services/api';

interface TopWorkersProps {
  limit?: number;
  compact?: boolean;
}

export default function TopWorkers({ limit = 5, compact = false }: TopWorkersProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['worker-stats'],
    queryFn: workerStatsApi.getAll,
    refetchInterval: 60000,
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-8 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Sort workers by progress_percent descending and take top N
  const topWorkers = [...(data?.workers || [])]
    .sort((a, b) => b.progress_percent - a.progress_percent)
    .slice(0, limit);

  const getRankBadge = (index: number) => {
    if (index === 0) return <Trophy className="w-4 h-4 text-yellow-500" />;
    if (index === 1) return <span className="text-sm font-bold text-gray-400">2nd</span>;
    if (index === 2) return <span className="text-sm font-bold text-amber-600">3rd</span>;
    return <span className="text-xs text-gray-400">{index + 1}th</span>;
  };

  const getProgressColor = (percent: number) => {
    if (percent >= 80) return 'bg-green-500';
    if (percent >= 50) return 'bg-blue-500';
    if (percent >= 30) return 'bg-yellow-500';
    return 'bg-gray-400';
  };

  if (compact) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Top Workers</h3>
        </div>
        <div className="space-y-2">
          {topWorkers.map((worker, index) => (
            <div
              key={worker.pic}
              className="flex items-center justify-between py-1"
            >
              <div className="flex items-center gap-2">
                <div className="w-6 flex justify-center">{getRankBadge(index)}</div>
                <span className="text-sm text-gray-700 truncate max-w-[100px]">
                  {worker.pic || 'Unknown'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-16 bg-gray-200 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full ${getProgressColor(worker.progress_percent)}`}
                    style={{ width: `${Math.min(worker.progress_percent, 100)}%` }}
                  />
                </div>
                <span className="text-xs font-medium text-gray-600 w-10 text-right">
                  {worker.progress_percent.toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>
        {data?.summary && (
          <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between text-xs text-gray-500">
            <span>{data.summary.total_workers} workers</span>
            <span className="flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              {data.summary.overall_progress.toFixed(1)}% avg
            </span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Top Workers</h3>
        </div>
        {data?.summary && (
          <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600">
            {data.summary.total_workers} total
          </span>
        )}
      </div>

      <div className="space-y-3">
        {topWorkers.map((worker, index) => (
          <div
            key={worker.pic}
            className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div className="w-8 flex justify-center">{getRankBadge(index)}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-800 truncate">
                  {worker.pic || 'Unknown'}
                </span>
                <span className="text-xs text-gray-500">
                  {worker.total_done}/{worker.total_videos}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(worker.progress_percent)}`}
                  style={{ width: `${Math.min(worker.progress_percent, 100)}%` }}
                />
              </div>
            </div>
            <span className="text-sm font-semibold text-gray-700 w-12 text-right">
              {worker.progress_percent.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>

      {data?.summary && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div>
              <div className="font-semibold text-gray-900">
                {data.summary.total_videos.toLocaleString()}
              </div>
              <div className="text-gray-500">Total Videos</div>
            </div>
            <div>
              <div className="font-semibold text-green-600">
                {data.summary.total_done.toLocaleString()}
              </div>
              <div className="text-gray-500">Completed</div>
            </div>
            <div>
              <div className="font-semibold text-blue-600">
                {data.summary.overall_progress.toFixed(1)}%
              </div>
              <div className="text-gray-500">Progress</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
