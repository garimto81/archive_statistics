import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, RefreshCw } from 'lucide-react';
import FolderTree from '../components/FolderTree';
import { foldersApi } from '../services/api';
import type { FolderTreeNode } from '../types';

export default function FoldersPage() {
  const [selectedFolder, setSelectedFolder] = useState<FolderTreeNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const { data: folderTree, isLoading, refetch } = useQuery({
    queryKey: ['folder-tree-full'],
    queryFn: () => foldersApi.getTree(undefined, 5),
  });

  const { data: folderDetails } = useQuery({
    queryKey: ['folder-details', selectedFolder?.path],
    queryFn: () => foldersApi.getDetails(selectedFolder!.path),
    enabled: !!selectedFolder?.path,
  });

  const handleSelectFolder = (node: FolderTreeNode) => {
    setSelectedFolder(node);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Folder Explorer</h1>
        <button
          onClick={() => refetch()}
          className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Folder Tree */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            {/* Search */}
            <div className="p-4 border-b border-gray-100">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search folders..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            {/* Tree */}
            <div className="max-h-[600px] overflow-y-auto">
              <FolderTree
                nodes={folderTree || []}
                onSelect={handleSelectFolder}
                selectedPath={selectedFolder?.path}
              />
            </div>
          </div>
        </div>

        {/* Folder Details */}
        <div className="lg:col-span-2">
          {selectedFolder ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                {selectedFolder.name}
              </h2>

              <div className="text-sm text-gray-500 mb-6 break-all">
                {selectedFolder.path}
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-500">Size</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {selectedFolder.size_formatted}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-500">Files</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {selectedFolder.file_count.toLocaleString()}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-500">Subfolders</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {selectedFolder.folder_count.toLocaleString()}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-500">Depth</div>
                  <div className="text-lg font-semibold text-gray-900">
                    Level {selectedFolder.depth}
                  </div>
                </div>
              </div>

              {/* File Types */}
              {folderDetails?.file_types && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">File Types</h3>
                  <div className="space-y-2">
                    {folderDetails.file_types.slice(0, 10).map((type: any) => (
                      <div key={type.extension} className="flex items-center">
                        <span className="w-20 text-sm font-medium text-gray-700">
                          {type.extension || 'unknown'}
                        </span>
                        <div className="flex-1 mx-4">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-primary-500 h-2 rounded-full"
                              style={{ width: `${type.percentage}%` }}
                            />
                          </div>
                        </div>
                        <span className="text-sm text-gray-500 w-24 text-right">
                          {type.total_size_formatted}
                        </span>
                        <span className="text-sm text-gray-400 w-16 text-right">
                          {type.percentage.toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Children Folders */}
              {selectedFolder.children && selectedFolder.children.length > 0 && (
                <div className="mt-6">
                  <h3 className="font-semibold text-gray-900 mb-3">Subfolders</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {selectedFolder.children.slice(0, 9).map((child) => (
                      <button
                        key={child.id}
                        onClick={() => setSelectedFolder(child)}
                        className="bg-gray-50 rounded-lg p-3 text-left hover:bg-gray-100 transition-colors"
                      >
                        <div className="font-medium text-gray-900 truncate">
                          {child.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {child.size_formatted}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center text-gray-500">
              Select a folder to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
