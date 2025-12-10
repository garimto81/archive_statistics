/**
 * ExtensionFilter - 확장자 필터 컴포넌트
 *
 * 대시보드에서 파일 확장자를 선택하여 통계를 필터링할 수 있는 UI.
 * - 다중 선택 지원
 * - 선택/전체해제 토글
 * - 파일 수 기반 정렬
 *
 * Issue: #7
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Filter, X, Check } from 'lucide-react';
import clsx from 'clsx';
import { statsApi } from '../services/api';

interface ExtensionFilterProps {
  selectedExtensions: Set<string>;
  onChange: (selected: Set<string>) => void;
  className?: string;
}

// 주요 확장자 그룹 (빠른 선택용)
const EXTENSION_GROUPS = {
  video: ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v'],
  audio: ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a'],
  image: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'],
  document: ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'],
};

export default function ExtensionFilter({
  selectedExtensions,
  onChange,
  className,
}: ExtensionFilterProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Fetch available extensions from API
  const { data: availableExtensions = [] } = useQuery({
    queryKey: ['available-extensions'],
    queryFn: statsApi.getAvailableExtensions,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const isAllSelected = selectedExtensions.size === 0;

  const toggleExtension = (ext: string) => {
    const newSelected = new Set(selectedExtensions);
    if (newSelected.has(ext)) {
      newSelected.delete(ext);
    } else {
      newSelected.add(ext);
    }
    onChange(newSelected);
  };

  const selectAll = () => {
    onChange(new Set());
  };

  const selectGroup = (groupName: keyof typeof EXTENSION_GROUPS) => {
    const groupExts = EXTENSION_GROUPS[groupName];
    const availableInGroup = groupExts.filter((ext) =>
      availableExtensions.includes(ext)
    );
    onChange(new Set(availableInGroup));
  };

  const clearSelection = () => {
    onChange(new Set());
  };

  // Show only top extensions when collapsed
  const displayExtensions = isExpanded
    ? availableExtensions
    : availableExtensions.slice(0, 8);

  const hasMoreExtensions = availableExtensions.length > 8;

  return (
    <div className={clsx('bg-white rounded-lg border border-gray-200 p-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Extension Filter</span>
          {selectedExtensions.size > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium bg-primary-100 text-primary-700 rounded-full">
              {selectedExtensions.size} selected
            </span>
          )}
        </div>
        {selectedExtensions.size > 0 && (
          <button
            onClick={clearSelection}
            className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
          >
            <X className="w-3 h-3" />
            Clear
          </button>
        )}
      </div>

      {/* Quick Group Buttons */}
      <div className="flex flex-wrap gap-2 mb-3">
        <button
          onClick={selectAll}
          className={clsx(
            'px-3 py-1 text-xs rounded-full transition-colors',
            isAllSelected
              ? 'bg-primary-500 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          )}
        >
          All Files
        </button>
        {Object.keys(EXTENSION_GROUPS).map((group) => {
          const groupExts = EXTENSION_GROUPS[group as keyof typeof EXTENSION_GROUPS];
          const hasAvailable = groupExts.some((ext) => availableExtensions.includes(ext));
          if (!hasAvailable) return null;

          const isGroupSelected =
            selectedExtensions.size > 0 &&
            groupExts.every(
              (ext) => !availableExtensions.includes(ext) || selectedExtensions.has(ext)
            );

          return (
            <button
              key={group}
              onClick={() => selectGroup(group as keyof typeof EXTENSION_GROUPS)}
              className={clsx(
                'px-3 py-1 text-xs rounded-full capitalize transition-colors',
                isGroupSelected
                  ? 'bg-primary-500 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              {group}
            </button>
          );
        })}
      </div>

      {/* Extension Chips */}
      <div className="flex flex-wrap gap-2">
        {displayExtensions.map((ext) => {
          const isSelected = selectedExtensions.has(ext);
          return (
            <button
              key={ext}
              onClick={() => toggleExtension(ext)}
              className={clsx(
                'px-3 py-1.5 text-sm rounded-full transition-all flex items-center gap-1.5',
                isSelected
                  ? 'bg-primary-500 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              {isSelected && <Check className="w-3 h-3" />}
              <span className="font-mono">.{ext}</span>
            </button>
          );
        })}

        {/* Show more button */}
        {hasMoreExtensions && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-3 py-1.5 text-sm text-primary-600 hover:text-primary-800 font-medium"
          >
            {isExpanded
              ? 'Show less'
              : `+${availableExtensions.length - 8} more`}
          </button>
        )}
      </div>
    </div>
  );
}
