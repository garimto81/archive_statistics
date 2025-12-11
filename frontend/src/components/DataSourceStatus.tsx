/**
 * DataSourceStatus - 데이터 소스 연결 상태 패널
 *
 * 모든 Google Sheets 데이터 소스의 연결 상태를 한눈에 보여주는 패널.
 * archive_db, metadata_db, iconik_db 각각의 상태를 표시.
 *
 * Block: components.data-source-status
 */
import { useQuery } from '@tanstack/react-query';
import { Database, RefreshCw } from 'lucide-react';
import { dataSourcesApi } from '../services/api';
import SyncStatusBadge from './SyncStatusBadge';

export default function DataSourceStatus() {
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['data-sources-status'],
    queryFn: dataSourcesApi.getStatus,
    refetchInterval: 60000, // 1분마다 갱신
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Data Sources</h3>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isRefetching}
          className="p-1 hover:bg-gray-100 rounded transition-colors"
          title="Refresh status"
        >
          <RefreshCw className={`w-4 h-4 text-gray-500 ${isRefetching ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="space-y-2">
        {data?.archive_db && (
          <SyncStatusBadge
            source="archive_db"
            label={data.archive_db.type}
            enabled={data.archive_db.enabled}
            status={data.archive_db.status}
            lastSync={data.archive_db.last_sync}
            recordCount={data.archive_db.record_count}
          />
        )}
        {data?.metadata_db && (
          <SyncStatusBadge
            source="metadata_db"
            label={data.metadata_db.type}
            enabled={data.metadata_db.enabled}
            status={data.metadata_db.status}
            lastSync={data.metadata_db.last_sync}
            recordCount={data.metadata_db.record_count}
          />
        )}
        {data?.iconik_db && (
          <SyncStatusBadge
            source="iconik_db"
            label={data.iconik_db.type}
            enabled={data.iconik_db.enabled}
            status={data.iconik_db.status}
            lastSync={data.iconik_db.last_sync}
            recordCount={data.iconik_db.record_count}
          />
        )}
      </div>
    </div>
  );
}
