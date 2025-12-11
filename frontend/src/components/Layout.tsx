import { ReactNode, useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  LayoutDashboard,
  FolderTree,
  BarChart3,
  History,
  Bell,
  Settings,
  ClipboardList,
  RefreshCw,
  Loader2,
  X,
  Clock,
  Film,
  Users,
  ChevronDown,
  Zap,
  Database,
} from 'lucide-react';
import clsx from 'clsx';
import { scanApi } from '../services/api';

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

interface LayoutProps {
  children: ReactNode;
}

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/folders', icon: FolderTree, label: 'Folders' },
  { path: '/work-status', icon: ClipboardList, label: 'Work Status' },
  { path: '/statistics', icon: BarChart3, label: 'Statistics' },
  { path: '/history', icon: History, label: 'History' },
  { path: '/alerts', icon: Bell, label: 'Alerts' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

type ScanType = 'incremental' | 'full';

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const queryClient = useQueryClient();
  const [scanMessage, setScanMessage] = useState<string | null>(null);
  const [showLogs, setShowLogs] = useState(false);
  const [showScanMenu, setShowScanMenu] = useState(false);
  const scanMenuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (scanMenuRef.current && !scanMenuRef.current.contains(event.target as Node)) {
        setShowScanMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Poll scan status - always poll to show status from other clients
  const { data: scanStatus } = useQuery({
    queryKey: ['scan-status'],
    queryFn: scanApi.getStatus,
    refetchInterval: (query) => query.state.data?.is_scanning ? 1000 : 5000,
  });

  // Start scan mutation
  const startScanMutation = useMutation({
    mutationFn: (scanType: ScanType) => scanApi.start(scanType),
    onSuccess: (data) => {
      setScanMessage(data.message);
      queryClient.invalidateQueries({ queryKey: ['scan-status'] });
      setTimeout(() => setScanMessage(null), 3000);
      setShowScanMenu(false);
    },
    onError: () => {
      setScanMessage('Scan failed to start');
      setTimeout(() => setScanMessage(null), 3000);
      setShowScanMenu(false);
    },
  });

  const handleScanClick = (scanType: ScanType) => {
    if (!scanStatus?.is_scanning) {
      startScanMutation.mutate(scanType);
    }
  };

  const isScanning = scanStatus?.is_scanning || startScanMutation.isPending;

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-primary-700">
                Archive Statistics
              </h1>
              <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded">
                v1.26.0 | Lazy Load Cascading Fix
              </span>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={clsx(
                      'flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary-100 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    )}
                  >
                    <Icon className="w-4 h-4 mr-1.5" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            {/* Scan Button & Status */}
            <div className="flex items-center gap-3">
              {scanMessage && (
                <span className="text-sm text-green-600">{scanMessage}</span>
              )}
              {isScanning && scanStatus && (
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-gray-600">
                    {scanStatus.progress.toFixed(0)}% - {scanStatus.files_scanned} files
                  </span>
                  {scanStatus.media_files_processed > 0 && (
                    <span className="flex items-center text-purple-600">
                      <Film className="w-3 h-3 mr-1" />
                      {scanStatus.media_files_processed} media
                    </span>
                  )}
                  {scanStatus.elapsed_seconds && (
                    <span className="flex items-center text-gray-500">
                      <Clock className="w-3 h-3 mr-1" />
                      {formatDuration(scanStatus.elapsed_seconds)}
                      {scanStatus.estimated_remaining_seconds && (
                        <span className="text-xs ml-1">
                          (~{formatDuration(scanStatus.estimated_remaining_seconds)} left)
                        </span>
                      )}
                    </span>
                  )}
                  <button
                    onClick={() => setShowLogs(!showLogs)}
                    className="text-xs text-primary-600 hover:underline"
                  >
                    {showLogs ? 'Hide Logs' : 'Show Logs'}
                  </button>
                </div>
              )}
              {/* Scan Button with Dropdown */}
              <div className="relative" ref={scanMenuRef}>
                {isScanning ? (
                  <button
                    disabled
                    className="flex items-center px-4 py-2 rounded-lg bg-gray-400 cursor-not-allowed text-white"
                  >
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Scanning...
                  </button>
                ) : (
                  <>
                    <button
                      onClick={() => setShowScanMenu(!showScanMenu)}
                      className="flex items-center px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-700 text-white transition-colors"
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Scan
                      <ChevronDown className="w-4 h-4 ml-1" />
                    </button>

                    {/* Dropdown Menu */}
                    {showScanMenu && (
                      <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                        <button
                          onClick={() => handleScanClick('incremental')}
                          className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-start gap-3"
                        >
                          <Zap className="w-5 h-5 text-yellow-500 mt-0.5 flex-shrink-0" />
                          <div>
                            <div className="font-medium text-gray-900">Quick Scan</div>
                            <div className="text-xs text-gray-500">신규/변경 파일만 스캔 (권장)</div>
                          </div>
                        </button>
                        <button
                          onClick={() => handleScanClick('full')}
                          className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-start gap-3"
                        >
                          <Database className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                          <div>
                            <div className="font-medium text-gray-900">Full Scan</div>
                            <div className="text-xs text-gray-500">전체 NAS 폴더 스캔</div>
                          </div>
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Scan Logs Panel */}
      {showLogs && isScanning && scanStatus?.logs && (
        <div className="bg-gray-900 text-green-400 border-b border-gray-700">
          <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs text-gray-400 font-mono">
                📡 Scan Logs (shared across all clients)
              </span>
              <button onClick={() => setShowLogs(false)} className="text-gray-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="font-mono text-xs space-y-0.5 max-h-32 overflow-y-auto">
              {scanStatus.logs.map((log, i) => (
                <div key={i} className="text-green-300">{log}</div>
              ))}
              {scanStatus.current_folder && (
                <div className="text-yellow-400 animate-pulse">
                  📂 Scanning: {scanStatus.current_folder.split('/').slice(-2).join('/')}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4">
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center text-sm text-gray-500">
            <div className="flex items-center gap-4">
              <span className="flex items-center">
                <Users className="w-4 h-4 mr-1.5 text-primary-600" />
                <span className="font-medium text-primary-700">{scanStatus?.active_viewers || 1}</span>
                <span className="ml-1">viewers online</span>
              </span>
            </div>
            <span className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
              NAS Connected
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
