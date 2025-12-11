/**
 * HandAnalysisSummary - Hand Analysis 요약 패널
 *
 * metadata db에서 동기화된 핸드 분석 데이터를 요약하여 표시.
 * 워크시트별 핸드 수 분포를 시각화.
 *
 * Block: components.hand-analysis-summary
 */
import { useQuery } from '@tanstack/react-query';
import { Spade } from 'lucide-react';
import { dataSourcesApi } from '../services/api';

export default function HandAnalysisSummary() {
  const { data, isLoading } = useQuery({
    queryKey: ['hand-analysis-summary'],
    queryFn: dataSourcesApi.getHandAnalysisSummary,
    refetchInterval: 60000,
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-6 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const maxCount = Math.max(...(data?.by_worksheet?.map((w) => w.count) || [1]));

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Spade className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Hand Analysis</h3>
          <span className="text-xs px-1.5 py-0.5 rounded bg-purple-100 text-purple-700">
            metadata db
          </span>
        </div>
        <div className="text-sm text-gray-500">
          <span className="font-medium text-gray-900">{data?.total_hands || 0}</span> hands
        </div>
      </div>

      {/* Worksheet Breakdown */}
      <div className="space-y-2">
        {data?.by_worksheet?.slice(0, 6).map((ws) => (
          <div key={ws.worksheet} className="flex items-center gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex justify-between text-sm mb-0.5">
                <span className="text-gray-700 truncate" title={ws.worksheet}>
                  {ws.worksheet}
                </span>
                <span className="text-gray-500 ml-2">{ws.count}</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-1.5">
                <div
                  className="bg-purple-500 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${(ws.count / maxCount) * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary Footer */}
      <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between text-xs text-gray-500">
        <span>{data?.worksheets_count || 0} worksheets</span>
        {data?.last_sync && (
          <span>Last sync: {new Date(data.last_sync).toLocaleTimeString('ko-KR')}</span>
        )}
      </div>
    </div>
  );
}
