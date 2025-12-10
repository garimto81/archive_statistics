/**
 * Statistics - 파일 통계 페이지
 *
 * 아카이브 파일 분석 통계를 시각화하는 페이지.
 * - File Type Distribution (Pie Chart)
 * - Top Folders by Size (Bar Chart)
 * - Storage Growth Trend (Line Chart)
 *
 * Issue: #5
 * Block: progress.dashboard
 */
import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Files, HardDrive, Clock, FileType } from 'lucide-react';
import StatCard from '../components/StatCard';
import { statsApi, foldersApi } from '../services/api';

// Constants
const CHART_COLORS = ['#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#6B7280'];
const TOP_FILE_TYPES_LIMIT = 5;
const TOP_FOLDERS_LIMIT = 5;
const FILE_TYPES_TABLE_LIMIT = 10;
const HISTORY_DAYS = 30;

export default function Statistics() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['stats-summary'],
    queryFn: statsApi.getSummary,
  });

  const { data: fileTypes } = useQuery({
    queryKey: ['file-types'],
    queryFn: () => statsApi.getFileTypes(FILE_TYPES_TABLE_LIMIT),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const { data: history } = useQuery({
    queryKey: ['history'],
    queryFn: () => statsApi.getHistory('daily', HISTORY_DAYS),
    staleTime: 5 * 60 * 1000,
  });

  const { data: folderTree } = useQuery({
    queryKey: ['folder-tree-stats'],
    queryFn: () => foldersApi.getTree(undefined, 1),
    staleTime: 5 * 60 * 1000,
  });

  // Memoized: Transform history data for chart
  const chartData = useMemo(() =>
    history?.data?.map((item) => ({
      date: new Date(item.date).toLocaleDateString('ko-KR', {
        month: 'short',
        day: 'numeric',
      }),
      size: Math.round(item.total_size / (1024 * 1024 * 1024 * 1024)), // Convert to TB
      files: item.total_files,
    })) || []
  , [history]);

  // Memoized: Pie chart data
  const pieData = useMemo(() =>
    fileTypes?.slice(0, TOP_FILE_TYPES_LIMIT).map((type) => ({
      name: type.extension || 'unknown',
      value: type.percentage,
      count: type.file_count,
      size: type.total_size_formatted,
    })) || []
  , [fileTypes]);

  // Memoized: Top folders data (sorted by size, avoid mutation)
  const topFolders = useMemo(() => {
    if (!folderTree || folderTree.length === 0) return [];

    // Calculate total size for proper percentage
    const totalSize = folderTree.reduce((sum, f) => sum + f.size, 0);

    return [...folderTree]  // Create copy to avoid mutation
      .sort((a, b) => b.size - a.size)
      .slice(0, TOP_FOLDERS_LIMIT)
      .map((folder) => ({
        name: folder.name,
        size: folder.size,
        size_formatted: folder.size_formatted,
        percentage: totalSize > 0 ? (folder.size / totalSize) * 100 : 0,
      }));
  }, [folderTree]);

  if (summaryLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Statistics</h1>
        <span className="text-sm text-gray-500">
          Last updated: {summary?.last_scan_at ? new Date(summary.last_scan_at).toLocaleString() : 'N/A'}
        </span>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Files"
          value={summary?.total_files.toLocaleString() || '0'}
          subtitle={`${summary?.total_folders || 0} folders`}
          icon={<Files className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Total Size"
          value={summary?.total_size_formatted || '0 B'}
          subtitle="Archive storage"
          icon={<HardDrive className="w-6 h-6" />}
          color="green"
        />
        <StatCard
          title="Media Duration"
          value={summary?.total_duration_formatted || '0h'}
          subtitle="Total playback time"
          icon={<Clock className="w-6 h-6" />}
          color="purple"
        />
        <StatCard
          title="File Types"
          value={summary?.file_type_count || 0}
          subtitle="Unique extensions"
          icon={<FileType className="w-6 h-6" />}
          color="orange"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* File Type Distribution */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">File Type Distribution</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, value }) => `${name} ${value.toFixed(1)}%`}
                >
                  {pieData.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number, _name: string, props) => {
                    const payload = props?.payload as { name: string; size: string } | undefined;
                    if (!payload) return [`${value.toFixed(1)}%`, ''];
                    return [`${value.toFixed(1)}% (${payload.size})`, payload.name];
                  }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              No file type data available
            </div>
          )}
        </div>

        {/* Top Folders by Size */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Top Folders by Size</h3>
          <div className="space-y-4">
            {topFolders.length > 0 ? (
              topFolders.map((folder, index) => (
                <div key={folder.name} className="flex items-center">
                  <span className="w-6 text-sm text-gray-500 font-medium">
                    {index + 1}
                  </span>
                  <div className="flex-1 mx-3">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium truncate max-w-[200px]">
                        {folder.name}
                      </span>
                      <span className="text-gray-500">{folder.size_formatted}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div
                        className="bg-primary-500 h-2.5 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(folder.percentage, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="h-48 flex items-center justify-center text-gray-400">
                No folder data available
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Storage Growth Trend */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Storage Growth Trend (30 days)</h3>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(value) => `${value} TB`} />
              <Tooltip formatter={(value: number) => [`${value} TB`, 'Storage']} />
              <Legend />
              <Line
                type="monotone"
                dataKey="size"
                stroke="#3B82F6"
                strokeWidth={2}
                dot={false}
                name="Total Storage"
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-64 flex items-center justify-center text-gray-400">
            No history data available
          </div>
        )}
      </div>

      {/* File Type Detail Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">File Types Detail</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Extension
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Files
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Size
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  %
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {fileTypes?.slice(0, FILE_TYPES_TABLE_LIMIT).map((type, index) => (
                <tr key={`type-${type.extension || 'unknown'}-${index}`} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {type.extension || 'unknown'}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                    {type.file_count.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-gray-600">
                    {type.total_size_formatted}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium text-gray-900">
                    {type.percentage.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
