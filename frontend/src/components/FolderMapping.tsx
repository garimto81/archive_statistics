import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FolderOpen,
  Link2,
  Link2Off,
  Wand2,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Search,
  Filter,
} from 'lucide-react';
import clsx from 'clsx';
import { folderMappingApi } from '../services/api';
import type { UnmappedFolder, WorkStatusOption, AutoMatchResult } from '../types';

type TabType = 'unmapped' | 'mapped' | 'auto-match';

export default function FolderMapping() {
  const [activeTab, setActiveTab] = useState<TabType>('unmapped');
  const [selectedFolder, setSelectedFolder] = useState<UnmappedFolder | null>(null);
  const [selectedWorkStatus, setSelectedWorkStatus] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [depthFilter, setDepthFilter] = useState({ min: 1, max: 3 });
  const [autoMatchResult, setAutoMatchResult] = useState<AutoMatchResult | null>(null);

  const queryClient = useQueryClient();

  // Queries
  const { data: unmappedFolders, isLoading: loadingUnmapped } = useQuery({
    queryKey: ['folder-mapping', 'unmapped', depthFilter],
    queryFn: () => folderMappingApi.getUnmapped({
      min_depth: depthFilter.min,
      max_depth: depthFilter.max,
      limit: 200,
    }),
    enabled: activeTab === 'unmapped',
  });

  const { data: mappedFolders, isLoading: loadingMapped } = useQuery({
    queryKey: ['folder-mapping', 'mapped'],
    queryFn: () => folderMappingApi.getMapped(undefined, 200),
    enabled: activeTab === 'mapped',
  });

  const { data: workStatusOptions } = useQuery({
    queryKey: ['folder-mapping', 'work-status-options'],
    queryFn: folderMappingApi.getWorkStatusOptions,
  });

  // Mutations
  const connectMutation = useMutation({
    mutationFn: ({ folderPath, workStatusId }: { folderPath: string; workStatusId: number }) =>
      folderMappingApi.connect(folderPath, workStatusId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['folder-mapping'] });
      setSelectedFolder(null);
      setSelectedWorkStatus(null);
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: (folderId: number) => folderMappingApi.disconnect(folderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['folder-mapping'] });
    },
  });

  const autoMatchMutation = useMutation({
    mutationFn: (dryRun: boolean) => folderMappingApi.autoMatch(dryRun),
    onSuccess: (data) => {
      setAutoMatchResult(data);
      if (!data.dry_run) {
        queryClient.invalidateQueries({ queryKey: ['folder-mapping'] });
      }
    },
  });

  // Filter folders by search term
  const filteredUnmapped = unmappedFolders?.filter(f =>
    f.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    f.path.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredMapped = mappedFolders?.filter(f =>
    f.folder_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    f.folder_path.toLowerCase().includes(searchTerm.toLowerCase()) ||
    f.work_status_category?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Group work status options by archive
  const groupedOptions = workStatusOptions?.reduce((acc, ws) => {
    const key = ws.archive_name || 'Unknown';
    if (!acc[key]) acc[key] = [];
    acc[key].push(ws);
    return acc;
  }, {} as Record<string, WorkStatusOption[]>);

  const handleConnect = () => {
    if (selectedFolder && selectedWorkStatus) {
      connectMutation.mutate({
        folderPath: selectedFolder.path,
        workStatusId: selectedWorkStatus,
      });
    }
  };

  const renderTabs = () => (
    <div className="flex border-b border-gray-200 mb-4">
      {[
        { id: 'unmapped' as const, label: '미연결 폴더', icon: FolderOpen, count: unmappedFolders?.length },
        { id: 'mapped' as const, label: '연결된 폴더', icon: Link2, count: mappedFolders?.length },
        { id: 'auto-match' as const, label: '자동 매칭', icon: Wand2 },
      ].map(tab => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          className={clsx(
            'flex items-center gap-2 px-4 py-3 border-b-2 -mb-px transition-colors',
            activeTab === tab.id
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          )}
        >
          <tab.icon className="w-4 h-4" />
          {tab.label}
          {tab.count !== undefined && (
            <span className={clsx(
              'px-2 py-0.5 text-xs rounded-full',
              activeTab === tab.id ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-600'
            )}>
              {tab.count}
            </span>
          )}
        </button>
      ))}
    </div>
  );

  const renderSearchBar = () => (
    <div className="flex gap-3 mb-4">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="폴더명 또는 경로로 검색..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        />
      </div>
      {activeTab === 'unmapped' && (
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <select
            value={depthFilter.min}
            onChange={(e) => setDepthFilter(d => ({ ...d, min: Number(e.target.value) }))}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
          >
            {[0, 1, 2, 3, 4].map(d => (
              <option key={d} value={d}>Depth {d}+</option>
            ))}
          </select>
          <span className="text-gray-400">~</span>
          <select
            value={depthFilter.max}
            onChange={(e) => setDepthFilter(d => ({ ...d, max: Number(e.target.value) }))}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
          >
            {[1, 2, 3, 4, 5, 6].map(d => (
              <option key={d} value={d}>Depth {d}</option>
            ))}
          </select>
        </div>
      )}
    </div>
  );

  const renderUnmappedTab = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 폴더 목록 */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
          <h3 className="font-medium text-gray-900">미연결 폴더 선택</h3>
          <p className="text-sm text-gray-500 mt-1">WorkStatus에 연결되지 않은 폴더 목록</p>
        </div>
        <div className="max-h-96 overflow-y-auto">
          {loadingUnmapped ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : filteredUnmapped?.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              미연결 폴더가 없습니다
            </div>
          ) : (
            <ul className="divide-y divide-gray-100">
              {filteredUnmapped?.map(folder => (
                <li
                  key={folder.id}
                  onClick={() => setSelectedFolder(folder)}
                  className={clsx(
                    'px-4 py-3 cursor-pointer transition-colors',
                    selectedFolder?.id === folder.id
                      ? 'bg-primary-50 border-l-4 border-primary-500'
                      : 'hover:bg-gray-50'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FolderOpen className="w-4 h-4 text-yellow-500" />
                      <span className="font-medium text-gray-900">{folder.name}</span>
                    </div>
                    <span className="text-xs text-gray-400">depth: {folder.depth}</span>
                  </div>
                  <div className="mt-1 text-sm text-gray-500 truncate">{folder.path}</div>
                  <div className="mt-1 text-xs text-gray-400">{folder.file_count} files</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* WorkStatus 선택 */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
          <h3 className="font-medium text-gray-900">WorkStatus 선택</h3>
          <p className="text-sm text-gray-500 mt-1">연결할 작업을 선택하세요</p>
        </div>
        <div className="max-h-96 overflow-y-auto">
          {groupedOptions && Object.entries(groupedOptions).map(([archive, options]) => (
            <div key={archive}>
              <div className="px-4 py-2 bg-gray-100 text-sm font-medium text-gray-700 sticky top-0">
                {archive}
              </div>
              <ul className="divide-y divide-gray-100">
                {options.map(ws => (
                  <li
                    key={ws.id}
                    onClick={() => setSelectedWorkStatus(ws.id)}
                    className={clsx(
                      'px-4 py-3 cursor-pointer transition-colors',
                      selectedWorkStatus === ws.id
                        ? 'bg-primary-50 border-l-4 border-primary-500'
                        : 'hover:bg-gray-50'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900">{ws.category}</span>
                      <span className="text-sm text-gray-500">
                        {ws.excel_done}/{ws.total_videos}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* 연결 버튼 */}
        {selectedFolder && selectedWorkStatus && (
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
            <button
              onClick={handleConnect}
              disabled={connectMutation.isPending}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {connectMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Link2 className="w-4 h-4" />
              )}
              연결하기
            </button>
            <div className="mt-2 text-sm text-gray-600 text-center">
              <span className="font-medium">{selectedFolder.name}</span>
              {' → '}
              <span className="font-medium">
                {workStatusOptions?.find(w => w.id === selectedWorkStatus)?.category}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderMappedTab = () => (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
        <h3 className="font-medium text-gray-900">연결된 폴더 목록</h3>
        <p className="text-sm text-gray-500 mt-1">폴더-WorkStatus 연결 관리</p>
      </div>
      <div className="max-h-[600px] overflow-y-auto">
        {loadingMapped ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        ) : filteredMapped?.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            연결된 폴더가 없습니다
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">폴더</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">WorkStatus</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">작업</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredMapped?.map(mapping => (
                <tr key={mapping.folder_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <FolderOpen className="w-4 h-4 text-yellow-500" />
                      <div>
                        <div className="font-medium text-gray-900">{mapping.folder_name}</div>
                        <div className="text-sm text-gray-500 truncate max-w-xs">{mapping.folder_path}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
                      <CheckCircle2 className="w-3 h-3" />
                      {mapping.work_status_category}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => disconnectMutation.mutate(mapping.folder_id)}
                      disabled={disconnectMutation.isPending}
                      className="inline-flex items-center gap-1 px-3 py-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                    >
                      <Link2Off className="w-4 h-4" />
                      연결 해제
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );

  const renderAutoMatchTab = () => (
    <div className="space-y-6">
      {/* 설명 & 버튼 */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-purple-100 rounded-lg">
            <Wand2 className="w-6 h-6 text-purple-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-medium text-gray-900">자동 매칭</h3>
            <p className="mt-1 text-gray-600">
              폴더명과 WorkStatus 카테고리를 fuzzy matching하여 자동으로 연결합니다.
              먼저 미리보기(Dry Run)로 결과를 확인한 후 적용하세요.
            </p>
            <div className="mt-4 flex gap-3">
              <button
                onClick={() => autoMatchMutation.mutate(true)}
                disabled={autoMatchMutation.isPending}
                className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
              >
                {autoMatchMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
                미리보기 (Dry Run)
              </button>
              <button
                onClick={() => {
                  if (window.confirm('자동 매칭을 실행하시겠습니까? 모든 매칭이 DB에 저장됩니다.')) {
                    autoMatchMutation.mutate(false);
                  }
                }}
                disabled={autoMatchMutation.isPending}
                className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                {autoMatchMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Wand2 className="w-4 h-4" />
                )}
                자동 매칭 실행
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 결과 */}
      {autoMatchResult && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className={clsx(
            'px-4 py-3 border-b border-gray-200',
            autoMatchResult.dry_run ? 'bg-yellow-50' : 'bg-green-50'
          )}>
            <div className="flex items-center gap-2">
              {autoMatchResult.dry_run ? (
                <AlertCircle className="w-5 h-5 text-yellow-600" />
              ) : (
                <CheckCircle2 className="w-5 h-5 text-green-600" />
              )}
              <h3 className="font-medium text-gray-900">
                {autoMatchResult.dry_run ? '미리보기 결과' : '매칭 완료'}
              </h3>
            </div>
            <p className="mt-1 text-sm text-gray-600">
              전체 미연결: {autoMatchResult.total_unmatched}개 /
              매칭됨: {autoMatchResult.matched_count}개
            </p>
          </div>
          <div className="max-h-96 overflow-y-auto">
            <table className="w-full">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">폴더</th>
                  <th className="px-4 py-2 text-center text-xs font-medium text-gray-500">→</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">WorkStatus</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {autoMatchResult.matches.map((match, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-2">
                      <div className="font-medium text-gray-900">{match.folder_name}</div>
                      <div className="text-xs text-gray-500 truncate max-w-xs">{match.folder_path}</div>
                    </td>
                    <td className="px-4 py-2 text-center">
                      <Link2 className="w-4 h-4 text-gray-400 inline" />
                    </td>
                    <td className="px-4 py-2">
                      <span className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                        {match.work_status_category}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-4">
      {renderTabs()}
      {activeTab !== 'auto-match' && renderSearchBar()}
      {activeTab === 'unmapped' && renderUnmappedTab()}
      {activeTab === 'mapped' && renderMappedTab()}
      {activeTab === 'auto-match' && renderAutoMatchTab()}
    </div>
  );
}
