/**
 * SyncStatusBadge - 데이터 소스 동기화 상태 배지
 *
 * 각 데이터 소스(archive_db, metadata_db, iconik_db)의 상태를 표시하는 공통 컴포넌트.
 * 색상으로 데이터 소스를 구분하고, 상태 아이콘으로 연결/동기화 상태를 표시.
 *
 * Block: components.sync-status
 */
import { CheckCircle, PauseCircle, RefreshCw, AlertCircle } from 'lucide-react';

type DataSourceType = 'archive_db' | 'metadata_db' | 'iconik_db';

interface SyncStatusBadgeProps {
  source: DataSourceType;
  label: string;
  enabled: boolean;
  status: string;
  lastSync?: string | null;
  recordCount?: number;
  compact?: boolean;
}

const SOURCE_COLORS: Record<DataSourceType, { bg: string; text: string }> = {
  archive_db: { bg: 'bg-blue-100', text: 'text-blue-700' },
  metadata_db: { bg: 'bg-purple-100', text: 'text-purple-700' },
  iconik_db: { bg: 'bg-gray-100', text: 'text-gray-500' },
};

function formatLastSync(isoString: string | null | undefined): string {
  if (!isoString) return 'Never';
  const date = new Date(isoString);
  return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
}

export default function SyncStatusBadge({
  source,
  label,
  enabled,
  status,
  lastSync,
  recordCount,
  compact = false,
}: SyncStatusBadgeProps) {
  const colors = SOURCE_COLORS[source];

  const StatusIcon = () => {
    if (!enabled) return <PauseCircle className="w-4 h-4 text-gray-400" />;
    if (status === 'syncing') return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
    if (status === 'error') return <AlertCircle className="w-4 h-4 text-red-500" />;
    return <CheckCircle className="w-4 h-4 text-green-500" />;
  };

  if (compact) {
    return (
      <div className="flex items-center gap-1.5">
        <StatusIcon />
        <span className={`text-xs px-1.5 py-0.5 rounded ${colors.bg} ${colors.text}`}>
          {source.replace('_', ' ')}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
      <StatusIcon />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900">{label}</span>
          <span className={`text-xs px-1.5 py-0.5 rounded ${colors.bg} ${colors.text}`}>
            {source.replace('_', ' ')}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          {recordCount !== undefined && <span>{recordCount} records</span>}
          {lastSync && <span>Last: {formatLastSync(lastSync)}</span>}
        </div>
      </div>
    </div>
  );
}
