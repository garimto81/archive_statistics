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
import FolderTree from '../components/FolderTree';
import { statsApi, foldersApi } from '../services/api';

const COLORS = ['#E91E63', '#9C27B0', '#00BCD4', '#795548', '#607D8B'];

export default function Dashboard() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['stats-summary'],
    queryFn: statsApi.getSummary,
  });

  const { data: fileTypes } = useQuery({
    queryKey: ['file-types'],
    queryFn: () => statsApi.getFileTypes(10),
  });

  const { data: history } = useQuery({
    queryKey: ['history'],
    queryFn: () => statsApi.getHistory('daily', 30),
  });

  const { data: folderTree } = useQuery({
    queryKey: ['folder-tree'],
    queryFn: () => foldersApi.getTree(undefined, 3),
  });

  // Transform history data for chart
  const chartData = history?.data?.map((item) => ({
    date: new Date(item.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
    size: Math.round(item.total_size / (1024 * 1024 * 1024 * 1024)), // Convert to TB
    files: item.total_files,
  })) || [];

  // Pie chart data
  const pieData = fileTypes?.slice(0, 5).map((type) => ({
    name: type.extension || 'unknown',
    value: type.percentage,
    count: type.file_count,
    size: type.total_size_formatted,
  })) || [];

  if (summaryLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Files"
          value={summary?.total_files.toLocaleString() || '0'}
          subtitle="+2,340 today"
          icon={<Files className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Total Size"
          value={summary?.total_size_formatted || '0 B'}
          subtitle="+1.2 TB today"
          icon={<HardDrive className="w-6 h-6" />}
          color="green"
        />
        <StatCard
          title="Media Duration"
          value={summary?.total_duration_formatted || '0h'}
          subtitle="+120 hrs today"
          icon={<Clock className="w-6 h-6" />}
          color="purple"
        />
        <StatCard
          title="File Types"
          value={summary?.file_type_count || 0}
          subtitle="MP4 is largest"
          icon={<FileType className="w-6 h-6" />}
          color="orange"
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6" style={{ minHeight: 'calc(100vh - 280px)' }}>
        {/* Folder Tree */}
        <div className="lg:col-span-1 flex flex-col">
          <FolderTree nodes={folderTree || []} />
        </div>

        {/* Charts */}
        <div className="lg:col-span-2 space-y-6">
          {/* Top Row: Pie Chart + Bar Chart */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* File Type Distribution */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">File Type Distribution</h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, value }) => `${name} ${value.toFixed(1)}%`}
                  >
                    {pieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number, _name: string, props: any) => [
                      `${value.toFixed(1)}% (${props.payload.size})`,
                      props.payload.name,
                    ]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Top Folders */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Top Folders by Size</h3>
              <div className="space-y-3">
                {folderTree?.slice(0, 5).map((folder, index) => (
                  <div key={folder.id} className="flex items-center">
                    <span className="w-6 text-sm text-gray-500">{index + 1}</span>
                    <div className="flex-1 mx-3">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium truncate">{folder.name}</span>
                        <span className="text-gray-500">{folder.size_formatted}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-primary-500 h-2 rounded-full"
                          style={{
                            width: `${Math.min((folder.size / (folderTree?.[0]?.size || 1)) * 100, 100)}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Storage Growth Trend */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Storage Growth Trend</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `${value} TB`}
                />
                <Tooltip
                  formatter={(value: number) => [`${value} TB`, 'Storage']}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="size"
                  stroke="#1976D2"
                  strokeWidth={2}
                  dot={false}
                  name="Total Storage"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
